from django.contrib.auth import get_user_model
from django.db import models
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from cookbook.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                             ShoppingCart, Subscription, Tag)
from .filters import IngredientFilter, RecipeFilter
from .pagination import UsersPagination
from .permissions import IsAuthorOrReadOnly
from .serializer import (AvatarSerializer, IngredientSerializer,
                         RecipeProfileSerializer, RecipeSerializer,
                         RecipeWriteSerializer, TagSerializer,
                         UserReadSerializer, UserRecipeSerializer)

User = get_user_model()


class RecipeUserViewSet(UserViewSet):
    """Вьюсет пользователей и подписок."""

    queryset = User.objects.all()
    serializer_class = UserReadSerializer
    pagination_class = UsersPagination
    permission_classes = (IsAuthorOrReadOnly,)

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
        if request.method != 'POST':
            get_object_or_404(
                Subscription, user=request.user, author__id=pk
            ).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        user = request.user
        author = get_object_or_404(User, pk=pk)
        if author == user:
            return ValidationError(
                {'detail': 'Нельзя подписаться на самого себя!'}
            )
        _, created = Subscription.objects.get_or_create(
            user=user, author=author
        )
        if not created:
            return ValidationError(
                f'Вы уже подписаны на пользователя '
                f'{author.username}'
            )
        return Response(
            self.get_serializer(author, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False, methods=['put', 'delete'], url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request, *args, **kwargs):
        """Добавление или удаление аватара текущего пользователя."""
        if request.method != 'PUT':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = AvatarSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


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


class RecipeViewSet(ModelViewSet):
    """Вьюсет для операций с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = UsersPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """Создание рецепта с текущим автором."""

        serializer.save(author=self.request.user)

    def handle_add_or_remove(self, model, request, pk):
        user = request.user

        if request.method == 'DELETE':
            get_object_or_404(model, user=user, recipe_id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(
            user=user, recipe_id=pk
        )
        if not created:
            raise ValidationError(
                f'{recipe.name} уже есть в '
                f'{model._meta.verbose_name.lower()}!'
            )
        return Response(
            RecipeProfileSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True, methods=['post', 'delete'], url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self.handle_add_or_remove(
            ShoppingCart,
            request,
            pk
        )

    @action(
        detail=True, methods=['post', 'delete'], url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self.handle_add_or_remove(
            Favorite,
            request,
            pk
        )

    @action(
        detail=True, methods=['get'], url_path='get-link',
    )
    def get_short_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""

        if not self.queryset.filter(pk=pk).exists():
            raise NotFound(f'Рецепт id={pk} не найден!')
        return Response({'short-link': request.build_absolute_uri(
            reverse('recipe-short-link', args=[pk])
        )})

    @action(
        detail=False, methods=['get'], url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(
            shoppingcarts__user=user
        )
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=models.Sum('amount')
        ).order_by('ingredient__name')
        current_time = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = (f'shopping_list_{user.id}_{current_time}.html')
        return FileResponse(
            render_to_string(
                'shopping_list_template.html',
                {
                    'recipes': recipes,
                    'total_ingredients': list(ingredients),
                    'date': timezone.now().strftime('%d.%m.%Y')
                }
            ),
            as_attachment=True,
            filename=file_name
        )


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None
    serializer_class = IngredientSerializer
