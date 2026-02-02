import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(username):
    """Функция для глобального валидатора по пользователям"""
    if username == settings.USER_PROFILE_PATH:
        raise ValidationError(
            f'Имя пользователя не может быть <{settings.USER_PROFILE_PATH}>.'
        )

    invalid_chars_match = re.sub(
        settings.USERNAME_ACCEPTABLE_SYMBOLS,
        '',
        username
    )
    if invalid_chars_match:
        raise ValidationError(
            (
                'В нике {username} обнаружены недопустимые '
                'символы: {invalid_chars}'
            ).format(
                username=username,
                invalid_chars=''.join(set(invalid_chars_match))
            )
        )

    return username


def validate_slug(slug):
    invalid_chars_match = re.sub(
        settings.SLUG_ACCEPTABLE_SYMBOLS,
        '',
        slug
    )
    if invalid_chars_match:
        raise ValidationError(
            (
                'В slug {slug} обнаружены недопустимые '
                'символы: {invalid_chars}'
            ).format(
                slug=slug,
                invalid_chars=''.join(set(invalid_chars_match))
            )
        )

    return slug
