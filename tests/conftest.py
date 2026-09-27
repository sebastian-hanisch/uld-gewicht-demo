"""Gemeinsame Fixtures fuer die uld-gewicht-demo Testsuite."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

W, D, H, CHAMFER = 160.0, 150.0, 160.0, 40.0


@pytest.fixture
def container_dims():
    return W, D, H, CHAMFER
