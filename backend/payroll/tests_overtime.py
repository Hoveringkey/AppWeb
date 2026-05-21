"""Tests para el módulo de Programación Semanal de Tiempo Extra."""
import datetime
from decimal import Decimal

from django.contrib.auth.models import Group, User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    DailyOvertimeAssignment,
    Employee,
    IncidenceCatalog,
    IncidenceRecord,
    OVERTIME_ROTATION_ANCHOR_ISO_WEEK,
    OVERTIME_ROTATION_ANCHOR_ISO_YEAR,
    OvertimePenalty,
    OvertimeProfile,
    PayrollClosure,
    Schedule,
    WeeklyOvertimeSchedule,
)
from .overtime_services import (
    apply_overtime_schedule_to_incidences,
    generate_overtime_schedule,
    get_overtime_rotation_parity,
    get_overtime_week_dates,
)
from .permissions import HR_CAPTURE


ANCHOR_YEAR = OVERTIME_ROTATION_ANCHOR_ISO_YEAR  # 2026
ANCHOR_WEEK = OVERTIME_ROTATION_ANCHOR_ISO_WEEK  # 21


def _make_user():
    group, _ = Group.objects.get_or_create(name=HR_CAPTURE)
    user = User.objects.create_user(username='ot_hr', password='pw')
    user.groups.add(group)
    return user


def _make_schedule_obj():
    return Schedule.objects.get_or_create(time_range='08:00-18:00')[0]


def _mk_emp(no, name='Emp'):
    return Employee.objects.create(
        no_nomina=no,
        nombre=name,
        puesto='Operador',
        fecha_ingreso=datetime.date(2024, 1, 1),
        horario_lv=_make_schedule_obj(),
    )


def _mk_catalogs():
    hx = IncidenceCatalog.objects.create(tipo='Horas Extra', abreviatura='HX')
    f = IncidenceCatalog.objects.create(tipo='Falta', abreviatura='F')
    psg = IncidenceCatalog.objects.create(tipo='Permiso Sin Goce', abreviatura='PSG')
    return hx, f, psg


class OvertimeRotationParityTests(APITestCase):
    def test_anchor_week_is_parity_A(self):
        self.assertEqual(get_overtime_rotation_parity(ANCHOR_YEAR, ANCHOR_WEEK), 'A')

    def test_anchor_plus_one_is_B(self):
        self.assertEqual(get_overtime_rotation_parity(ANCHOR_YEAR, ANCHOR_WEEK + 1), 'B')

    def test_anchor_plus_two_is_A(self):
        self.assertEqual(get_overtime_rotation_parity(ANCHOR_YEAR, ANCHOR_WEEK + 2), 'A')

    def test_anchor_minus_one_is_B(self):
        self.assertEqual(get_overtime_rotation_parity(ANCHOR_YEAR, ANCHOR_WEEK - 1), 'B')


