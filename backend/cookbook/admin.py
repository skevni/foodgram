from django import forms
from django.contrib import admin
from django.contrib.admin.decorators import register
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)

admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


@register(User)
class MyUserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email', 'first_name', 'last_name')


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')


@register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit')


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.image:
            self.fields['image'].help_text = mark_safe(
                '<br>' + format_html(
                    '<img src="{}" style="max-height: 100px; max-width: 100px;'
                    ' border-radius: 8px; border: 1px solid #ddd; margin-top: '
                    ' 10px;" />',
                    self.instance.image.url
                )
            )


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'text', 'author', 'pub_date',
                    'image_preview',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'author', 'pub_date')
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" '
                '/>',
                obj.image.url
            )
        return 'Изображение не загружено'

    image_preview.short_description = 'Фото'


@register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')


@register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe_name')
    list_filter = ('user', 'recipe')
