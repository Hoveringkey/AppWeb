from decimal import Decimal

from rest_framework import serializers

from .models import (
    DailyOvertimeAssignment,
    OvertimePenalty,
    OvertimeProfile,
    WeeklyOvertimeSchedule,
)
from .overtime_services import (
    HOURS_TIPO_1,
    HOURS_TIPO_2,
    get_overtime_week_dates,
)


class OvertimeProfileSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)

    class Meta:
        model = OvertimeProfile
        fields = [
            'id', 'empleado', 'empleado_nombre', 'profile_type',
            'custom_weekdays', 'custom_daily_hours', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'empleado_nombre']

    def validate(self, attrs):
        profile_type = attrs.get(
            'profile_type', getattr(self.instance, 'profile_type', None)
        )
        custom_weekdays = attrs.get(
            'custom_weekdays', getattr(self.instance, 'custom_weekdays', None)
        )
        custom_daily_hours = attrs.get(
            'custom_daily_hours', getattr(self.instance, 'custom_daily_hours', None)
        )

        if profile_type == OvertimeProfile.FIXED_CUSTOM:
            if not custom_weekdays:
                raise serializers.ValidationError({
                    'custom_weekdays': 'Requerido y no vacío para FIXED_CUSTOM.'
                })
            if not isinstance(custom_weekdays, list):
                raise serializers.ValidationError({
                    'custom_weekdays': 'Debe ser una lista.'
                })
            normalized = []
            for d in custom_weekdays:
                if isinstance(d, bool) or not isinstance(d, int):
                    raise serializers.ValidationError({
                        'custom_weekdays': 'Cada día debe ser entero entre 0 y 5.'
                    })
                if d < 0 or d > 5:
                    raise serializers.ValidationError({
                        'custom_weekdays': 'Días válidos: 0=Lun .. 5=Sáb.'
                    })
                normalized.append(d)
            attrs['custom_weekdays'] = normalized
            if custom_daily_hours is None or Decimal(custom_daily_hours) <= 0:
                raise serializers.ValidationError({
                    'custom_daily_hours': 'Debe ser mayor a 0.'
                })

        return attrs


class OvertimePenaltySerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)

    class Meta:
        model = OvertimePenalty
        fields = [
            'id', 'schedule', 'empleado', 'empleado_nombre',
            'reason', 'source_incidence_date', 'created_at',
        ]
        read_only_fields = fields


class DailyOvertimeAssignmentSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)

    class Meta:
        model = DailyOvertimeAssignment
        fields = [
            'id', 'schedule', 'empleado', 'empleado_nombre', 'fecha',
            'assignment_type', 'hours', 'compensation_type',
            'source', 'is_forced', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'empleado_nombre']

    def validate(self, attrs):
        schedule = attrs.get('schedule', getattr(self.instance, 'schedule', None))
        if schedule is None:
            raise serializers.ValidationError({'schedule': 'Requerido.'})

        if schedule.status != WeeklyOvertimeSchedule.DRAFT:
            raise serializers.ValidationError({
                'schedule': 'Solo se pueden editar asignaciones de una planilla en DRAFT.'
            })

        fecha = attrs.get('fecha', getattr(self.instance, 'fecha', None))
        if fecha is None:
            raise serializers.ValidationError({'fecha': 'Requerida.'})

        week_dates = get_overtime_week_dates(schedule.iso_year, schedule.iso_week)
        if fecha not in week_dates:
            raise serializers.ValidationError({
                'fecha': 'La fecha debe ser lunes-sábado dentro de la semana ISO de la planilla.'
            })

        assignment_type = attrs.get(
            'assignment_type', getattr(self.instance, 'assignment_type', None)
        )
        hours = attrs.get('hours', getattr(self.instance, 'hours', None))
        if hours is None:
            raise serializers.ValidationError({'hours': 'Requeridas.'})
        hours = Decimal(hours)

        if assignment_type == DailyOvertimeAssignment.TIPO_1:
            if hours != HOURS_TIPO_1:
                raise serializers.ValidationError({
                    'hours': f'TIPO_1 debe tener exactamente {HOURS_TIPO_1} horas.'
                })
        elif assignment_type == DailyOvertimeAssignment.TIPO_2:
            if hours != HOURS_TIPO_2:
                raise serializers.ValidationError({
                    'hours': f'TIPO_2 debe tener exactamente {HOURS_TIPO_2} horas.'
                })
        elif assignment_type == DailyOvertimeAssignment.CUSTOM:
            if hours <= 0:
                raise serializers.ValidationError({
                    'hours': 'CUSTOM requiere horas > 0.'
                })
        else:
            raise serializers.ValidationError({
                'assignment_type': 'Tipo de asignación inválido.'
            })

        attrs['hours'] = hours
        return attrs

    def create(self, validated_data):
        validated_data.setdefault('source', DailyOvertimeAssignment.MANUAL)
        return super().create(validated_data)


class WeeklyOvertimeScheduleSerializer(serializers.ModelSerializer):
    assignments = DailyOvertimeAssignmentSerializer(many=True, read_only=True)
    penalties = OvertimePenaltySerializer(many=True, read_only=True)
    week_dates = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyOvertimeSchedule
        fields = [
            'id', 'iso_year', 'iso_week', 'status',
            'created_by', 'created_at', 'updated_at',
            'published_at', 'locked_at', 'notes',
            'assignments', 'penalties', 'week_dates',
        ]
        read_only_fields = [
            'id', 'status', 'created_by', 'created_at', 'updated_at',
            'published_at', 'locked_at', 'assignments', 'penalties', 'week_dates',
        ]

    def get_week_dates(self, obj):
        return [d.isoformat() for d in get_overtime_week_dates(obj.iso_year, obj.iso_week)]


class GenerateScheduleSerializer(serializers.Serializer):
    iso_year = serializers.IntegerField(min_value=1, max_value=9999)
    iso_week = serializers.IntegerField(min_value=1, max_value=53)
