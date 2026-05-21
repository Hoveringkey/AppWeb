from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


OVERTIME_ROTATION_ANCHOR_ISO_YEAR = 2026
OVERTIME_ROTATION_ANCHOR_ISO_WEEK = 21


class Schedule(models.Model):
    time_range = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.time_range

class Employee(models.Model):
    no_nomina = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=255)
    puesto = models.CharField(max_length=255)
    fecha_ingreso = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    fecha_baja = models.DateField(null=True, blank=True)
    motivo_baja = models.TextField(null=True, blank=True)
    horario_lv = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, related_name='employees_lv')
    horario_s = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees_s')
    vacaciones_historicas_disfrutadas = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.no_nomina} - {self.nombre}"

class IncidenceCatalog(models.Model):
    tipo = models.CharField(max_length=100)
    abreviatura = models.CharField(max_length=10)
    aplica_bono_mensual = models.BooleanField(default=False)
    aplica_bono_semanal = models.BooleanField(default=False)
    aplica_incentivo = models.BooleanField(default=False)

    def __str__(self):
        return self.tipo

class IncidenceRecord(models.Model):
    fecha = models.DateField()
    semana_num = models.IntegerField()
    empleado = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='incidences')
    tipo_incidencia = models.ForeignKey(IncidenceCatalog, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('empleado', 'fecha', 'tipo_incidencia')

    def __str__(self):
        return f"{self.empleado.no_nomina} - {self.tipo_incidencia.abreviatura} ({self.fecha})"

class Loan(models.Model):
    empleado = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    abono_semanal = models.DecimalField(max_digits=10, decimal_places=2)
    pagos_realizados = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='PENDIENTE', choices=[
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('CANCELADO', 'Cancelado')
    ])

    def __str__(self):
        return f"Loan for {self.empleado.nombre}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['empleado'],
                condition=models.Q(is_active=True),
                name='unique_active_loan_per_employee',
            ),
        ]

class ExtraHourBank(models.Model):
    empleado = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='extra_hours')
    horas_deuda = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Extra Hours for {self.empleado.nombre}: {self.horas_deuda}"

class PayrollClosure(models.Model):
    iso_year = models.IntegerField()
    semana_num = models.IntegerField()
    closed_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    total_employees = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='CLOSED')
    checksum = models.CharField(max_length=128, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['iso_year', 'semana_num'],
                name='unique_payroll_closure_iso_year_week',
            ),
        ]
        ordering = ['-iso_year', '-semana_num']

    def __str__(self):
        return f"Payroll closure {self.iso_year}-W{self.semana_num}"

class PayrollSnapshot(models.Model):
    """Immutable audit record written once when a payroll week is permanently closed."""
    iso_year = models.IntegerField(null=True, blank=True, db_index=True)
    semana_num = models.IntegerField(db_index=True)
    closure = models.ForeignKey(
        PayrollClosure,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='snapshots',
    )
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    empleado_no_nomina = models.CharField(max_length=50)
    empleado_nombre = models.CharField(max_length=255)
    total_pagar = models.DecimalField(max_digits=10, decimal_places=2)
    desglose = models.JSONField()  # Full calculation dict for this employee

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['closure', 'empleado_no_nomina'],
                name='unique_payroll_snapshot_closure_employee',
            ),
        ]
        ordering = ['-fecha_cierre']

    def __str__(self):
        return f"Snapshot S{self.semana_num} – {self.empleado_no_nomina}"


