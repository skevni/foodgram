import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from cookbook.constants import MIN_COOKING_TIME
from cookbook.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Кодирование изображения в base64."""

    def to_internal_value(self, data):
        """Метод преобразования картинки"""

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='photo.' + ext)

        return super().to_internal_value(data)


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


class UserReadSerializer(UserCreateSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        """Метод проверки подписки"""

        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj.id).exists()


class CustomCreateUserSerializer(UserReadSerializer):
    """Сериализатор для создания пользователя
    без проверки на подписку """

    class Meta(UserReadSerializer.Meta):
        """Мета-параметры сериализатора"""

        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


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

    def user_model(self, recipe, model):
        request = self.context['request']

        return (
            request is not None
            and not request.user.is_anonymous
            and model.objects.filter(user=request.user, recipe=recipe).exists()
        )

    def get_is_favorited(self, obj):
        """Метод проверки наличия в избранном."""

        return self.user_model(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Метод проверки наличия в корзине."""

        return self.user_model(obj, ShoppingCart)


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах"""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')

    @staticmethod
    def validate_amount(value):
        """Метод валидации количества"""

        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0!'
            )
        return value

    def validate_id(self, value):
        if not Ingredient.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f'Ингредиент с id {value} не найден.'
            )
        return value


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""

    ingredients = IngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(use_url=True)
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
                ingredient_id=ingredient['id'],
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

        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)

        existing_ingredients = {ri.ingredient_id: ri
                                for ri in instance.recipe_ingredients.all()}
        ingredient_ids = [item['id'] for item in ingredients_data]

        # Удаляем ингредиенты, которых нет в запросе
        for ingredient_id, recipe_ingredient in existing_ingredients.items():
            if ingredient_id not in ingredient_ids:
                recipe_ingredient.delete()

        # Создаем или обновляем ингредиенты
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']

            if ingredient_id in existing_ingredients:
                # Обновляем существующий ингредиент
                existing_ingredients[ingredient_id].amount = amount
                existing_ingredients[ingredient_id].save()
            else:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_id,
                    amount=amount
                )

        return instance


class RecipeAdditionalSerializer(serializers.ModelSerializer):
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
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeAdditionalSerializer(
            recipes, many=True, context={'request': request}
        ).data


class AddFavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в избранное по модели Recipe."""
    image = Base64ImageField()

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор добавления или удаления аватара."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ['avatar', ]
