import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ngettext


class LoadJsonFixtureCommand(BaseCommand):
    """Базовый класс для загрузки JSON-фикстур."""

    model_class = None
    fixture_file = None

    def pluralize_russian(count, forms):
        """
        Возвращает правильную форму слова для русского языка.

        :param count: число
        :param forms: кортеж из трёх форм: (1, 2, 5)
            например: ('запись', 'записи', 'записей')
        :return: строка с правильной формой
        """
        count = abs(count) % 100
        if count > 10 and count < 20:
            return forms[2]  # 11-19 -> записей
        count = count % 10
        if count == 1:
            return forms[0]  # 1, 21, 31... -> запись
        elif count in (2, 3, 4):
            return forms[1]  # 2, 3, 4, 22, 23, 24... -> записи
        else:
            return forms[2]  # 5, 6, ..., 20, 25... -> записей

    def handle(self, *args, **options):
        try:
            with open(
                Path.joinpath(
                    Path.joinpath(settings.BASE_DIR, 'data'),
                    self.fixture_file
                ),
                'r',
                encoding='utf-8'
            ) as file:
                all_records = self.model_class.objects.bulk_create(
                    (self.model_class(**row) for row in json.load(file)),
                    ignore_conflicts=False
                )
                count = len(all_records)
                first_part = self.pluralize_russian(
                    count,
                    ('Загружена', 'Загружены', 'Загружено')
                )
                second_part = self.pluralize_russian(
                    count,
                    ('запись', 'записи', 'записей')
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Выполнена загрузка файла {file.name}. '
                        f'{first_part} {count} {second_part}.'
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Файл {file.name}.\nОшибка: {e}')
            )

    
