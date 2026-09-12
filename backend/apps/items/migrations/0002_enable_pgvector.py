from django.db import migrations


def enable_vector_extension(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "CREATE EXTENSION IF NOT EXISTS vector"
        )


class Migration(migrations.Migration):
    dependencies = [("items", "0001_initial")]
    operations = [
        migrations.RunPython(
            enable_vector_extension,
            migrations.RunPython.noop,
        )
    ]
