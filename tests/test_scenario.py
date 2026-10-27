"""Szenario: Ordnungen, einspitzige Bereiche, Profile und die Größe des Modells."""

import math

import pytest

import arw_constants as C
import arw_scenario as S


def test_namen_und_texte():
    assert [S.name(a) for a in range(4)] == ["A", "B", "C", "D"]
    assert S.order_text((2, 0, 1)) == "C > A > B"


def test_strikte_ordnungen():
    assert S.linear_orders(1) == [(0,)] and S.linear_orders(2) == [(0, 1), (1, 0)]
    orders = S.linear_orders(3)
    assert len(orders) == 6 and orders[0] == (0, 1, 2) and orders[-1] == (2, 1, 0) and len(set(orders)) == 6
    assert len(S.linear_orders(4)) == 24
    with pytest.raises(ValueError):
        S.linear_orders(0)


def test_vorrang_innerhalb_einer_ordnung():
    assert S.prefers((1, 0, 2), 1, 0) and not S.prefers((1, 0, 2), 0, 1) and S.prefers((1, 0, 2), 0, 2) and S.prefers((1, 0, 2), 1, 2)


def test_einspitzige_ordnungen():
    assert S.single_peaked_orders(1) == [(0,)] and S.single_peaked_orders(2) == [(0, 1), (1, 0)]
    assert set(S.single_peaked_orders(3)) == {(0, 1, 2), (1, 0, 2), (1, 2, 0), (2, 1, 0)}              # A B C, B A C, B C A, C B A
    assert len(S.single_peaked_orders(4)) == 8 and len(S.single_peaked_orders(5)) == 16               # 2^(m−1)
    assert (0, 2, 1) not in S.single_peaked_orders(3) and (2, 0, 1) not in S.single_peaked_orders(3)


def test_bereiche_und_profile():
    assert S.domain_orders(3, "alle") == S.linear_orders(3) and S.domain_orders(3, "einspitzig") == S.single_peaked_orders(3)
    with pytest.raises(ValueError):
        S.domain_orders(3, "Mitte")
    assert len(S.profiles(2, 3, "alle")) == 36 and len(S.profiles(3, 3, "einspitzig")) == 64 and len(S.profiles(2, 2, "alle")) == 4
    p = S.profiles(2, 2, "alle")
    assert p[0] == ((0, 1), (0, 1)) and p[1] == ((0, 1), (1, 0)) and len(set(p)) == 4


def test_zahl_der_variablen_und_grenze():
    assert S.variable_count(2, 3, "alle") == 36 * 6 == 216
    assert S.variable_count(3, 3, "alle") == 216 * 6 == 1296
    assert S.variable_count(3, 3, "einspitzig") == 64 * 6
    assert S.variable_count(2, 4, "alle") == 576 * 24 == 13824
    assert S.variable_count(4, 3, "alle") == 1296 * math.factorial(3)
    assert S.size_ok(4, 3, "alle") and S.size_ok(2, 4, "alle") and not S.size_ok(5, 3, "alle") and not S.size_ok(3, 4, "alle") and S.size_ok(5, 3, "einspitzig")
    assert S.size_ok(2, 2, "alle") and C.MAX_VARIABLES == 20000
