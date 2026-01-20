from django.conf.urls.static import static
from django.urls import include, path

from backend import settings
# from rest_framework.routers import DefaultRouter

# from backend.backend import settings

# from . import views

app_name = 'api'

urlpatterns = [
    path('', include('djoser.urls')),  # Работа с пользователями
    path('auth/', include('djoser.urls.authtoken')),  # Работа с токенами
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
