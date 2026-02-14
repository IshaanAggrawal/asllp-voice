from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AgentConfiguration, ConversationSession, ConversationLog
from authentication.serializers import UserRegistrationSerializer, UserDetailSerializer


class AgentConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for AI agent configuration"""
    
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = AgentConfiguration
        fields = [
            'id',
            'user',
            'name',
            'system_prompt',
            'conversation_model',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_system_prompt(self, value):
        """Ensure system prompt is not empty"""
        if not value.strip():
            raise serializers.ValidationError("System prompt cannot be empty")
        return value


class ConversationSessionSerializer(serializers.ModelSerializer):
    """Serializer for conversation sessions"""
    
    agent_name = serializers.ReadOnlyField(source='agent.name')
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = ConversationSession
        fields = [
            'id',
            'agent',
            'agent_name',
            'user',
            'status',
            'started_at',
            'ended_at',
            'total_turns',
            'average_latency_ms'
        ]
        read_only_fields = ['id', 'user', 'started_at', 'total_turns', 'average_latency_ms']


class ConversationLogSerializer(serializers.ModelSerializer):
    """Serializer for conversation logs"""
    
    class Meta:
        model = ConversationLog
        fields = [
            'id',
            'session',
            'timestamp',
            'speaker',
            'transcript',
            'intent',
            'latency_ms'
        ]
        read_only_fields = ['id', 'timestamp']
