from django.contrib import admin
from .models import AgentConfiguration, ConversationSession, ConversationLog


@admin.register(AgentConfiguration)
class AgentConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'conversation_model', 'created_at']
    list_filter = ['conversation_model', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent', 'user', 'status', 'started_at', 'total_turns']
    list_filter = ['status', 'started_at']
    search_fields = ['agent__name', 'user__username']
    readonly_fields = ['id', 'started_at', 'ended_at']


@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display = ['session', 'speaker', 'timestamp', 'latency_ms']
    list_filter = ['speaker', 'timestamp']
    search_fields = ['transcript', 'intent']
    readonly_fields = ['id', 'timestamp']
