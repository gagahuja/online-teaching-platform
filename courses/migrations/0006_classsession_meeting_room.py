from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_classsession_meeting_room'),
    ]

    operations = [
        migrations.RunSQL(
            sql="SELECT 1;",
            reverse_sql="SELECT 1;"
        ),
    ]


