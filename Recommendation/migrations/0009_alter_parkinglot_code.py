# Generated by Django 5.0.6 on 2024-06-24 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Recommendation', '0008_alter_usersetting_address_alter_usersetting_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parkinglot',
            name='code',
            field=models.CharField(max_length=3, primary_key=True, serialize=False),
        ),
    ]
