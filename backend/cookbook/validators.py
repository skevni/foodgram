import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(username):
    """Функция для глобального валидатора по пользователям"""

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
