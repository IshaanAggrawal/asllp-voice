from django.db import models
from django.contrib.auth.models import User
import uuid


class AgentConfiguration(models.Model):
    """Custom AI agent definition created by users"""
    
    CONVERSATION_MODEL_CHOICES = [
        ('llama3.2:1b', 'LLaMA 3.2 1B (Ollama)'),
        ('qwen2.5:1.5b', 'Qwen 2.5 1.5B (Ollama)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agents')
    name = models.CharField(max_length=255, help_text="Agent display name")
    system_prompt = models.TextField(help_text="System prompt defining agent personality and behavior")
    conversation_model = models.CharField(
        max_length=50,
        choices=CONVERSATION_MODEL_CHOICES,
        default='llama3.2:1b',
        help_text="Model to use for conversation generation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Configuration'
        verbose_name_plural = 'Agent Configurations'
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"


class ConversationSession(models.Model):
    """Tracks individual voice call sessions"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(AgentConfiguration, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    total_turns = models.IntegerField(default=0, help_text="Number of conversation turns")
    average_latency_ms = models.IntegerField(null=True, blank=True, help_text="Average response latency")
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Conversation Session'
        verbose_name_plural = 'Conversation Sessions'
    
    def __str__(self):
        return f"Session {self.id} - {self.agent.name}"


class ConversationLog(models.Model):
    """Optional: Logs individual conversation turns for analytics"""
    
    SPEAKER_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    speaker = models.CharField(max_length=10, choices=SPEAKER_CHOICES)
    transcript = models.TextField()
    intent = models.CharField(max_length=100, null=True, blank=True, help_text="Classified intent by orchestrator")
    latency_ms = models.IntegerField(null=True, blank=True, help_text="Processing latency in milliseconds")
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Conversation Log'
        verbose_name_plural = 'Conversation Logs'
    
    def __str__(self):
        return f"{self.speaker} at {self.timestamp}"
