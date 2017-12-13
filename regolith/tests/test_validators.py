from regolith.validators import validate_schema
from regolith.schemas import schemas
from regolith.exemplars import exemplars
import pytest


@pytest.mark.parametrize('key', schemas.keys())
def test_validation(key):
    validate_schema(exemplars[key], schemas[key], (key, ))


