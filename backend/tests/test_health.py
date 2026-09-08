import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.requests import validate_bounds


def test_validate_bounds_ok():
    bounds, err = validate_bounds(
        {
            "bounds": {
                "minLon": 77.0,
                "minLat": 28.5,
                "maxLon": 77.3,
                "maxLat": 28.7,
            }
        }
    )
    assert err is None
    assert bounds["minLat"] == 28.5


def test_validate_bounds_missing():
    bounds, err = validate_bounds({})
    assert bounds is None
    assert "bounds" in err.lower()


def test_validate_bounds_incomplete():
    bounds, err = validate_bounds({"bounds": {"minLon": 1}})
    assert bounds is None
    assert err is not None
