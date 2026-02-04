from cookbook.models import Tag
from .load_json_fixture import LoadJsonFixtureCommand


class Command(LoadJsonFixtureCommand):
    help = 'Загрузить теги из tags.json'
    model_class = Tag
    fixture_file = 'tags.json'
