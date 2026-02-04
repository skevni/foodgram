from cookbook.models import Ingredient
from .load_json_fixture import LoadJsonFixtureCommand


class Command(LoadJsonFixtureCommand):
    help = 'Загрузить данные об ингредиентах из ingredients.json'
    model_class = Ingredient
    fixture_file = 'ingredients.json'
