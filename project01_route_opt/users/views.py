"""
Views for the users app.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from .models import User, CompanyProfile, DriverProfile, MunicipalAdminProfile, UserDevice
from .serializers import (
    UserSerializer, CompanyProfileSerializer, DriverProfileSerializer,
    MunicipalAdminProfileSerializer, UserDeviceSerializer, LoginSerializer,
    UserProfileSerializer, PasswordChangeSerializer
)


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserLoginView(APIView):
    """User login endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserProfileSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """User logout endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view and update endpoint."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class CompanyProfileView(generics.RetrieveUpdateAPIView):
    """Company profile view and update endpoint."""
    serializer_class = CompanyProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(CompanyProfile, user=self.request.user)


class DriverProfileView(generics.RetrieveUpdateAPIView):
    """Driver profile view and update endpoint."""
    serializer_class = DriverProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(DriverProfile, user=self.request.user)


class MunicipalAdminProfileView(generics.RetrieveUpdateAPIView):
    """Municipal admin profile view and update endpoint."""
    serializer_class = MunicipalAdminProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(MunicipalAdminProfile, user=self.request.user)


class UserDeviceView(generics.CreateAPIView):
    """Register user device for push notifications."""
    serializer_class = UserDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PasswordChangeView(APIView):
    """Change user password endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password changed successfully'})
            else:
                return Response(
                    {'error': 'Invalid old password'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics."""
    user = request.user
    stats = {
        'user_type': user.user_type,
        'is_verified': user.is_verified,
        'created_at': user.created_at,
        'last_login': user.last_login,
    }
    
    # Add profile-specific stats
    if hasattr(user, 'company_profile'):
        stats['company_info'] = {
            'company_name': user.company_profile.company_name,
            'business_type': user.company_profile.business_type,
        }
    elif hasattr(user, 'driver_profile'):
        stats['driver_info'] = {
            'employee_id': user.driver_profile.employee_id,
            'vehicle_number': user.driver_profile.vehicle_number,
            'assigned_zone': user.driver_profile.assigned_zone,
        }
    elif hasattr(user, 'admin_profile'):
        stats['admin_info'] = {
            'department': user.admin_profile.department,
            'jurisdiction_area': user.admin_profile.jurisdiction_area,
        }
    
    return Response(stats)
