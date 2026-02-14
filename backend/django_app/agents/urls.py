from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentConfigurationViewSet, ConversationSessionViewSet, ConversationLogViewSet

# Separate routers to prevent the agent detail route (^(?P<pk>[^/.]+)/$)
# from capturing "sessions/" and "logs/" before their own routes can match.
agent_router = DefaultRouter()
agent_router.register(r'', AgentConfigurationViewSet, basename='agent')

session_router = DefaultRouter()
session_router.register(r'', ConversationSessionViewSet, basename='session')

log_router = DefaultRouter()
log_router.register(r'', ConversationLogViewSet, basename='log')

urlpatterns = [
    # These MUST come before the agent catch-all
    path('sessions/', include(session_router.urls)),
    path('logs/', include(log_router.urls)),
    path('', include(agent_router.urls)),
]
