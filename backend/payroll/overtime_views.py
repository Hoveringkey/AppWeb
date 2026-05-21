from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import (
    DailyOvertimeAssignment,
    OvertimePenalty,
    OvertimeProfile,
    PayrollClosure,
    WeeklyOvertimeSchedule,
)
from .overtime_serializers import (
    DailyOvertimeAssignmentSerializer,
    GenerateScheduleSerializer,
    OvertimePenaltySerializer,
    OvertimeProfileSerializer,
    WeeklyOvertimeScheduleSerializer,
)
from .overtime_services import (
    OvertimeScheduleLockedError,
    OvertimeWeekClosedError,
    apply_overtime_schedule_to_incidences,
    generate_overtime_schedule,
)
from .permissions import IsPayrollOperator
from .views import WeekClosedConflict


class ScheduleLockedConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'La planilla ya está bloqueada o publicada.'
    default_code = 'schedule_locked'


def _ensure_week_open(iso_year, iso_week):
    if PayrollClosure.objects.filter(iso_year=iso_year, semana_num=iso_week).exists():
        raise WeekClosedConflict()


class OvertimeProfileViewSet(viewsets.ModelViewSet):
    queryset = OvertimeProfile.objects.select_related('empleado').all()
    serializer_class = OvertimeProfileSerializer
    permission_classes = [IsAuthenticated, IsPayrollOperator]

    def get_queryset(self):
        qs = super().get_queryset()
        empleado = self.request.query_params.get('empleado')
        if empleado:
            qs = qs.filter(empleado_id=empleado)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('1', 'true', 'yes'))
        return qs


class WeeklyOvertimeScheduleViewSet(viewsets.ModelViewSet):
    queryset = WeeklyOvertimeSchedule.objects.all().prefetch_related(
        'assignments__empleado', 'penalties__empleado'
    )
    serializer_class = WeeklyOvertimeScheduleSerializer
    permission_classes = [IsAuthenticated, IsPayrollOperator]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        iso_year = self.request.query_params.get('iso_year')
        iso_week = self.request.query_params.get('iso_week')
        if iso_year:
            try:
                qs = qs.filter(iso_year=int(iso_year))
            except (TypeError, ValueError):
                return qs.none()
        if iso_week:
            try:
                qs = qs.filter(iso_week=int(iso_week))
            except (TypeError, ValueError):
                return qs.none()
        return qs

    def _ensure_mutable(self, schedule):
        _ensure_week_open(schedule.iso_year, schedule.iso_week)
        if schedule.status != WeeklyOvertimeSchedule.DRAFT:
            raise ScheduleLockedConflict()

    def update(self, request, *args, **kwargs):
        self._ensure_mutable(self.get_object())
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_mutable(self.get_object())
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._ensure_mutable(self.get_object())
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        payload = GenerateScheduleSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        iso_year = payload.validated_data['iso_year']
        iso_week = payload.validated_data['iso_week']

        try:
            schedule = generate_overtime_schedule(iso_year, iso_week, user=request.user)
        except OvertimeWeekClosedError:
            raise WeekClosedConflict()
        except OvertimeScheduleLockedError:
            raise ScheduleLockedConflict()

        # Recargar con relaciones para serializar todo.
        schedule = (
            WeeklyOvertimeSchedule.objects
            .prefetch_related('assignments__empleado', 'penalties__empleado')
            .get(pk=schedule.pk)
        )
        return Response(
            WeeklyOvertimeScheduleSerializer(schedule).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        schedule = self.get_object()
        _ensure_week_open(schedule.iso_year, schedule.iso_week)
        if schedule.status != WeeklyOvertimeSchedule.DRAFT:
            raise ScheduleLockedConflict()
        schedule.status = WeeklyOvertimeSchedule.PUBLISHED
        schedule.published_at = timezone.now()
        schedule.save(update_fields=['status', 'published_at', 'updated_at'])
        return Response(WeeklyOvertimeScheduleSerializer(schedule).data)

    @action(detail=True, methods=['post'], url_path='apply-to-incidences')
    def apply_to_incidences(self, request, pk=None):
        schedule = self.get_object()
        _ensure_week_open(schedule.iso_year, schedule.iso_week)
        try:
            result = apply_overtime_schedule_to_incidences(schedule, user=request.user)
        except OvertimeWeekClosedError:
            raise WeekClosedConflict()
        except OvertimeScheduleLockedError:
            raise ScheduleLockedConflict()

        schedule.refresh_from_db()
        data = WeeklyOvertimeScheduleSerializer(schedule).data
        data['apply_result'] = result
        return Response(data, status=status.HTTP_200_OK)


class DailyOvertimeAssignmentViewSet(viewsets.ModelViewSet):
    queryset = DailyOvertimeAssignment.objects.select_related('empleado', 'schedule').all()
    serializer_class = DailyOvertimeAssignmentSerializer
    permission_classes = [IsAuthenticated, IsPayrollOperator]

    def get_queryset(self):
        qs = super().get_queryset()
        schedule = self.request.query_params.get('schedule')
        if schedule:
            try:
                qs = qs.filter(schedule_id=int(schedule))
            except (TypeError, ValueError):
                return qs.none()
        return qs

    def _ensure_mutable(self, instance):
        schedule = instance.schedule
        _ensure_week_open(schedule.iso_year, schedule.iso_week)
        if schedule.status != WeeklyOvertimeSchedule.DRAFT:
            raise ScheduleLockedConflict()

    def update(self, request, *args, **kwargs):
        self._ensure_mutable(self.get_object())
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_mutable(self.get_object())
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._ensure_mutable(self.get_object())
        return super().destroy(request, *args, **kwargs)


class OvertimePenaltyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OvertimePenalty.objects.select_related('empleado', 'schedule').all()
    serializer_class = OvertimePenaltySerializer
    permission_classes = [IsAuthenticated, IsPayrollOperator]

    def get_queryset(self):
        qs = super().get_queryset()
        schedule = self.request.query_params.get('schedule')
        if schedule:
            try:
                qs = qs.filter(schedule_id=int(schedule))
            except (TypeError, ValueError):
                return qs.none()
        return qs
