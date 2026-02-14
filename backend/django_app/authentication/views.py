from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserDetailSerializer
from datetime import timedelta


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user with enhanced validation"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'success': True,
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and set JWT tokens in HTTP-only cookies
    Also returns tokens in response body for compatibility
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'success': False,
            'message': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({
            'success': False,
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    # Create response
    response = Response({
        'success': True,
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    }, status=status.HTTP_200_OK)
    
    # Set HTTP-only cookies (secure in production)
    # Access token - 1 day
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=86400,  # 1 day in seconds
        httponly=True,  # Prevents JavaScript access
        secure=False,   # Set to True in production (HTTPS)
        samesite='Lax'  # CSRF protection
    )
    
    # Refresh token - 7 days
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=604800,  # 7 days in seconds
        httponly=True,
        secure=False,   # Set to True in production
        samesite='Lax'
    )
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user details"""
    serializer = UserDetailSerializer(request.user)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user and clear JWT cookies
    """
    response = Response({
        'success': True,
        'message': 'Logged out successfully. Cookies cleared.'
    }, status=status.HTTP_200_OK)
    
    # Delete cookies by setting them to expire immediately
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    return response

