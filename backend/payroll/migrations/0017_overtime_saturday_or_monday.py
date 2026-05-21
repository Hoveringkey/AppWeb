from django.db import migrations, models


PROFILE_TYPE_CHOICES_NEW = [
    ('ROTATION_A', 'Rotación A (lun-mié / mar-jue)'),
    ('ROTATION_B', 'Rotación B (mar-jue / lun-mié)'),
    ('SATURDAY_OR_MONDAY_8H', 'Sábado o Lunes 8h'),
    ('SATURDAY_MONDAY_8H', 'Sábado o Lunes 8h (legacy)'),
    ('FIXED_4DAY', 'Lunes a jueves fijo'),
    ('FIXED_CUSTOM', 'Personalizado'),
]

PROFILE_TYPE_CHOICES_OLD = [
    ('ROTATION_A', 'Rotación A (lun-mié / mar-jue)'),
    ('ROTATION_B', 'Rotación B (mar-jue / lun-mié)'),
    ('SATURDAY_MONDAY_8H', 'Sábado y lunes 8h'),
    ('FIXED_4DAY', 'Lunes a jueves fijo'),
    ('FIXED_CUSTOM', 'Personalizado'),
]


def migrate_saturday_monday_to_or(apps, schema_editor):
    OvertimeProfile = apps.get_model('payroll', 'OvertimeProfile')
    for profile in OvertimeProfile.objects.filter(profile_type='SATURDAY_MONDAY_8H'):
        weekdays = profile.custom_weekdays
        if not isinstance(weekdays, list) or not weekdays:
            profile.custom_weekdays = [5]
        elif weekdays == [0] or weekdays == [5]:
            pass  # respetar selección existente
        else:
            # cualquier otro valor (incluyendo [0, 5] del modelo viejo) -> default sábado
            profile.custom_weekdays = [5]
        profile.profile_type = 'SATURDAY_OR_MONDAY_8H'
        profile.save(update_fields=['profile_type', 'custom_weekdays'])


def reverse_or_to_saturday_monday(apps, schema_editor):
    OvertimeProfile = apps.get_model('payroll', 'OvertimeProfile')
    OvertimeProfile.objects.filter(profile_type='SATURDAY_OR_MONDAY_8H').update(
        profile_type='SATURDAY_MONDAY_8H'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0016_overtimeprofile_weeklyovertimeschedule_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overtimeprofile',
            name='profile_type',
            field=models.CharField(max_length=32, choices=PROFILE_TYPE_CHOICES_NEW),
        ),
        migrations.RunPython(
            migrate_saturday_monday_to_or,
            reverse_or_to_saturday_monday,
        ),
    ]
