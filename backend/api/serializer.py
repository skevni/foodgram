from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from cookbook.constants import MIN_COOKING_TIME, MIN_INGREDIENTS_AMOUNT
from cookbook.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Subscription,
    Tag
)

User = get_user_model()


class TagSerializer(ModelSerializer):
    """Сериализатор для вывода тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(ModelSerializer):
    """Сериализатор для вывода ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserReadSerializer(UserSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (*UserSerializer.Meta.fields, 'avatar', 'is_subscribed')
        read_only_fields = fields

    def get_is_subscribed(self, author):
        """Метод проверки подписки"""

        user = self.context.get('request').user

        return not user.is_anonymous and Subscription.objects.filter(
            user=user, author=author
        ).exists()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True)
    author = UserReadSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time'
                  )
        read_only_fields = fields

    def user_relation(self, recipe, model):
        request = self.context['request']

        return (
            request is not None
            and not request.user.is_anonymous
            and model.objects.filter(user=request.user, recipe=recipe).exists()
        )

    def get_is_favorited(self, obj):
        """Метод проверки наличия в избранном."""

        return self.user_relation(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Метод проверки наличия в корзине."""

        return self.user_relation(obj, ShoppingCart)


class IngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для ингредиентов в рецептах"""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_INGREDIENTS_AMOUNT)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""

    ingredients = IngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(allow_null=True)
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'name',
                  'image', 'text', 'cooking_time')

    def to_representation(self, instance):
        """Метод представления модели"""

        return RecipeSerializer(instance, context=self.context).data

    def create_ingredients(self, recipe, ingredients):
        """Метод создания ингредиента"""

        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    def create_tags(self, tags, recipe):
        """Метод добавления тега"""

        recipe.tags.set(tags)

    def create(self, validated_data):
        """Метод создания модели"""

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления модели"""

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(recipe=instance, ingredients=ingredients_data)

        return super().update(instance, validated_data)


class RecipeProfileSerializer(serializers.ModelSerializer):
    """Дополнительный сериализатор для рецептов в профиле. """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserRecipeSerializer(UserSerializer):
    """Сериализатор для модели User, его подписок и рецептов."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(
        read_only=True, source='recipes.count'
    )

    class Meta(UserSerializer.Meta):
        model = User
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, author):
        """Метод для получения рецептов."""

        request = self.context.get('request')
        recipes = author.recipes.all()
        recipes_limit = request.GET.get(
            'recipes_limit', 10**10
        )

        return RecipeProfileSerializer(
            recipes[:int(recipes_limit)],
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, user):
        """Метод для получения количества рецептов."""
        return user.recipes.count()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор добавления или удаления аватара."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ['avatar', ]