class OvertimeProfile(models.Model):
    ROTATION_A = 'ROTATION_A'
    ROTATION_B = 'ROTATION_B'
    SATURDAY_OR_MONDAY_8H = 'SATURDAY_OR_MONDAY_8H'
    SATURDAY_MONDAY_8H = 'SATURDAY_MONDAY_8H'  # legacy: migrado a SATURDAY_OR_MONDAY_8H
    FIXED_4DAY = 'FIXED_4DAY'
    FIXED_CUSTOM = 'FIXED_CUSTOM'

    PROFILE_TYPE_CHOICES = [
        (ROTATION_A, 'Rotación A (lun-mié / mar-jue)'),
        (ROTATION_B, 'Rotación B (mar-jue / lun-mié)'),
        (SATURDAY_OR_MONDAY_8H, 'Sábado o Lunes 8h'),
        (SATURDAY_MONDAY_8H, 'Sábado o Lunes 8h (legacy)'),
        (FIXED_4DAY, 'Lunes a jueves fijo'),
        (FIXED_CUSTOM, 'Personalizado'),
    ]

    empleado = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name='overtime_profile'
    )
    profile_type = models.CharField(max_length=32, choices=PROFILE_TYPE_CHOICES)
    custom_weekdays = models.JSONField(default=list, blank=True)
    custom_daily_hours = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OvertimeProfile {self.empleado_id} ({self.profile_type})"

    def clean(self):
        super().clean()
        if self.profile_type == self.FIXED_CUSTOM:
            if not self.custom_weekdays:
                raise ValidationError({'custom_weekdays': 'Requerido para FIXED_CUSTOM.'})
            if not isinstance(self.custom_weekdays, list):
                raise ValidationError({'custom_weekdays': 'Debe ser una lista.'})
            for d in self.custom_weekdays:
                if not isinstance(d, int) or d < 0 or d > 5:
                    raise ValidationError({
                        'custom_weekdays': 'Cada día debe ser entero entre 0 (lunes) y 5 (sábado).'
                    })
            if self.custom_daily_hours is None or self.custom_daily_hours <= 0:
                raise ValidationError({'custom_daily_hours': 'Debe ser mayor a 0 para FIXED_CUSTOM.'})

        if self.profile_type in (self.SATURDAY_OR_MONDAY_8H, self.SATURDAY_MONDAY_8H):
            if not isinstance(self.custom_weekdays, list) or len(self.custom_weekdays) != 1:
                raise ValidationError({
                    'custom_weekdays': 'Debe contener exactamente un día: [0]=Lunes o [5]=Sábado.'
                })
            day = self.custom_weekdays[0]
            if day not in (0, 5):
                raise ValidationError({
                    'custom_weekdays': 'Día único permitido: 0 (Lunes) o 5 (Sábado).'
                })


class WeeklyOvertimeSchedule(models.Model):
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    LOCKED = 'LOCKED'

    STATUS_CHOICES = [
        (DRAFT, 'Borrador'),
        (PUBLISHED, 'Publicada'),
        (LOCKED, 'Bloqueada'),
    ]

    iso_year = models.IntegerField()
    iso_week = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['iso_year', 'iso_week'],
                name='unique_overtime_schedule_iso_year_week',
            ),
        ]
        ordering = ['-iso_year', '-iso_week']

    def __str__(self):
        return f"WeeklyOvertimeSchedule {self.iso_year}-W{self.iso_week} ({self.status})"


class DailyOvertimeAssignment(models.Model):
    TIPO_1 = 'TIPO_1'
    TIPO_2 = 'TIPO_2'
    CUSTOM = 'CUSTOM'
    ASSIGNMENT_TYPE_CHOICES = [
        (TIPO_1, '1º Tiempo (8h)'),
        (TIPO_2, '2º Tiempo (4h)'),
        (CUSTOM, 'Personalizado'),
    ]

    PAYROLL = 'PAYROLL'
    TXT = 'TXT'
    COMPENSATION_TYPE_CHOICES = [
        (PAYROLL, 'Nómina'),
        (TXT, 'Tiempo por Tiempo'),
    ]

    AUTO = 'AUTO'
    MANUAL = 'MANUAL'
    SOURCE_CHOICES = [(AUTO, 'Auto'), (MANUAL, 'Manual')]

    schedule = models.ForeignKey(
        WeeklyOvertimeSchedule,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    empleado = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='overtime_assignments',
    )
    fecha = models.DateField()
    assignment_type = models.CharField(max_length=10, choices=ASSIGNMENT_TYPE_CHOICES)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    compensation_type = models.CharField(
        max_length=10, choices=COMPENSATION_TYPE_CHOICES, default=PAYROLL
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=AUTO)
    is_forced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'empleado', 'fecha'],
                name='unique_overtime_assignment_schedule_emp_fecha',
            ),
        ]
        ordering = ['fecha', 'empleado_id']

    def __str__(self):
        return f"{self.empleado_id} {self.fecha} {self.assignment_type}"


class OvertimePenalty(models.Model):
    schedule = models.ForeignKey(
        WeeklyOvertimeSchedule,
        on_delete=models.CASCADE,
        related_name='penalties',
    )
    empleado = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='overtime_penalties',
    )
    reason = models.CharField(max_length=10)
    source_incidence_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'empleado'],
                name='unique_overtime_penalty_schedule_empleado',
            ),
        ]

    def __str__(self):
        return f"Penalty {self.empleado_id} {self.reason} ({self.source_incidence_date})"
