from django.contrib import admin
from django.contrib.admin.decorators import register
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
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
        # Без этой строки будет ошибка.
        super().__init__(request, params, model, model_admin)

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
    parameter_name = 'cooking_time'

    @staticmethod
    def get_time_ranges(short_limit, medium_limit):
        """
        Возвращает диапазоны фильтрации по времени с текстовыми описаниями.
        Можно использовать в lookups() и queryset().
        """
        return {
            'short': {
                'lookup': {'cooking_time__range': (1, short_limit)},
                'verbose_name': f'до {short_limit} мин',
            },
            'medium': {
                'lookup': {
                    'cooking_time__range': (short_limit + 1, medium_limit)
                },
                'verbose_name': f'{short_limit + 1} – {medium_limit} мин',
            },
            'long': {
                'lookup': {'cooking_time__gt': medium_limit},
                'verbose_name': f'больше {medium_limit} мин',
            }
        }

    def _get_limits(self, recipes):
        """Вычисляет границы."""
        times = sorted(set(cook_time for cook_time in recipes.values_list(
            'cooking_time', flat=True) if cook_time is not None)
        )
        total = len(times)
        if total >= 3:
            return times[total // 3], times[2 * total // 3]
        return (None, None)

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        short_limit, medium_limit = self._get_limits(recipes)
        if short_limit is None or medium_limit is None:
            return []

        return [
            (
                key,
                f'{config["verbose_name"]} '
                f'({recipes.filter(**config["lookup"]).count()})'
            )
            for key, config in self.get_time_ranges(
                short_limit, medium_limit
            ).items()
        ]

    def queryset(self, request, recipes):
        if self.value() not in ['short', 'medium', 'long']:
            return recipes

        short_limit, medium_limit = self._get_limits(recipes)
        time_ranges = self.get_time_ranges(short_limit, medium_limit)

        return recipes.filter(**time_ranges[self.value]['lookup'])


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'cooking_time', 'author', 'favorites_count',
        'ingredients_list', 'tags_list', 'image_preview'
    )
    search_fields = (
        'name', 'author__username', 'tags__name', 'ingredients__name'
    )
    list_filter = (
        ('tags', admin.RelatedOnlyFieldListFilter),
        ('author', admin.RelatedOnlyFieldListFilter),
        CookingTimeFilter
    )
    autocomplete_fields = ('tags', 'ingredients')
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
    list_filter = (
        ('recipe', admin.RelatedOnlyFieldListFilter),
        ('ingredient', admin.RelatedOnlyFieldListFilter)
    )


@register(Favorite, ShoppingCart)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = (
        ('user', admin.RelatedOnlyFieldListFilter),
        ('recipe', admin.RelatedOnlyFieldListFilter)
    )
