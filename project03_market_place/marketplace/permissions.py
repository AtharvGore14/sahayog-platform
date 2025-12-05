from rest_framework.permissions import BasePermission

class IsSeller(BasePermission):
    """
    Custom permission to only allow users in the 'seller' group.
    """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='seller').exists()

class IsBuyer(BasePermission):
    """
    Custom permission to only allow users in the 'buyer' group.
    """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='buyer').exists()