import io

from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.exceptions import NotFound
from xhtml2pdf import pisa


def prepare_shopping_list(ingridients, recipes):
    context = {
        'recipes': recipes,
        'total_ingredients': ingridients,
        'date': timezone.now().strftime("%d.%m.%Y"),
    }

    html_string = render_to_string('shopping_list_template.html', context)

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer,
                                 encoding='utf-8')

    if pisa_status.err:
        raise NotFound('Ошибка генерации PDF!')
    pdf_buffer.seek(0)
    return pdf_buffer
