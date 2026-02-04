from django.contrib import admin
from django.contrib.admin.decorators import register
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)

admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


@register(User)
class AdminUser(UserAdmin):
    list_display = (
        'pk', 'username', 'email', 'fullname', 'avatar_preview',
        'recipe_count', 'subscription_count', 'follower_count'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        (
            'Аватар', {'fields': ('avatar',)}
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('recipes')

    def get_list_filter(self, request):
        return [HasRecipesFilter, HasSubscriptionsFilter, HasFollowersFilter]

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

    @admin.display(description='Рецепты')
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписки')
    def subscription_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def follower_count(self, user):
        return user.authors.count()


class BaseHasFilter(admin.SimpleListFilter):
    filter_field = None
    filter_title = None
    filter_param = None

    def __init__(self, request, params, model, model_admin):
        if (
            not self.filter_field or not self.filter_title
            or not self.filter_param
        ):
            raise ValueError(
                'filter_field, filter_title и filter_param '
                'должны быть определены в подклассе BaseHasFilter'
            )
        self.title = f'Есть {self.filter_title}'
        self.parameter_name = f'has_{self.filter_param}'
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        yes_count = queryset.filter(
            **{f'{self.filter_field}__isnull': False}
        ).distinct().count()
        no_count = queryset.filter(
            **{f'{self.filter_field}__isnull': True}
        ).count()

        return [
            ('yes', f'Есть ({yes_count})'),
            ('no', f'Нет ({no_count})'),
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


@register(Tag)
class TagAdmin(CountMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug') + CountMixin.list_display
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')


@register(Ingredient)
class IngredientAdmin(CountMixin, admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'measurement_unit'
    ) + CountMixin.list_display
    search_fields = ('name',)
    list_filter = ('name', HasInRecipesFilter)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_range'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        times = list(queryset.values_list(
            'cooking_time', flat=True).order_by('cooking_time')
        )
        total = len(times)
        if total == 0:
            return [
                ('0', 'Нет данных'),
            ]

        # Определяем два порога: делим на три примерно равные группы
        idx1 = total // 3
        idx2 = 2 * total // 3

        t1 = times[idx1] if idx1 < total else times[-1]
        t2 = times[idx2] if idx2 < total else times[-1]

        # Считаем количество в каждом диапазоне
        count1 = queryset.filter(cooking_time__lte=t1).count()
        count2 = queryset.filter(
            cooking_time__gt=t1, cooking_time__lte=t2
        ).count()
        count3 = queryset.filter(cooking_time__gt=t2).count()

        # Формируем подписи
        return [
            (f'0:{t1}', f'до {t1} мин ({count1})'),
            (f'{t1 + 1}:{t2}', f'{t1 + 1}–{t2} мин ({count2})'),
            (f'{t2 + 1}:inf', f'больше {t2} мин ({count3})'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            try:
                value = self.value()
                if ':' in value:
                    start, end = value.split(':')
                    start = int(start)
                    if end == 'inf':
                        return queryset.filter(cooking_time__gt=start)
                    else:
                        end = int(end)
                        return queryset.filter(
                            cooking_time__gte=start, cooking_time__lte=end
                        )
            except Exception:
                return queryset
        return queryset


class AuthorTagBaseCountFilter(admin.SimpleListFilter):
    """
    Базовый фильтр для моделей, связанных с Recipe.
    Ожидает, что подкласс определит:
        - model: связная модель (например, User, Tag)
        - recipe_field: поле модели, через которое она связана с Recipe
        - title: название фильтра
    """
    model = None
    recipe_field = None

    def lookups(self, request, model_admin):
        if not self.model or not self.recipe_field:
            raise ValueError(
                'Модель и recipe_field должны быть заданы в '
                f'{self.__class__.__name__}'
            )

        qs = model_admin.get_queryset(request)

        related_objects = (
            self.model.objects
            .filter(**{'recipes__in': qs})
            .annotate(recipe_count=Count('recipes', distinct=True))
            .order_by('-recipe_count')
        )

        return [
            (obj.pk, f'{obj} ({obj.recipe_count})')
            for obj in related_objects
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                **{f'{self.recipe_field}__pk': self.value()}
            )
        return queryset


class AuthorFilter(AuthorTagBaseCountFilter):
    title = 'Автор'
    parameter_name = 'author'
    model = User
    recipe_field = 'author'


class TagFilter(AuthorTagBaseCountFilter):
    title = 'Тег'
    parameter_name = 'tag'
    model = Tag
    recipe_field = 'tags'


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'cooking_time', 'author', 'favorites_count',
        'ingredients_list', 'tags_list', 'image_preview'
    )
    search_fields = (
        'name', 'author__username', 'tags__name', 'ingredients__name'
    )
    list_filter = (TagFilter, AuthorFilter, CookingTimeFilter)
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Ингредиенты')
    @mark_safe
    def ingredients_list(self, recipe):
        ingredients = [
            f'{item.ingredient.name} ({item.ingredient.measurement_unit}) — '
            f'{item.amount}'
            for item in recipe.recipe_ingredients.all()
        ]
        return '<br>'.join(ingredients) if ingredients else 'Нет ингредиентов'

    @admin.display(description='Теги')
    @mark_safe
    def tags_list(self, recipe):
        tags = [
            f'<span padding: 4px 8px; border-radius: 12px; color: white; '
            f'margin-right: 4px;">{tag.name}</span>'
            for tag in recipe.tags.all()
        ]
        return ''.join(tags) if tags else 'Нет тегов'

    @admin.display(description='Изображение')
    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return (f'<img src="{recipe.image.url}" style="max-height: 100px; '
                    'max-width: 100px; border-radius: 8px;" />')
        return 'Изображение не загружено'


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
