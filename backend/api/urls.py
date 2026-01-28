from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, RecipeUserViewSet, TagViewSet

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewSet, basename="tags")
router.register('users', RecipeUserViewSet, basename="users")
router.register('recipes', RecipeViewSet, basename="recipes")

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),  # Работа с токенами
    path("", include(router.urls)),
]
