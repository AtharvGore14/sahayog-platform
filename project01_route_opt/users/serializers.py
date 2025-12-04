"""
Serializers for the users app.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, CompanyProfile, DriverProfile, MunicipalAdminProfile, UserDevice


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type', 'phone_number',
            'address', 'location', 'profile_picture', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CompanyProfileSerializer(serializers.ModelSerializer):
    """Serializer for CompanyProfile model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CompanyProfile
        fields = '__all__'


class DriverProfileSerializer(serializers.ModelSerializer):
    """Serializer for DriverProfile model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DriverProfile
        fields = '__all__'


class MunicipalAdminProfileSerializer(serializers.ModelSerializer):
    """Serializer for MunicipalAdminProfile model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MunicipalAdminProfile
        fields = '__all__'


class UserDeviceSerializer(serializers.ModelSerializer):
    """Serializer for UserDevice model."""
    
    class Meta:
        model = UserDevice
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password.')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with related data."""
    company_profile = CompanyProfileSerializer(read_only=True)
    driver_profile = DriverProfileSerializer(read_only=True)
    admin_profile = MunicipalAdminProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone_number', 'address', 'location',
            'profile_picture', 'is_verified', 'created_at', 'updated_at',
            'company_profile', 'driver_profile', 'admin_profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
