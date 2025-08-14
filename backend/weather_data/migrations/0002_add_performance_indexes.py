# Generated performance optimization migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather_data', '0001_initial'),
    ]

    operations = [
        # Add indexes for better query performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_weather_data_timestamp ON weather_data_weatherdata (timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_weather_data_timestamp;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_weather_data_city_timestamp ON weather_data_weatherdata (city_id, timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_weather_data_city_timestamp;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_weather_data_temperature ON weather_data_weatherdata (temperature);",
            reverse_sql="DROP INDEX IF EXISTS idx_weather_data_temperature;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_air_quality_timestamp ON weather_data_airqualitydata (timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_air_quality_timestamp;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_air_quality_city_timestamp ON weather_data_airqualitydata (city_id, timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_air_quality_city_timestamp;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_city_active ON weather_data_city (is_active) WHERE is_active = true;",
            reverse_sql="DROP INDEX IF EXISTS idx_city_active;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_forecast_date ON weather_data_weatherforecast (forecast_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_forecast_date;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_forecast_city_date ON weather_data_weatherforecast (city_id, forecast_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_forecast_city_date;"
        ),
    ]