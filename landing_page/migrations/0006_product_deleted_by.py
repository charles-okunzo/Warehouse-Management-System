# Generated by Django 4.2.6 on 2023-12-13 12:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('landing_page', '0005_product_deleted_at_product_is_deleted_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
