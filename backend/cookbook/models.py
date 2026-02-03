from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db import models
from django.forms import ValidationError

from .constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_INGREDIENT_NAME,
    MAX_LENGTH_LAST_NAME,
    MAX_LENGTH_MEASUREMENT,
    MAX_LENGTH_RECIPE_NAME,
    MAX_LENGTH_SLUG,
    MAX_LENGTH_TAG,
    MAX_LENGTH_USERNAME,
)
from .validators import validate_slug, validate_username


class User(AbstractUser):
    """
    Кастомная модель пользователя с логином по email.
    """
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
        'Аватар',
        upload_to='users/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:50] if self.username else self.email


class UserRecipeRelationModel(models.Model):
    """
    Абстрактная модель для связей пользователь-рецепт (избранное, корзина и
    т.д.).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        ordering = ('-recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(app_label)s_%(class)s_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} — {self.recipe.name}'


class Tag(models.Model):
    """Тег для рецептов."""
    name = models.CharField('Название тега',
                            max_length=MAX_LENGTH_TAG,
                            unique=True)
    slug = models.SlugField(
        'Идентификатор',
        max_length=MAX_LENGTH_SLUG,
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
    name = models.CharField('Название ингредиента',
                            max_length=MAX_LENGTH_INGREDIENT_NAME)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=MAX_LENGTH_MEASUREMENT)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Рецепт, созданный пользователем."""
    name = models.CharField('Название', max_length=MAX_LENGTH_RECIPE_NAME)
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/',
        blank=True,
        null=True,
    )
    text = models.TextField('Описание')
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
        'Время приготовления, мин', default=1)

    class Meta:
        default_related_name = 'recipes'
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
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.DecimalField(
        'Количество',
        max_digits=10,
        decimal_places=2,
        default=1,
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        default_related_name = 'recipe_ingredients'
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


class Favorite(UserRecipeRelationModel):
    """Избранное — рецепт, сохранённый пользователем."""
    class Meta(UserRecipeRelationModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelationModel):
    """Список покупок — рецепт, добавленный в корзину."""
    class Meta(UserRecipeRelationModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Subscription(models.Model):
    """Подписка пользователя на автора."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='followers',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author_subscription'
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def save(self, *args, **kwargs):
        self.full_clean()  # Гарантирует вызов clean() при сохранении
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} подписан на {self.author}.'
