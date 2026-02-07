from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentConfigurationViewSet, ConversationSessionViewSet, ConversationLogViewSet

router = DefaultRouter()
router.register(r'', AgentConfigurationViewSet, basename='agent')
router.register(r'sessions', ConversationSessionViewSet, basename='session')
router.register(r'logs', ConversationLogViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
]
