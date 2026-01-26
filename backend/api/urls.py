from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'

router = DefaultRouter()

router.register('tags/', views.TagViewSet, basename="tags")
router.register('users', views.UserViewSet, basename="users")
# router.register('tags', views.TagViewSet, basename="tags")

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),  # Работа с токенами
    path("", include(router.urls)),
]
