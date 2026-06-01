# Convert AddOn.menu (ForeignKey) -> AddOn.menus (ManyToManyField),
# preserving any existing menu links.

from django.db import migrations, models


def copy_menu_to_menus(apps, schema_editor):
    AddOn = apps.get_model("inventory", "AddOn")
    for addon in AddOn.objects.all():
        if addon.menu_id:
            addon.menus.add(addon.menu_id)


def copy_menus_to_menu(apps, schema_editor):
    # Reverse: take the first linked menu back into the FK.
    AddOn = apps.get_model("inventory", "AddOn")
    for addon in AddOn.objects.all():
        first = addon.menus.first()
        if first:
            addon.menu_id = first.id
            addon.save(update_fields=["menu"])


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_addon"),
    ]

    operations = [
        # 1. Add the new M2M with a temporary related_name so it doesn't clash
        #    with the FK's 'addons' reverse accessor while both fields coexist.
        migrations.AddField(
            model_name="addon",
            name="menus",
            field=models.ManyToManyField(
                blank=True, related_name="addons_tmp", to="inventory.smoothiemenu"
            ),
        ),
        # 2. Copy existing FK links into the M2M.
        migrations.RunPython(copy_menu_to_menus, copy_menus_to_menu),
        # 3. Drop the old FK.
        migrations.RemoveField(
            model_name="addon",
            name="menu",
        ),
        # 4. Restore the intended related_name now that the FK is gone.
        migrations.AlterField(
            model_name="addon",
            name="menus",
            field=models.ManyToManyField(
                blank=True, related_name="addons", to="inventory.smoothiemenu"
            ),
        ),
    ]
