from django_filters import (BooleanFilter, CharFilter, FilterSet,
                            ModelMultipleChoiceFilter, NumberFilter)
from django_filters.widgets import BooleanWidget

from cookbook.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(
        widget=BooleanWidget(), method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(
        widget=BooleanWidget(), method='filter_in_shopping_cart')
    author = NumberFilter(field_name='author__id')
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug', to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'tags', 'author', 'is_in_shopping_cart')

    def filter_is_favorited(self, recipes, name, value):
        user = self.request.user
        if not user or user.is_anonymous:
            return recipes
        if value:
            return recipes.filter(favorites__user=user)
        return recipes.exclude(favorites__user=user)

    def filter_in_shopping_cart(self, recipes, name, value):
        user = self.request.user
        if not user or user.is_anonymous:
            return recipes
        if value:
            return recipes.filter(shoppingcarts__user=user)
        return recipes.exclude(shoppingcarts__user=user)


class IngredientFilter(FilterSet):
    name = CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
