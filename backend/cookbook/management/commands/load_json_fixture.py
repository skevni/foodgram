import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ngettext


class LoadJsonFixtureCommand(BaseCommand):
    """Базовый класс для загрузки JSON-фикстур."""

    model_class = None
    fixture_file = None

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
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Выполнена загрузка фала {file.name}. '
                        f'{ngettext(
                            'Загружена {count} запись',
                            'Загружено {count} записи',
                            count
                        ).format(count=count)}.'
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Файл {file.name}.\nОшибка: {e}')
            )
