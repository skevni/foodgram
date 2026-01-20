from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import DecimalValidator, MinLengthValidator
from django.db import models

from .constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                        MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME)
from .validators import validate_username, validate_slug


class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователя создания пользователей
    и суперпользователей без поля `is_superuser` в форме.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Поле "email" обязательно.')
        if not username:
            raise ValueError('Поле "username" обязательно.')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)  # Хеширование пароля
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser):
    """Кастомная модель пользователя с поддержкой подписок и аватарки."""
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
        blank=True,
        validators=[MinLengthValidator(1)],
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_LAST_NAME,
        blank=True,
        validators=[MinLengthValidator(1)],
    )
    password = models.CharField('Пароль', max_length=128)
    avatar = models.URLField('Аватар', blank=True, null=True)
    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='followers',
        help_text='Пользователи, на которых подписан этот пользователь.',
    )

    is_active = models.BooleanField('Активен', default=True)
    is_staff = models.BooleanField('Администратор', default=False)
    is_superuser = models.BooleanField('Суперпользователь', default=False)
    date_joined = models.DateTimeField('Дата регистрации', auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username'],
                name='unique_username'
            ),
            models.UniqueConstraint(
                fields=['email'],
                name='unique_email'
            ),
        ]

    def __str__(self):
        return self.username[:50]

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.username

    def get_short_name(self):
        return self.first_name if self.first_name else self.username

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    # @property
    # def is_superuser(self):
    #     return self.is_superuser

    # Эти свойства можно добавить позже, если будет введено поле `role`
    # @property
    # def is_admin(self):
    #     return self.is_staff or self.is_superuser
    #
    # @property
    # def is_moderator(self):
    #     return False  # Реализовать при наличии role
    #
    # @property
    # def is_user(self):
    #     return not self.is_staff


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
    name = models.CharField('Название ингредиента', max_length=128)
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
        default=1,
        validators=[DecimalValidator(max_digits=10, decimal_places=2)],
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
        unique_together = (
            ('user', 'recipe'),
        )

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
                fields=['user', 'recipe'], name='unique_shoppingcart'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user.username} {self.recipe.name}'
