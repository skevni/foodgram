from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .pagination import UsersPagination
from recipes.models import Tag, Subscription
from .serializer import AvatarSerializer, TagSerializer, UserReadSerializer

User = get_user_model()


class RecipeUserViewSet(UserViewSet):
    """Вьюсет пользователей на основе Djoser."""

    queryset = User.objects.all()
    serializer_class = UserReadSerializer
    pagination_class = UsersPagination

    @action(
        detail=False, methods=['get'], url_path='subscriptions',
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        return self.get_paginated_response(UserRecipeSerializer(
            self.paginate_queryset(
                User.objects.filter(authors__user=request.user)
            ),
            context={'request': request},
            many=True
        ).data)

    @action(
        detail=True, methods=['post', 'delete'], url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user
        if request.method == 'POST':
            if author == user:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    f'Вы уже подписаны на пользователя '
                    f'{subscription.author.username}',
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = self.get_serializer(
                author, context={'request': request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=user, author=author
        ).delete()
        if not deleted:
            return Response({'detail': 'Вы не были подписаны'},
                            status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['put', 'delete'], url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request, *args, **kwargs):
        """Добавление или удаление аватара текущего пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для отображения тегов.

    Предоставляет эндпоинт для получения списка тегов.
    Пагинация отключена, так как тегов обычно небольшое количество.
    Доступен поиск по названию тега (поле 'name').
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('name',)
    pagination_class = None
