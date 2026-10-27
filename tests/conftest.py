"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def two_two():
    """Zwei Wähler, zwei Alternativen A und B: vier Profile. Von Hand: Pareto legt (A>B, A>B) auf A>B und (B>A, B>A) auf B>A fest; bei Uneinigkeit gibt es vier Möglichkeiten, zwei davon sind Diktaturen, es bleiben zwei Lösungen."""
    return 2, 2
