"""
Django management command for user management operations
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import csv
import json

from accounts.user_management import user_manager, role_manager
from accounts.models import UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Manage users with various operations'

    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            choices=[
                'stats', 'create_role', 'assign_role', 'bulk_update',
                'cleanup_inactive', 'export_users', 'send_notification'
            ],
            help='Operation to perform'
        )
        
        # Common arguments
        parser.add_argument('--email', help='User email')
        parser.add_argument('--user-ids', nargs='+', type=int, help='List of user IDs')
        parser.add_argument('--days', type=int, default=30, help='Number of days for time-based operations')
        
        # Role management
        parser.add_argument('--role-name', help='Role name')
        parser.add_argument('--role-description', help='Role description')
        parser.add_argument('--permissions', nargs='+', help='List of permission codenames')
        
        # Bulk operations
        parser.add_argument('--activate', action='store_true', help='Activate users')
        parser.add_argument('--deactivate', action='store_true', help='Deactivate users')
        parser.add_argument('--verify', action='store_true', help='Verify users')
        
        # Export
        parser.add_argument('--output-file', help='Output file path')
        parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Export format')
        
        # Notifications
        parser.add_argument('--subject', help='Notification subject')
        parser.add_argument('--message', help='Notification message')
        parser.add_argument('--notification-type', choices=['email', 'sms'], default='email')

    def handle(self, *args, **options):
        operation = options['operation']
        
        try:
            if operation == 'stats':
                self.show_user_statistics(options)
            elif operation == 'create_role':
                self.create_role(options)
            elif operation == 'assign_role':
                self.assign_role(options)
            elif operation == 'bulk_update':
                self.bulk_update_users(options)
            elif operation == 'cleanup_inactive':
                self.cleanup_inactive_users(options)
            elif operation == 'export_users':
                self.export_users(options)
            elif operation == 'send_notification':
                self.send_notification(options)
                
        except Exception as e:
            raise CommandError(f'Error executing {operation}: {str(e)}')

    def show_user_statistics(self, options):
        """Show user statistics"""
        days = options['days']
        stats = user_manager.get_user_statistics(days)
        
        self.stdout.write(self.style.SUCCESS(f'\n=== User Statistics (Last {days} days) ==='))
        self.stdout.write(f"Total Users: {stats['total_users']}")
        self.stdout.write(f"Active Users: {stats['active_users']}")
        self.stdout.write(f"Verified Users: {stats['verified_users']}")
        self.stdout.write(f"Staff Users: {stats['staff_users']}")
        self.stdout.write(f"New Users (Period): {stats['new_users_period']}")
        self.stdout.write(f"Active Users (Period): {stats['active_users_period']}")
        
        if stats['activity_breakdown']:
            self.stdout.write('\n=== Activity Breakdown ===')
            for activity_type, count in stats['activity_breakdown'].items():
                self.stdout.write(f"{activity_type}: {count}")
        
        if stats['api_usage']:
            self.stdout.write('\n=== API Usage ===')
            api_stats = stats['api_usage']
            self.stdout.write(f"Total Requests: {api_stats.get('total_requests', 0)}")
            avg_success = api_stats.get('avg_success_rate', 0)
            if avg_success:
                self.stdout.write(f"Average Success Rate: {avg_success:.2f}%")

    def create_role(self, options):
        """Create a new user role"""
        role_name = options.get('role_name')
        if not role_name:
            raise CommandError('--role-name is required for create_role operation')
        
        role_description = options.get('role_description', '')
        permissions = options.get('permissions', [])
        
        role = role_manager.create_role(role_name, role_description, permissions)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created role: {role.name}')
        )
        
        if permissions:
            self.stdout.write(f'Assigned permissions: {", ".join(permissions)}')

    def assign_role(self, options):
        """Assign role to users"""
        role_name = options.get('role_name')
        user_ids = options.get('user_ids')
        
        if not role_name:
            raise CommandError('--role-name is required for assign_role operation')
        if not user_ids:
            raise CommandError('--user-ids is required for assign_role operation')
        
        count = user_manager.assign_role_to_users(user_ids, role_name)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned role "{role_name}" to {count} users')
        )

    def bulk_update_users(self, options):
        """Bulk update users"""
        user_ids = options.get('user_ids')
        if not user_ids:
            raise CommandError('--user-ids is required for bulk_update operation')
        
        updates = {}
        if options.get('activate'):
            updates['is_active'] = True
        elif options.get('deactivate'):
            updates['is_active'] = False
        
        if options.get('verify'):
            updates['is_verified'] = True
        
        if not updates:
            raise CommandError('No update operations specified (use --activate, --deactivate, or --verify)')
        
        count = user_manager.bulk_update_users(user_ids, updates)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {count} users with {updates}')
        )

    def cleanup_inactive_users(self, options):
        """Clean up inactive users"""
        days = options.get('days', 365)
        
        self.stdout.write(f'Cleaning up users inactive for more than {days} days...')
        count = user_manager.cleanup_inactive_users(days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deactivated {count} inactive users')
        )

    def export_users(self, options):
        """Export user data"""
        user_ids = options.get('user_ids')
        output_file = options.get('output_file')
        format_type = options.get('format', 'csv')
        
        if not user_ids:
            # Export all users if no specific IDs provided
            user_ids = list(User.objects.values_list('id', flat=True))
        
        if not output_file:
            output_file = f'users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.{format_type}'
        
        export_data = user_manager.export_user_data(user_ids, format_type)
        
        # Write to file
        if format_type == 'csv':
            self.write_csv_export(export_data['data'], output_file)
        elif format_type == 'json':
            self.write_json_export(export_data, output_file)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported {export_data["count"]} users to {output_file}')
        )

    def write_csv_export(self, data, filename):
        """Write data to CSV file"""
        if not data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                # Convert complex fields to strings
                processed_row = {}
                for key, value in row.items():
                    if isinstance(value, (list, dict)):
                        processed_row[key] = json.dumps(value)
                    else:
                        processed_row[key] = value
                writer.writerow(processed_row)

    def write_json_export(self, data, filename):
        """Write data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str)

    def send_notification(self, options):
        """Send bulk notification"""
        user_ids = options.get('user_ids')
        subject = options.get('subject')
        message = options.get('message')
        notification_type = options.get('notification_type', 'email')
        
        if not user_ids:
            raise CommandError('--user-ids is required for send_notification operation')
        if not subject:
            raise CommandError('--subject is required for send_notification operation')
        if not message:
            raise CommandError('--message is required for send_notification operation')
        
        count = user_manager.send_bulk_notification(
            user_ids, subject, message, notification_type
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {notification_type} notifications to {count} users')
        )