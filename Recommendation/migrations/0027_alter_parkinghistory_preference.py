# Generated by Django 5.0.6 on 2024-09-04 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Recommendation', '0026_remove_parkinghistory_walking_time_1_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parkinghistory',
            name='preference',
            field=models.CharField(choices=[('Pay Less', 'Pay Less'), ('Walk Less', 'Walk Less')], max_length=50),
        ),
    ]
