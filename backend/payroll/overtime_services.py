"""Servicios del módulo de Programación Semanal de Tiempo Extra.

Sienta capa de planeación sobre el motor de nómina existente:
- Genera asignaciones AUTO a partir de OvertimeProfile y la paridad de rotación
  anclada en (OVERTIME_ROTATION_ANCHOR_ISO_YEAR, OVERTIME_ROTATION_ANCHOR_ISO_WEEK).
- Detecta penalizaciones (F/PSG) en la semana ISO anterior.
- Aplica la planilla a IncidenceRecord (HX) sin modificar el motor de cálculo.
"""

import datetime
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

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
    WeeklyOvertimeSchedule,
)
from .services import get_iso_week_date_range


PENALTY_ABREVIATURAS = ('F', 'PSG')
HOURS_TIPO_1 = Decimal('8.00')
HOURS_TIPO_2 = Decimal('4.00')


def get_overtime_week_dates(iso_year, iso_week):
    """Devuelve las 6 fechas lunes..sábado de la semana ISO."""
    monday = datetime.date.fromisocalendar(iso_year, iso_week, 1)
    return [monday + timedelta(days=i) for i in range(6)]


def _iso_weeks_in_year(year):
    """Devuelve la cantidad de semanas ISO en un año dado (52 o 53)."""
    # 28-dic siempre cae en la última semana ISO del año.
    return datetime.date(year, 12, 28).isocalendar()[1]


def _iso_week_diff(iso_year, iso_week, anchor_year, anchor_week):
    """Diferencia (con signo) entre dos semanas ISO en cantidad de semanas."""
    target_monday = datetime.date.fromisocalendar(iso_year, iso_week, 1)
    anchor_monday = datetime.date.fromisocalendar(anchor_year, anchor_week, 1)
    delta_days = (target_monday - anchor_monday).days
    # Las semanas ISO siempre arrancan en lunes, así que el delta es múltiplo de 7.
    return delta_days // 7


def get_overtime_rotation_parity(iso_year, iso_week):
    """Retorna 'A' o 'B' usando la diferencia en semanas respecto al ancla.

    No se usa iso_week % 2 porque el calendario ISO puede tener 53 semanas
    en algunos años; el ancla absoluta evita saltos espurios.
    """
    diff = _iso_week_diff(
        iso_year, iso_week,
        OVERTIME_ROTATION_ANCHOR_ISO_YEAR,
        OVERTIME_ROTATION_ANCHOR_ISO_WEEK,
    )
    return 'A' if diff % 2 == 0 else 'B'


def get_profile_weekdays(profile, parity):
    """Devuelve [(weekday_idx, assignment_type, hours)] que aplican al perfil."""
    p_type = profile.profile_type

    if p_type == OvertimeProfile.ROTATION_A:
        if parity == 'A':
            return [(0, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1),
                    (2, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1)]
        return [(1, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1),
                (3, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1)]

    if p_type == OvertimeProfile.ROTATION_B:
        if parity == 'A':
            return [(1, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1),
                    (3, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1)]
        return [(0, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1),
                (2, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1)]

    if p_type == OvertimeProfile.SATURDAY_MONDAY_8H:
        return [(5, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1),
                (0, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1)]

    if p_type == OvertimeProfile.FIXED_4DAY:
        return [(d, DailyOvertimeAssignment.TIPO_1, HOURS_TIPO_1) for d in range(4)]

    if p_type == OvertimeProfile.FIXED_CUSTOM:
        hours = profile.custom_daily_hours or Decimal('0.00')
        return [
            (int(d), DailyOvertimeAssignment.CUSTOM, hours)
            for d in (profile.custom_weekdays or [])
        ]

    return []


def _previous_iso_week(iso_year, iso_week):
    """Devuelve (prev_iso_year, prev_iso_week) manejando salto de año."""
    if iso_week > 1:
        return iso_year, iso_week - 1
    prev_year = iso_year - 1
    return prev_year, _iso_weeks_in_year(prev_year)


def detect_overtime_penalties(iso_year, iso_week):
    """Detecta F/PSG en la semana ISO anterior y devuelve dicts."""
    prev_year, prev_week = _previous_iso_week(iso_year, iso_week)
    prev_monday, prev_sunday = get_iso_week_date_range(prev_year, prev_week)

    records = (
        IncidenceRecord.objects
        .filter(
            fecha__gte=prev_monday,
            fecha__lte=prev_sunday,
            tipo_incidencia__abreviatura__in=PENALTY_ABREVIATURAS,
        )
        .select_related('empleado', 'tipo_incidencia')
        .order_by('empleado_id', 'fecha')
    )

    seen = set()
    out = []
    for rec in records:
        if rec.empleado_id in seen:
            continue
        seen.add(rec.empleado_id)
        out.append({
            'empleado': rec.empleado,
            'reason': rec.tipo_incidencia.abreviatura,
            'source_incidence_date': rec.fecha,
        })
    return out


