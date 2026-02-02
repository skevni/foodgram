import base64
import io
import os

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.exceptions import NotFound
from xhtml2pdf import pisa


def get_dejavu_base64():
    """Возвращает base64 содержимое DejaVuSans.ttf"""
    font_path = os.path.join(
        settings.STATIC_ROOT, 'fonts', 'DejaVuSans.ttf')
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт не найден: {font_path}")

    with open(font_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def link_callback(uri, rel):
    """
    Преобразует статические/медиа URI в абсолютные пути на файловой системе.
    """
    if uri.startswith('static/'):
        path = os.path.join(
            settings.STATIC_ROOT or settings.STATICFILES_DIRS[0],
            uri.replace('static/', '', 1))
    elif uri.startswith('/static/'):
        path = os.path.join(
            settings.STATIC_ROOT or settings.STATICFILES_DIRS[0],
            uri.lstrip('/static/'))
    else:
        path = os.path.join(settings.BASE_DIR, uri.lstrip('/'))
    return path


def prepare_shopping_list_pdf(ingredients, recipes):
    context = {
        'recipes': recipes,
        'total_ingredients': ingredients,
        'date': timezone.now().strftime("%d.%m.%Y"),
    }

    html_string = render_to_string('shopping_list_template.html', context)

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        html_string,
        dest=pdf_buffer,
        encoding='utf-8',
        # link_callback=link_callback
    )

    if pisa_status.err:
        raise NotFound('Ошибка генерации PDF!')
    pdf_buffer.seek(0)
    return pdf_buffer


def prepare_shopping_list_html(ingredients, recipes):
    context = {
        'recipes': recipes,
        'total_ingredients': ingredients,
        'date': timezone.now().strftime("%d.%m.%Y"),
    }

    return render_to_string('shopping_list_template.html', context)
