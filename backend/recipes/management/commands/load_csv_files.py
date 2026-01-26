import csv
import os
import pdb

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from pytils.translit import translify

from recipes.models import Tag, Ingredient


class Command(BaseCommand):
    help = 'Load data from CSV files in data/ folder'

    def handle(self, *args, **options):
        base_dir = os.path.join(os.path.dirname(
            __file__), '..', '..', '..', 'data')
        base_dir = os.path.abspath(base_dir)

        self.stdout.write(f'Looking for CSV files in: {base_dir}')

        if not os.path.exists(base_dir):
            self.stdout.write(self.style.ERROR(
                f'Directory {base_dir} does not exist!'))
            return

        # Загрузка тегов
        tags_file = os.path.join(base_dir, 'tags.csv')
        if os.path.exists(tags_file):
            self.load_tags(tags_file)
        else:
            self.stdout.write(self.style.WARNING(f'{tags_file} not found!'))

        # Загрузка ингредиентов
        ingredients_file = os.path.join(base_dir, 'ingredients.csv')
        if os.path.exists(ingredients_file):
            self.load_ingredients(ingredients_file)
        else:
            self.stdout.write(self.style.WARNING(
                f'{ingredients_file} not found!'))

    def load_tags(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            tags = []
            for row in reader:
                name = row['name'].strip()
                slug = (
                    row.get('slug', '').strip()
                    or slugify(translify(name), allow_unicode=True)
                )
                tags.append(Tag(name=name, slug=slug))
            with transaction.atomic():
                Tag.objects.bulk_create(tags, ignore_conflicts=False)
            self.stdout.write(self.style.SUCCESS(
                f'Loaded {len(tags)} tags from {file_path}'))

    def load_ingredients(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            ingredients = []
            for row in reader:
                ingredients.append(Ingredient(
                    name=row['name'].strip(),
                    measurement_unit=row['measurement_unit'].strip()
                ))
            
            with transaction.atomic():
                Ingredient.objects.bulk_create(
                    ingredients, ignore_conflicts=False)
            self.stdout.write(self.style.SUCCESS(
                f'Loaded {len(ingredients)} ingredients from {file_path}'))