class OvertimeScheduleGenerateTests(APITestCase):
    """Generación de planilla, perfiles y penalizaciones."""

    iso_year = ANCHOR_YEAR  # paridad A
    iso_week = ANCHOR_WEEK

    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        self.hx, self.f, self.psg = _mk_catalogs()
        # Empleados con todos los perfiles
        self.e_a = _mk_emp('RA-1', 'Rotación A')
        self.e_b = _mk_emp('RB-1', 'Rotación B')
        self.e_sm = _mk_emp('SM-1', 'Sábado-Lunes')
        self.e_4d = _mk_emp('4D-1', '4 días')
        self.e_cx = _mk_emp('CX-1', 'Custom')
        self.e_inactive = _mk_emp('INACT-1', 'Sin perfil activo')

        OvertimeProfile.objects.create(empleado=self.e_a, profile_type=OvertimeProfile.ROTATION_A)
        OvertimeProfile.objects.create(empleado=self.e_b, profile_type=OvertimeProfile.ROTATION_B)
        OvertimeProfile.objects.create(
            empleado=self.e_sm,
            profile_type=OvertimeProfile.SATURDAY_OR_MONDAY_8H,
            custom_weekdays=[0],
        )
        OvertimeProfile.objects.create(empleado=self.e_4d, profile_type=OvertimeProfile.FIXED_4DAY)
        OvertimeProfile.objects.create(
            empleado=self.e_cx,
            profile_type=OvertimeProfile.FIXED_CUSTOM,
            custom_weekdays=[0, 4],
            custom_daily_hours=Decimal('6.00'),
        )
        OvertimeProfile.objects.create(
            empleado=self.e_inactive,
            profile_type=OvertimeProfile.ROTATION_A,
            is_active=False,
        )

    def _generate(self):
        return generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)

    def test_rotation_a_pattern_a(self):
        sched = self._generate()
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.e_a)
            .order_by('fecha')
            .values_list('fecha', 'assignment_type', 'hours')
        )
        # Paridad A → lun (0) y mié (2), TIPO_2 a 4h cada uno (8h totales semanales)
        self.assertEqual([d[0] for d in days], [week_dates[0], week_dates[2]])
        for _, t, h in days:
            self.assertEqual(t, DailyOvertimeAssignment.TIPO_2)
            self.assertEqual(h, Decimal('4.00'))
        self.assertEqual(sum((h for _, _, h in days), Decimal('0.00')), Decimal('8.00'))

    def test_rotation_b_pattern_a(self):
        sched = self._generate()
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.e_b)
            .order_by('fecha')
            .values_list('fecha', 'assignment_type', 'hours')
        )
        # Paridad A pero ROTATION_B → mar (1) y jue (3), TIPO_2 4h cada uno
        self.assertEqual([d[0] for d in days], [week_dates[1], week_dates[3]])
        for _, t, h in days:
            self.assertEqual(t, DailyOvertimeAssignment.TIPO_2)
            self.assertEqual(h, Decimal('4.00'))
        self.assertEqual(sum((h for _, _, h in days), Decimal('0.00')), Decimal('8.00'))

    def test_saturday_or_monday_profile_lunes(self):
        sched = self._generate()
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.e_sm)
            .order_by('fecha')
            .values_list('fecha', 'assignment_type', 'hours')
        )
        # custom_weekdays=[0] → solo lunes, TIPO_1, 8h
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0][0], week_dates[0])
        self.assertEqual(days[0][1], DailyOvertimeAssignment.TIPO_1)
        self.assertEqual(days[0][2], Decimal('8.00'))

    def test_fixed_4day(self):
        sched = self._generate()
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.e_4d)
            .order_by('fecha')
            .values_list('fecha', 'assignment_type', 'hours')
        )
        self.assertEqual([d[0] for d in days], week_dates[:4])
        for _, t, h in days:
            self.assertEqual(t, DailyOvertimeAssignment.TIPO_2)
            self.assertEqual(h, Decimal('4.00'))
        # 4 días × 4h = 16h
        self.assertEqual(sum((h for _, _, h in days), Decimal('0.00')), Decimal('16.00'))

    def test_fixed_custom(self):
        sched = self._generate()
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.e_cx)
            .order_by('fecha')
            .values_list('fecha', 'assignment_type', 'hours')
        )
        self.assertEqual([d[0] for d in days], [week_dates[0], week_dates[4]])
        for _, t, h in days:
            self.assertEqual(t, DailyOvertimeAssignment.CUSTOM)
            self.assertEqual(h, Decimal('6.00'))

    def test_inactive_profile_not_assigned(self):
        sched = self._generate()
        self.assertFalse(
            DailyOvertimeAssignment.objects.filter(schedule=sched, empleado=self.e_inactive).exists()
        )


