from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import DecimalValidator, MinLengthValidator
from django.db import models
from django.forms import ValidationError

from .constants import (
    MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME, MAX_LENGTH_INGRIDIENT_NAME,
    MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME)
from .validators import validate_username, validate_slug


class User(AbstractUser):
    username = models.CharField(
        'Логин',
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        help_text='Допускаются только буквы, цифры и @/./+/-/_.',
        validators=[validate_username],
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        },
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_FIRST_NAME,
        validators=[MinLengthValidator(1)],
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_LAST_NAME,
        validators=[MinLengthValidator(1)],
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True, null=True, verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'email', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:50]


User = get_user_model()


class UserRecipeRelationModel(models.Model):
    """
    Абстрактная модель.
    Добавляет поля автора и рецепта, для связывающих их моделей.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(
        'Recipe', on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s_set'
    )

    class Meta:
        abstract = True
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(app_label)s_%(model_name)s_user_recipe'
            ),
        )

    def __str__(self):
        return f'{self.user} - {self.recipe}.'


class Tag(models.Model):
    """Тег для рецептов."""
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        validators=[validate_slug],
        help_text='Уникальный слаг для URL.',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиент с единицей измерения."""
    name = models.CharField(
        'Название ингредиента',
        max_length=MAX_LENGTH_INGRIDIENT_NAME
    )
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Рецепт, созданный пользователем."""
    name = models.CharField('Название', max_length=256)
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/',
        blank=True,
        null=True,
    )
    text = models.TextField(verbose_name='Описание')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        default=1, verbose_name='Время приготовления, мин')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связь рецепта и ингредиента с количеством."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.DecimalField(
        'Количество',
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
        ordering = ('ingredient__name',)

    def __str__(self):
        return (f'{self.ingredient.name}: {self.amount} '
                f'{self.ingredient.measurement_unit}')


class Favorite(models.Model):
    """Избранное."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт')

    class Meta:        
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_ingredient'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user.username} {self.recipe.name}'


class ShoppingCart(models.Model):
    """Список покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart_user_recipe'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user.username} {self.recipe.name}'


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='followers'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author_subscription'
            ),
        )

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def __str__(self):
        return f'{self.user} подписан на {self.author}.'
