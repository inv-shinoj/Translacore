from django.db import migrations


def seed_form_types(apps, schema_editor):
    FormType = apps.get_model("forms", "FormType")

    # Enum values (must match forms.enums.FormTypeKey)
    FORM_TYPES = [
        (1, "Project", "Project creation form"),
    ]

    for key, name, description in FORM_TYPES:
        FormType.objects.get_or_create(
            key=key,
            defaults={
                "name": name,
                "description": description,
                "is_active": True,
            }
        )


def reverse_seed_form_types(apps, schema_editor):
    FormType = apps.get_model("forms", "FormType")
    FormType.objects.filter(key__in=[1, 2, 3, 4]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0001_initial"),  
    ]

    operations = [
        migrations.RunPython(
            seed_form_types,
            reverse_code=reverse_seed_form_types
        )
    ]
