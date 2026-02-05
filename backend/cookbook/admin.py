from typing import Any
from django.contrib import admin
from django.contrib.admin.decorators import register
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.db.models.base import Model
from django.http import HttpRequest
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)

admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


class BaseHasFilter(admin.SimpleListFilter):
    filter_field = None
    filter_title = None
    filter_param = None

    def __init__(self, request, params, model, model_admin):
        self.title = f'Есть {self.filter_title}'
        self.parameter_name = f'has_{self.filter_param}'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Есть'),
            ('no', 'Нет'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                **{f'{self.filter_field}__isnull': False}
            ).distinct()
        if self.value() == 'no':
            return queryset.filter(**{f'{self.filter_field}__isnull': True})
        return queryset


class HasRecipesFilter(BaseHasFilter):
    filter_field = 'recipes'
    filter_title = 'рецепты'
    filter_param = 'recipes'


class HasSubscriptionsFilter(BaseHasFilter):
    filter_field = 'subscriptions'
    filter_title = 'подписки'
    filter_param = 'subscriptions'


class HasFollowersFilter(BaseHasFilter):
    filter_field = 'authors'
    filter_title = 'подписчики'
    filter_param = 'followers'


class HasInRecipesFilter(BaseHasFilter):
    filter_field = 'recipe_ingredients'
    filter_title = 'в рецептах'
    filter_param = 'in_recipes'


class CountMixin:
    """
    Общий класс отображения количества рецептов, тегов или продуктов
    в списке объектов.
    """
    list_display = ('recipe_count', )

    @admin.display(description='Рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()


@register(User)
class AdminUser(CountMixin, UserAdmin):
    list_display = (
        'pk', 'username', 'email', 'fullname', 'avatar_preview',
        'recipe_count', 'subscription_count', 'follower_count',
        *CountMixin.list_display
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Аватар', {'fields': ('avatar',)}
        ),
    )
    list_filter = (
        HasRecipesFilter, HasSubscriptionsFilter, HasFollowersFilter
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('recipes')

    @admin.display(description='ФИО')
    def fullname(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_preview(self, user):
        if user.avatar:
            return (f'<img src="{user.avatar.url}" style="max-height: 100px; '
                    'max-width: 100px; border-radius: 8px; border: 1px solid '
                    '#ddd; margin-top: 10px;" />'
                    )
        return 'Аватар не загружен'

    @admin.display(description='Подписки')
    def subscription_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def follower_count(self, user):
        return user.authors.count()

@register(Tag)
class TagAdmin(CountMixin, admin.ModelAdmin):
    list_display = (*CountMixin.list_display, 'pk', 'name', 'slug')
    search_fields = ('name', 'slug')


@register(Ingredient)
class IngredientAdmin(CountMixin, admin.ModelAdmin):
    list_display = (
        *CountMixin.list_display, 'pk', 'name', 'measurement_unit'
    )
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit', HasInRecipesFilter)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_range'

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.short_limit = None
        self.medium_limit = None
        self.time_range = {
            'short': {'cooking_time__range': (0, self.short_limit)},
            'medium': {
                'cooking_time__range': (
                    self.short_limit + 1, self.medium_limit
                )
            },
            'long': {'cooking_time__gt': self.medium_limit},
        }

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        times = sorted(set(queryset.values_list('cooking_time', flat=True)))
        total = len(times)

        # Требуется минимум 3 уникальных значения
        if total < 3:
            return None

        self.short_limit = times[total // 3]
        self.medium_limit = times[2 * total // 3]

        # Подсчитываем количество
        count1 = queryset.filter(cooking_time__lte=self.short_limit).count()
        count2 = queryset.filter(
            cooking_time__gt=self.short_limit,
            cooking_time__lte=self.medium_limit
        ).count()
        count3 = queryset.filter(cooking_time__gt=self.medium_limit).count()

        return [
            ('short', f'до {self.short_limit} мин ({count1})'),
            (
                'medium', (
                    f'{self.short_limit + 1}–{self.medium_limit} '
                    f'мин ({count2})'
                )
            ),
            ('long', f'больше {self.medium_limit} мин ({count3})'),
        ]

    def queryset(self, request, recipes):
        if self.value() in self.time_range:
            return recipes.filter(self.time_range[self.value()])

        return recipes


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'cooking_time', 'author', 'favorites_count',
        'ingredients_list', 'tags_list', 'image_preview'
    )
    search_fields = (
        'name', 'author__username', 'tags__name', 'ingredients__name'
    )
    list_filter = ('tags', 'authors', CookingTimeFilter)
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Ингредиенты')
    @mark_safe
    def ingredients_list(self, recipe):
        return '<br>'.join(
            f'{item.ingredient.name} ({item.ingredient.measurement_unit}) — '
            f'{item.amount}'
            for item in recipe.recipe_ingredients.all()
        )

    @admin.display(description='Теги')
    @mark_safe
    def tags_list(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Изображение')
    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return (f'<img src="{recipe.image.url}" style="max-height: 100px; '
                    'max-width: 100px; border-radius: 8px;" />')
        return ''


@register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')


@register(Favorite, ShoppingCart)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
