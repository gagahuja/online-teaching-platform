from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_classsession_is_active'),
    ]

    operations = [
        migrations.RunSQL(
            sql="SELECT 1;",
            reverse_sql="SELECT 1;"
        ),
    ]

