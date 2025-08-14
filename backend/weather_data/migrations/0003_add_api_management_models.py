# Generated manually for API management models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('weather_data', '0002_add_performance_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='APIProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('base_url', models.URLField()),
                ('api_key', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('priority', models.IntegerField(default=1, help_text='Lower number = higher priority')),
                ('requests_per_minute', models.IntegerField(default=60)),
                ('requests_per_day', models.IntegerField(default=1000)),
                ('requests_per_month', models.IntegerField(default=100000)),
                ('cost_per_request', models.DecimalField(decimal_places=6, default=0.0, max_digits=10)),
                ('monthly_budget', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('last_health_check', models.DateTimeField(blank=True, null=True)),
                ('is_healthy', models.BooleanField(default=True)),
                ('error_count', models.IntegerField(default=0)),
                ('success_rate', models.FloatField(default=100.0)),
                ('supported_endpoints', models.JSONField(default=list)),
                ('configuration', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'API Provider',
                'verbose_name_plural': 'API Providers',
                'ordering': ['priority', 'name'],
            },
        ),
        migrations.CreateModel(
            name='APIUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('endpoint', models.CharField(max_length=200)),
                ('request_count', models.IntegerField(default=0)),
                ('success_count', models.IntegerField(default=0)),
                ('error_count', models.IntegerField(default=0)),
                ('avg_response_time', models.FloatField(default=0.0)),
                ('max_response_time', models.FloatField(default=0.0)),
                ('cost', models.DecimalField(decimal_places=6, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_records', to='weather_data.apiprovider')),
            ],
            options={
                'verbose_name': 'API Usage',
                'verbose_name_plural': 'API Usage Records',
            },
        ),
        migrations.CreateModel(
            name='APIFailover',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=200)),
                ('endpoint', models.CharField(max_length=200)),
                ('error_details', models.TextField(blank=True)),
                ('failed_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('fallback_provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='failover_events_as_fallback', to='weather_data.apiprovider')),
                ('primary_provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='failover_events_as_primary', to='weather_data.apiprovider')),
            ],
            options={
                'verbose_name': 'API Failover Event',
                'verbose_name_plural': 'API Failover Events',
                'ordering': ['-failed_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='apiusage',
            unique_together={('provider', 'date', 'endpoint')},
        ),
    ]