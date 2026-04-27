from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("collaboration", "0003_collaborationtextoperation"),
    ]

    operations = [
        migrations.AddField(
            model_name="collaborationtextoperation",
            name="client_id",
            field=models.CharField(default="", max_length=255),
        ),
        migrations.AddField(
            model_name="collaborationtextoperation",
            name="client_sequence",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name="collaborationtextoperation",
            unique_together={
                ("room", "node_id", "applied_version"),
                ("room", "node_id", "client_id", "client_sequence"),
            },
        ),
    ]
