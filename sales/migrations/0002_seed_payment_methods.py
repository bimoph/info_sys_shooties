from django.db import migrations

ALLOWED = ['QRIS', 'Cash', 'Shooties Passport']


def seed_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model('sales', 'PaymentMethod')

    # Ensure the three allowed methods exist and are active.
    for name in ALLOWED:
        pm, _ = PaymentMethod.objects.get_or_create(name=name)
        if not pm.is_active:
            pm.is_active = True
            pm.save(update_fields=['is_active'])

    # Deactivate any other payment methods (kept for historical orders).
    PaymentMethod.objects.exclude(name__in=ALLOWED).update(is_active=False)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_payment_methods, noop),
    ]
