from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def short_link_redirect(request, pk):
    if not Recipe.objects.filter(id=pk).exists():
        raise Http404(f'Рецепта {pk} не существует!')
    return redirect(f'/recipes/{pk}')
