# Enhanced user management system migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('accounts', '0002_auto_20250813_1905'),
    ]

    operations = [
        # Add new fields to existing User model
        migrations.AddField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pics/'),
        ),
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='user',
            name='location',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='UTC', max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='preferred_units',
            field=models.CharField(
                choices=[('metric', 'Metric'), ('imperial', 'Imperial')],
                default='metric',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='language',
            field=models.CharField(default='en', max_length=10),
        ),
        migrations.AddField(
            model_name='user',
            name='last_activity',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='login_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_token',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='api_key',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='api_requests_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='api_rate_limit',
            field=models.PositiveIntegerField(default=1000),
        ),
        
        # Rename existing field
        migrations.RenameField(
            model_name='user',
            old_name='is_email_verified',
            new_name='is_verified',
        ),
        
        # Add new fields to existing UserProfile model
        migrations.AddField(
            model_name='userprofile',
            name='dashboard_layout',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='favorite_cities',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='default_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='push_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='show_air_quality',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='show_forecasts',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='forecast_days',
            field=models.PositiveIntegerField(default=5),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_visibility',
            field=models.CharField(
                choices=[('public', 'Public'), ('private', 'Private'), ('friends', 'Friends Only')],
                default='private',
                max_length=20
            ),
        ),
        
        # Rename existing fields in UserProfile
        migrations.RenameField(
            model_name='userprofile',
            old_name='receive_email_alerts',
            new_name='email_notifications',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='receive_sms_alerts',
            new_name='sms_notifications',
        ),
        
        # Create new models
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('permissions', models.ManyToManyField(blank=True, to='auth.permission')),
            ],
            options={
                'verbose_name': 'User Role',
                'verbose_name_plural': 'User Roles',
            },
        ),
        
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(
                    choices=[
                        ('login', 'Login'), ('logout', 'Logout'), ('api_request', 'API Request'),
                        ('profile_update', 'Profile Update'), ('password_change', 'Password Change'),
                        ('city_search', 'City Search'), ('weather_view', 'Weather View'),
                        ('forecast_view', 'Forecast View')
                    ],
                    max_length=50
                )),
                ('description', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='accounts.user')),
            ],
            options={
                'verbose_name': 'User Activity',
                'verbose_name_plural': 'User Activities',
                'ordering': ['-timestamp'],
            },
        ),
        
        migrations.CreateModel(
            name='UserAPIUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('endpoint', models.CharField(max_length=200)),
                ('request_count', models.PositiveIntegerField(default=0)),
                ('success_count', models.PositiveIntegerField(default=0)),
                ('error_count', models.PositiveIntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_usage', to='accounts.user')),
            ],
            options={
                'verbose_name': 'API Usage',
                'verbose_name_plural': 'API Usage Records',
                'unique_together': {('user', 'date', 'endpoint')},
            },
        ),
        
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(max_length=40, unique=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField()),
                ('location', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='accounts.user')),
            ],
            options={
                'verbose_name': 'User Session',
                'verbose_name_plural': 'User Sessions',
                'ordering': ['-last_activity'],
            },
        ),
    ]