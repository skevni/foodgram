from django.contrib.admin import ModelAdmin, register
from django.contrib.auth.admin import UserAdmin

from foodgram.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag, User
)


@register(User)
class MyUserAdmin(ModelAdmin):
    list_display = ['pk', 'username', 'email', 'first_name', 'last_name']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['username', 'email', 'first_name', 'last_name']


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['pk', 'name', 'slug']
    search_fields = ['name', 'slug']
    list_filter = ['name', 'slug']


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ['pk', 'name', 'measurement_unit']
    search_fields = ['name']
    list_filter = ['name', 'measurement_unit']


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ['pk', 'name', 'text', 'author', 'pub_date']
    search_fields = ['name']
    list_filter = ['name', 'tags', 'author']


@register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    list_display = ['pk', 'recipe', 'ingredient', 'amount']
    search_fields = ['recipe', 'ingredient']
    list_filter = ['recipe', 'ingredient']


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ['pk', 'user', 'recipe']
    search_fields = ['user', 'recipe']
    list_filter = ['user', 'recipe']


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ['pk', 'user', 'recipe']
    search_fields = ['user', 'recipe']
    list_filter = ['user', 'recipe']