class OvertimeScheduleLockedError(Exception):
    """La planilla ya no admite cambios automáticos (PUBLISHED/LOCKED)."""


class OvertimeWeekClosedError(Exception):
    """La semana objetivo ya tiene PayrollClosure: no se puede operar."""


@transaction.atomic
def generate_overtime_schedule(iso_year, iso_week, user=None):
    if PayrollClosure.objects.filter(iso_year=iso_year, semana_num=iso_week).exists():
        raise OvertimeWeekClosedError()

    schedule, created = WeeklyOvertimeSchedule.objects.select_for_update().get_or_create(
        iso_year=iso_year,
        iso_week=iso_week,
        defaults={'created_by': user},
    )
    if not created and schedule.status != WeeklyOvertimeSchedule.DRAFT:
        raise OvertimeScheduleLockedError()

    parity = get_overtime_rotation_parity(iso_year, iso_week)
    week_dates = get_overtime_week_dates(iso_year, iso_week)

    # Recompute penalties: borrar y reescribir.
    OvertimePenalty.objects.filter(schedule=schedule).delete()
    penalty_dicts = detect_overtime_penalties(iso_year, iso_week)
    penalty_emp_ids = {p['empleado'].pk for p in penalty_dicts}

    OvertimePenalty.objects.bulk_create([
        OvertimePenalty(
            schedule=schedule,
            empleado=p['empleado'],
            reason=p['reason'],
            source_incidence_date=p['source_incidence_date'],
        )
        for p in penalty_dicts
    ])

    # Borrar solo AUTO no forzado; preservar MANUAL y is_forced=True.
    DailyOvertimeAssignment.objects.filter(
        schedule=schedule,
        source=DailyOvertimeAssignment.AUTO,
        is_forced=False,
    ).delete()

    # Asignaciones existentes que se preservan: para no chocar con UNIQUE.
    preserved = set(
        DailyOvertimeAssignment.objects
        .filter(schedule=schedule)
        .values_list('empleado_id', 'fecha')
    )

    profiles = (
        OvertimeProfile.objects
        .filter(is_active=True, empleado__is_active=True)
        .select_related('empleado')
    )

    to_create = []
    for profile in profiles:
        if profile.empleado_id in penalty_emp_ids:
            continue
        for weekday_idx, assignment_type, hours in get_profile_weekdays(profile, parity):
            fecha = week_dates[weekday_idx]
            if (profile.empleado_id, fecha) in preserved:
                continue
            to_create.append(DailyOvertimeAssignment(
                schedule=schedule,
                empleado=profile.empleado,
                fecha=fecha,
                assignment_type=assignment_type,
                hours=hours,
                compensation_type=DailyOvertimeAssignment.PAYROLL,
                source=DailyOvertimeAssignment.AUTO,
                is_forced=False,
            ))

    DailyOvertimeAssignment.objects.bulk_create(to_create)

    schedule.save(update_fields=['updated_at']) if not created else None
    return schedule


@transaction.atomic
def apply_overtime_schedule_to_incidences(schedule, user=None):
    if schedule.status != WeeklyOvertimeSchedule.PUBLISHED:
        raise OvertimeScheduleLockedError()

    if PayrollClosure.objects.filter(
        iso_year=schedule.iso_year, semana_num=schedule.iso_week
    ).exists():
        raise OvertimeWeekClosedError()

    try:
        hx_catalog = IncidenceCatalog.objects.get(abreviatura='HX')
    except IncidenceCatalog.DoesNotExist as exc:
        raise ValueError("IncidenceCatalog 'HX' no existe en el catálogo.") from exc

    payroll_assignments = schedule.assignments.filter(
        compensation_type=DailyOvertimeAssignment.PAYROLL
    )

    created = 0
    updated = 0
    for a in payroll_assignments:
        semana_num = a.fecha.isocalendar()[1]
        _, was_created = IncidenceRecord.objects.update_or_create(
            empleado=a.empleado,
            fecha=a.fecha,
            tipo_incidencia=hx_catalog,
            defaults={'cantidad': a.hours, 'semana_num': semana_num},
        )
        if was_created:
            created += 1
        else:
            updated += 1

    schedule.status = WeeklyOvertimeSchedule.LOCKED
    schedule.locked_at = timezone.now()
    schedule.save(update_fields=['status', 'locked_at', 'updated_at'])

    return {
        'incidences_created': created,
        'incidences_updated': updated,
        'total_payroll_assignments': payroll_assignments.count(),
    }
