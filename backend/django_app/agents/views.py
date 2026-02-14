from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import AgentConfiguration, ConversationSession, ConversationLog
from .serializers import (
    AgentConfigurationSerializer,
    ConversationSessionSerializer,
    ConversationLogSerializer
)


class AgentConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI agent configurations
    
    Endpoints:
    - GET /api/agents/ - List user's agents
    - POST /api/agents/ - Create new agent
    - GET /api/agents/{id}/ - Get agent details
    - PUT/PATCH /api/agents/{id}/ - Update agent
    - DELETE /api/agents/{id}/ - Delete agent
    """
    
    serializer_class = AgentConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return agents owned by current user"""
        return AgentConfiguration.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user to current authenticated user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Start a new conversation session for this agent"""
        agent = self.get_object()
        
        session = ConversationSession.objects.create(
            agent=agent,
            user=request.user,
            status='active'
        )
        
        serializer = ConversationSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConversationSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversation sessions
    
    Endpoints:
    - GET /api/agents/sessions/ - List user's sessions
    - POST /api/agents/sessions/ - Create new session
    - GET /api/agents/sessions/{id}/ - Get session details
    - PATCH /api/agents/sessions/{id}/ - Update session (e.g., end session)
    - POST /api/agents/sessions/{id}/end_session/ - End a session
    - GET /api/agents/sessions/{id}/logs/ - Get session logs
    """
    
    serializer_class = ConversationSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return sessions for current user"""
        return ConversationSession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user to current authenticated user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End an active session"""
        session = self.get_object()
        session.status = 'ended'
        session.ended_at = timezone.now()
        session.save()
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get conversation logs for this session"""
        session = self.get_object()
        logs = ConversationLog.objects.filter(session=session)
        serializer = ConversationLogSerializer(logs, many=True)
        return Response(serializer.data)


class ConversationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for conversation logs
    
    Endpoints:
    - GET /api/logs/ - List logs (filtered by user's sessions)
    - GET /api/logs/{id}/ - Get specific log
    """
    
    serializer_class = ConversationLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return logs from user's sessions only"""
        user_sessions = ConversationSession.objects.filter(user=self.request.user)
        return ConversationLog.objects.filter(session__in=user_sessions)