class OvertimePenaltyTests(APITestCase):
    """F/PSG en la semana ISO anterior generan OvertimePenalty y bloquean el AUTO."""

    iso_year = ANCHOR_YEAR
    iso_week = ANCHOR_WEEK

    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        self.hx, self.f, self.psg = _mk_catalogs()
        self.emp_falta = _mk_emp('PEN-F-1', 'Tiene Falta')
        self.emp_psg = _mk_emp('PEN-PSG-1', 'Tiene PSG')
        self.emp_ok = _mk_emp('PEN-OK-1', 'Sin penalty')
        for emp in (self.emp_falta, self.emp_psg, self.emp_ok):
            OvertimeProfile.objects.create(empleado=emp, profile_type=OvertimeProfile.ROTATION_A)

    def _add_prev_week_incidence(self, emp, catalog, day_idx=2):
        prev_year, prev_week = (
            (self.iso_year, self.iso_week - 1) if self.iso_week > 1 else (self.iso_year - 1, 52)
        )
        date = datetime.date.fromisocalendar(prev_year, prev_week, day_idx + 1)
        IncidenceRecord.objects.create(
            empleado=emp,
            fecha=date,
            semana_num=prev_week,
            tipo_incidencia=catalog,
            cantidad=Decimal('1.00'),
        )
        return date

    def test_penalty_from_F_previous_week(self):
        d = self._add_prev_week_incidence(self.emp_falta, self.f)
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        self.assertTrue(
            OvertimePenalty.objects.filter(schedule=sched, empleado=self.emp_falta, reason='F').exists()
        )
        # Y no recibió asignación AUTO
        self.assertFalse(
            DailyOvertimeAssignment.objects.filter(schedule=sched, empleado=self.emp_falta).exists()
        )

    def test_penalty_from_PSG_previous_week(self):
        self._add_prev_week_incidence(self.emp_psg, self.psg)
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        self.assertTrue(
            OvertimePenalty.objects.filter(schedule=sched, empleado=self.emp_psg, reason='PSG').exists()
        )

    def test_employee_without_penalty_still_assigned(self):
        self._add_prev_week_incidence(self.emp_falta, self.f)
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        self.assertTrue(
            DailyOvertimeAssignment.objects.filter(schedule=sched, empleado=self.emp_ok).exists()
        )

    def test_penalty_uses_iso_date_range_year_boundary(self):
        """Una falta en la última semana ISO del año X dispara penalty en W1 del año X+1."""
        cross_year = 2026  # 2027-W1 inicia 2027-01-04, así que la prev semana es 2026-W53
        # 2026 tiene 53 semanas ISO
        emp = _mk_emp('YR-1', 'Cross year')
        OvertimeProfile.objects.create(empleado=emp, profile_type=OvertimeProfile.ROTATION_A)
        IncidenceRecord.objects.create(
            empleado=emp,
            fecha=datetime.date.fromisocalendar(cross_year, 53, 1),
            semana_num=53,
            tipo_incidencia=self.f,
            cantidad=Decimal('1.00'),
        )
        sched = generate_overtime_schedule(2027, 1, user=self.user)
        self.assertTrue(
            OvertimePenalty.objects.filter(schedule=sched, empleado=emp).exists()
        )


