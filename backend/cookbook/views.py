from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from .models import Recipe


def short_link_redirect(request, pk):
    if not Recipe.objects.filter(id=pk).exists():
        raise ValidationError(f'Рецепт с идентификатором {pk} не найден!')
    return redirect(f'/recipes/{pk}')
