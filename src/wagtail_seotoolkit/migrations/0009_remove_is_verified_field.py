# Generated migration to remove is_verified field

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("wagtail_seotoolkit", "0008_pluginemailverification"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pluginemailverification",
            name="is_verified",
        ),
    ]