class OvertimeManualForcedTests(APITestCase):
    iso_year = ANCHOR_YEAR
    iso_week = ANCHOR_WEEK

    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        self.hx, self.f, self.psg = _mk_catalogs()
        self.emp_pen = _mk_emp('PEN-FORCE-1', 'Penalizado')
        OvertimeProfile.objects.create(empleado=self.emp_pen, profile_type=OvertimeProfile.ROTATION_A)
        prev_year = self.iso_year
        prev_week = self.iso_week - 1
        IncidenceRecord.objects.create(
            empleado=self.emp_pen,
            fecha=datetime.date.fromisocalendar(prev_year, prev_week, 3),
            semana_num=prev_week,
            tipo_incidencia=self.f,
            cantidad=Decimal('1.00'),
        )

    def test_forced_manual_assignment_for_penalized(self):
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        # No tiene AUTO
        self.assertFalse(
            DailyOvertimeAssignment.objects.filter(schedule=sched, empleado=self.emp_pen).exists()
        )
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        resp = self.client.post('/api/payroll/overtime/assignments/', {
            'schedule': sched.id,
            'empleado': self.emp_pen.pk,
            'fecha': week_dates[0].isoformat(),
            'assignment_type': DailyOvertimeAssignment.TIPO_1,
            'hours': '8.00',
            'compensation_type': DailyOvertimeAssignment.PAYROLL,
            'is_forced': True,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        assignment = DailyOvertimeAssignment.objects.get(schedule=sched, empleado=self.emp_pen)
        self.assertTrue(assignment.is_forced)
        self.assertEqual(assignment.source, DailyOvertimeAssignment.MANUAL)

    def test_regenerate_draft_preserves_manual_assignments(self):
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        emp = _mk_emp('MAN-1', 'Manual')
        OvertimeProfile.objects.create(empleado=emp, profile_type=OvertimeProfile.FIXED_4DAY)
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        # Regenerar incluye al nuevo empleado
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        # Reemplazar la asignación de lunes con una MANUAL TIPO_2
        existing = DailyOvertimeAssignment.objects.get(
            schedule=sched, empleado=emp, fecha=week_dates[0]
        )
        existing.delete()
        DailyOvertimeAssignment.objects.create(
            schedule=sched,
            empleado=emp,
            fecha=week_dates[0],
            assignment_type=DailyOvertimeAssignment.TIPO_2,
            hours=Decimal('4.00'),
            compensation_type=DailyOvertimeAssignment.TXT,
            source=DailyOvertimeAssignment.MANUAL,
            is_forced=False,
        )
        # Re-generar: la MANUAL debe persistir
        generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        manual = DailyOvertimeAssignment.objects.get(
            schedule=sched, empleado=emp, fecha=week_dates[0]
        )
        self.assertEqual(manual.source, DailyOvertimeAssignment.MANUAL)
        self.assertEqual(manual.compensation_type, DailyOvertimeAssignment.TXT)


class OvertimeScheduleApplyTests(APITestCase):
    iso_year = ANCHOR_YEAR
    iso_week = ANCHOR_WEEK

    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        self.hx, self.f, self.psg = _mk_catalogs()
        self.emp = _mk_emp('APP-1', 'Apply')
        self.emp2 = _mk_emp('APP-2', 'Apply 2')
        OvertimeProfile.objects.create(empleado=self.emp, profile_type=OvertimeProfile.ROTATION_A)
        OvertimeProfile.objects.create(empleado=self.emp2, profile_type=OvertimeProfile.FIXED_4DAY)
        self.sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)

    def _publish(self):
        resp = self.client.post(f'/api/payroll/overtime/schedules/{self.sched.id}/publish/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.sched.refresh_from_db()

    def test_cannot_regenerate_published(self):
        self._publish()
        resp = self.client.post('/api/payroll/overtime/schedules/generate/', {
            'iso_year': self.iso_year, 'iso_week': self.iso_week,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_payroll_closure_blocks_generate(self):
        PayrollClosure.objects.create(iso_year=self.iso_year, semana_num=self.iso_week)
        resp = self.client.post('/api/payroll/overtime/schedules/generate/', {
            'iso_year': self.iso_year, 'iso_week': self.iso_week,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_payroll_closure_blocks_publish_and_apply(self):
        PayrollClosure.objects.create(iso_year=self.iso_year, semana_num=self.iso_week)
        resp = self.client.post(f'/api/payroll/overtime/schedules/{self.sched.id}/publish/')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        resp = self.client.post(
            f'/api/payroll/overtime/schedules/{self.sched.id}/apply-to-incidences/'
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_apply_creates_HX_incidences(self):
        self._publish()
        expected = self.sched.assignments.filter(
            compensation_type=DailyOvertimeAssignment.PAYROLL
        ).count()
        self.assertGreater(expected, 0)
        resp = self.client.post(
            f'/api/payroll/overtime/schedules/{self.sched.id}/apply-to-incidences/'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        hx_count = IncidenceRecord.objects.filter(tipo_incidencia=self.hx).count()
        self.assertEqual(hx_count, expected)
        # Verifica semana_num = fecha.isocalendar()[1]
        for rec in IncidenceRecord.objects.filter(tipo_incidencia=self.hx):
            self.assertEqual(rec.semana_num, rec.fecha.isocalendar()[1])

    def test_apply_ignores_TXT(self):
        # Cambiar una asignación a TXT
        a = self.sched.assignments.first()
        a.compensation_type = DailyOvertimeAssignment.TXT
        a.save()
        expected = self.sched.assignments.filter(
            compensation_type=DailyOvertimeAssignment.PAYROLL
        ).count()
        self._publish()
        self.client.post(
            f'/api/payroll/overtime/schedules/{self.sched.id}/apply-to-incidences/'
        )
        hx_count = IncidenceRecord.objects.filter(tipo_incidencia=self.hx).count()
        self.assertEqual(hx_count, expected)

    def test_apply_sets_status_locked(self):
        self._publish()
        self.client.post(
            f'/api/payroll/overtime/schedules/{self.sched.id}/apply-to-incidences/'
        )
        self.sched.refresh_from_db()
        self.assertEqual(self.sched.status, WeeklyOvertimeSchedule.LOCKED)
        self.assertIsNotNone(self.sched.locked_at)

    def test_apply_twice_returns_409_and_no_duplicates(self):
        self._publish()
        resp1 = self.client.post(
            f'/api/payroll/overtime/schedules/{self.sched.id}/apply-to-incidences/'
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        count_after_first = IncidenceRecord.objects.filter(tipo_incidencia=self.hx).count()
        resp2 = self.client.post(
            f'/api/payroll/overtime/schedules/{self.sched.id}/apply-to-incidences/'
        )
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)
        count_after_second = IncidenceRecord.objects.filter(tipo_incidencia=self.hx).count()
        self.assertEqual(count_after_first, count_after_second)


class OvertimeAssignmentValidationTests(APITestCase):
    iso_year = ANCHOR_YEAR
    iso_week = ANCHOR_WEEK

    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        _mk_catalogs()
        self.emp = _mk_emp('VAL-1', 'Validation')
        OvertimeProfile.objects.create(empleado=self.emp, profile_type=OvertimeProfile.ROTATION_A)
        self.sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        self.week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)

    def _post(self, **overrides):
        payload = {
            'schedule': self.sched.id,
            'empleado': self.emp.pk,
            'fecha': self.week_dates[4].isoformat(),
            'assignment_type': DailyOvertimeAssignment.TIPO_1,
            'hours': '8.00',
            'compensation_type': DailyOvertimeAssignment.PAYROLL,
        }
        payload.update(overrides)
        return self.client.post('/api/payroll/overtime/assignments/', payload, format='json')

    def test_sunday_rejected(self):
        sunday = self.week_dates[5] + datetime.timedelta(days=1)
        resp = self._post(fecha=sunday.isoformat())
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fecha_outside_iso_week_rejected(self):
        outside = self.week_dates[0] - datetime.timedelta(days=7)
        resp = self._post(fecha=outside.isoformat())
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tipo_1_requires_8_hours(self):
        resp = self._post(assignment_type=DailyOvertimeAssignment.TIPO_1, hours='4.00')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tipo_2_requires_4_hours(self):
        resp = self._post(assignment_type=DailyOvertimeAssignment.TIPO_2, hours='8.00')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_custom_requires_positive_hours(self):
        resp = self._post(assignment_type=DailyOvertimeAssignment.CUSTOM, hours='0.00')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_custom_accepts_positive_hours(self):
        # Usar día libre (martes) para evitar choque con AUTO existente
        resp = self._post(
            fecha=self.week_dates[1].isoformat(),
            assignment_type=DailyOvertimeAssignment.CUSTOM,
            hours='6.00',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)


class OvertimeProfileValidationTests(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        self.emp = _mk_emp('PRF-1', 'Profile')

    def test_fixed_custom_requires_weekdays(self):
        resp = self.client.post('/api/payroll/overtime/profiles/', {
            'empleado': self.emp.pk,
            'profile_type': OvertimeProfile.FIXED_CUSTOM,
            'custom_weekdays': [],
            'custom_daily_hours': '6.00',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fixed_custom_requires_positive_hours(self):
        resp = self.client.post('/api/payroll/overtime/profiles/', {
            'empleado': self.emp.pk,
            'profile_type': OvertimeProfile.FIXED_CUSTOM,
            'custom_weekdays': [0, 2],
            'custom_daily_hours': '0',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fixed_custom_rejects_out_of_range_weekday(self):
        resp = self.client.post('/api/payroll/overtime/profiles/', {
            'empleado': self.emp.pk,
            'profile_type': OvertimeProfile.FIXED_CUSTOM,
            'custom_weekdays': [0, 6],
            'custom_daily_hours': '5.00',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creates_valid_profile(self):
        resp = self.client.post('/api/payroll/overtime/profiles/', {
            'empleado': self.emp.pk,
            'profile_type': OvertimeProfile.ROTATION_A,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)


class OvertimeSaturdayOrMondayTests(APITestCase):
    """Reglas del perfil SATURDAY_OR_MONDAY_8H (reemplaza al legacy)."""

    iso_year = ANCHOR_YEAR
    iso_week = ANCHOR_WEEK

    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        _mk_catalogs()
        self.emp_lun = _mk_emp('SM-LUN', 'Lunes')
        self.emp_sab = _mk_emp('SM-SAB', 'Sábado')

    def _post_profile(self, emp, custom_weekdays, profile_type=None):
        return self.client.post('/api/payroll/overtime/profiles/', {
            'empleado': emp.pk,
            'profile_type': profile_type or OvertimeProfile.SATURDAY_OR_MONDAY_8H,
            'custom_weekdays': custom_weekdays,
        }, format='json')

    def test_accepts_lunes_only(self):
        resp = self._post_profile(self.emp_lun, [0])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.emp_lun)
            .values_list('fecha', 'assignment_type', 'hours')
        )
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0][0], week_dates[0])
        self.assertEqual(days[0][1], DailyOvertimeAssignment.TIPO_1)
        self.assertEqual(days[0][2], Decimal('8.00'))

    def test_accepts_sabado_only(self):
        resp = self._post_profile(self.emp_sab, [5])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.emp_sab)
            .values_list('fecha', 'assignment_type', 'hours')
        )
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0][0], week_dates[5])
        self.assertEqual(days[0][1], DailyOvertimeAssignment.TIPO_1)
        self.assertEqual(days[0][2], Decimal('8.00'))

    def test_rejects_empty_weekdays(self):
        resp = self._post_profile(self.emp_lun, [])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_both_days(self):
        resp = self._post_profile(self.emp_lun, [0, 5])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_invalid_day(self):
        resp = self._post_profile(self.emp_lun, [2])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_out_of_range_day(self):
        resp = self._post_profile(self.emp_lun, [6])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_legacy_value_with_weekdays_5_generates_only_saturday(self):
        # Simula una fila migrada con el valor viejo todavía en la BD.
        # bypass del serializer: bulk_create no corre clean().
        DailyOvertimeAssignment.objects.all().delete()
        OvertimeProfile.objects.bulk_create([
            OvertimeProfile(
                empleado=self.emp_sab,
                profile_type=OvertimeProfile.SATURDAY_MONDAY_8H,
                custom_weekdays=[5],
            ),
        ])
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.emp_sab)
            .values_list('fecha', 'assignment_type', 'hours')
        )
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0][0], week_dates[5])
        self.assertEqual(days[0][1], DailyOvertimeAssignment.TIPO_1)
        self.assertEqual(days[0][2], Decimal('8.00'))

    def test_legacy_value_with_empty_weekdays_falls_back_to_saturday(self):
        OvertimeProfile.objects.bulk_create([
            OvertimeProfile(
                empleado=self.emp_sab,
                profile_type=OvertimeProfile.SATURDAY_MONDAY_8H,
                custom_weekdays=[],
            ),
        ])
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        days = list(
            DailyOvertimeAssignment.objects
            .filter(schedule=sched, empleado=self.emp_sab)
            .values_list('fecha', flat=True)
        )
        self.assertEqual(days, [week_dates[5]])


class OvertimePRReviewFixesTests(APITestCase):
    """Cobertura adicional para los puntos del review del PR #29."""

    iso_year = ANCHOR_YEAR
    iso_week = ANCHOR_WEEK

    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(self.user)
        _mk_catalogs()
        self.emp = _mk_emp('REV-1', 'Review')
        OvertimeProfile.objects.create(empleado=self.emp, profile_type=OvertimeProfile.ROTATION_A)

    def test_generate_rejects_nonexistent_iso_week_53(self):
        """2025 tiene 52 semanas ISO; iso_week=53 debe ser 400, no 500."""
        resp = self.client.post('/api/payroll/overtime/schedules/generate/', {
            'iso_year': 2025, 'iso_week': 53,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        self.assertIn('iso_week', resp.data)

    def test_generate_accepts_valid_iso_week_53_in_2026(self):
        """2026 sí tiene 53 semanas ISO; iso_week=53 es válido."""
        resp = self.client.post('/api/payroll/overtime/schedules/generate/', {
            'iso_year': 2026, 'iso_week': 53,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)

    def test_assignment_create_blocked_by_payroll_closure(self):
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        PayrollClosure.objects.create(iso_year=self.iso_year, semana_num=self.iso_week)
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        resp = self.client.post('/api/payroll/overtime/assignments/', {
            'schedule': sched.id,
            'empleado': self.emp.pk,
            'fecha': week_dates[4].isoformat(),
            'assignment_type': DailyOvertimeAssignment.TIPO_1,
            'hours': '8.00',
            'compensation_type': DailyOvertimeAssignment.PAYROLL,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT, resp.content)

    def test_assignment_create_ignores_client_source_auto(self):
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        week_dates = get_overtime_week_dates(self.iso_year, self.iso_week)
        resp = self.client.post('/api/payroll/overtime/assignments/', {
            'schedule': sched.id,
            'empleado': self.emp.pk,
            'fecha': week_dates[4].isoformat(),
            'assignment_type': DailyOvertimeAssignment.TIPO_1,
            'hours': '8.00',
            'compensation_type': DailyOvertimeAssignment.PAYROLL,
            'source': DailyOvertimeAssignment.AUTO,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        a = DailyOvertimeAssignment.objects.get(
            schedule=sched, empleado=self.emp, fecha=week_dates[4]
        )
        self.assertEqual(a.source, DailyOvertimeAssignment.MANUAL)

    def test_direct_post_to_schedules_returns_405(self):
        resp = self.client.post('/api/payroll/overtime/schedules/', {
            'iso_year': self.iso_year, 'iso_week': self.iso_week,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, resp.content)
        # Confirma que la planilla no quedó creada por la vía directa
        self.assertFalse(
            WeeklyOvertimeSchedule.objects.filter(
                iso_year=self.iso_year, iso_week=self.iso_week
            ).exists()
        )

    def test_schedule_patch_rejects_iso_year_change(self):
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        resp = self.client.patch(
            f'/api/payroll/overtime/schedules/{sched.id}/',
            {'iso_year': 2027},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        sched.refresh_from_db()
        self.assertEqual(sched.iso_year, self.iso_year)

    def test_schedule_patch_rejects_iso_week_change(self):
        sched = generate_overtime_schedule(self.iso_year, self.iso_week, user=self.user)
        resp = self.client.patch(
            f'/api/payroll/overtime/schedules/{sched.id}/',
            {'iso_week': self.iso_week + 1},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        sched.refresh_from_db()
        self.assertEqual(sched.iso_week, self.iso_week)
