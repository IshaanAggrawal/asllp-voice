from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AgentConfiguration, ConversationSession, ConversationLog


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


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, data):
        """Check that passwords match"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user
