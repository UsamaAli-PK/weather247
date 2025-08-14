from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, UserActivity, UserRole, UserAPIUsage


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone_number')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    permissions_summary = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'is_active', 'is_staff', 'is_superuser', 'is_verified',
            'date_joined', 'last_login', 'last_activity', 'login_count',
            'preferred_units', 'timezone', 'language', 'api_requests_count',
            'api_rate_limit', 'profile', 'permissions_summary'
        )
        read_only_fields = (
            'id', 'date_joined', 'last_login', 'last_activity', 'login_count',
            'api_requests_count', 'is_verified'
        )

    def get_permissions_summary(self, obj):
        """Get user permissions summary"""
        from .utils import get_user_permissions_summary
        return get_user_permissions_summary(obj)


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activities"""
    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ('user', 'timestamp')


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for user roles"""
    permissions_count = serializers.SerializerMethodField()

    class Meta:
        model = UserRole
        fields = '__all__'

    def get_permissions_count(self, obj):
        return obj.permissions.count()


class UserAPIUsageSerializer(serializers.ModelSerializer):
    """Serializer for API usage tracking"""
    class Meta:
        model = UserAPIUsage
        fields = '__all__'
        read_only_fields = ('user', 'date')


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class BulkUserOperationSerializer(serializers.Serializer):
    """Serializer for bulk user operations"""
    operation = serializers.ChoiceField(choices=['activate', 'deactivate', 'delete'])
    user_ids = serializers.ListField(child=serializers.IntegerField())

    def validate_user_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one user ID is required")
        return value


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    api_requests_today = serializers.IntegerField()

