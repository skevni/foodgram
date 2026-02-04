import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class LoadJsonFixtureCommand(BaseCommand):
    """Базовый класс для загрузки JSON-фикстур."""

    def ensure_connection(self):
        from django.db import connection
        connection.ensure_connection()

    model_class = None
    fixture_file = None
    data_dir = Path.joinpath(settings.BASE_DIR, 'data')

    def handle(self, *args, **options):
        if not self.model_class or not self.fixture_file:
            self.stdout.write(self.style.ERROR(
                'model_class и fixture_file должны быть определены!'))
            return

        try:
            self.ensure_connection()
            with open(Path.joinpath(
                self.data_dir, self.fixture_file), 'r', encoding='utf-8'
            ) as file:
                all_records = self.model_class.objects.bulk_create(
                    (self.model_class(**row) for row in json.load(file)),
                    ignore_conflicts=False
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Выполнена загрузка фала {file.name}. '
                        f'Количество: {len(all_records)}.'
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Файл {file.name}.\nОшибка: {e}')
            )
