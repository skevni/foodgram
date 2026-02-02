from django.template.loader import render_to_string
from django.utils import timezone


def prepare_shopping_list_html(ingredients, recipes):
    context = {
        'recipes': recipes,
        'total_ingredients': ingredients,
        'date': timezone.now().strftime('%d.%m.%Y'),
    }

    return render_to_string('shopping_list_template.html', context)
