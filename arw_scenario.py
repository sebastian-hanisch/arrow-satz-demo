"""Szenario: Alternativen, Ordnungen, Bereiche und Profile. Eine Ordnung ist ein Tupel von Alternativen, die beste zuerst; ein Profil ist ein Tupel mit je einer Ordnung je Wähler."""

import itertools
import math

import arw_constants as C


def name(a: int) -> str:
    """Buchstabe der Alternative (0 → A)."""
    return chr(ord("A") + a)


def linear_orders(m: int) -> list:
    """Alle strikten Ordnungen von m Alternativen in lexikografischer Reihenfolge."""
    if m < 1:
        raise ValueError("Mindestens eine Alternative")
    return list(itertools.permutations(range(m)))


def single_peaked_orders(m: int) -> list:
    """Einspitzige Ordnungen bezüglich der Achse A < B < C < …: jede Anfangsstrecke der Ordnung ist ein Abschnitt der Achse."""
    result = []
    for order in linear_orders(m):
        if all(max(order[:k]) - min(order[:k]) == k - 1 for k in range(1, m + 1)):
            result.append(order)
    return result


def domain_orders(m: int, domain: str) -> list:
    if domain == "alle":
        return linear_orders(m)
    if domain == "einspitzig":
        return single_peaked_orders(m)
    raise ValueError(domain)


def prefers(order, a: int, b: int) -> bool:
    """Steht a in der Ordnung vor b?"""
    return order.index(a) < order.index(b)


def order_text(order) -> str:
    return " > ".join(name(a) for a in order)


def profiles(n: int, m: int, domain: str) -> list:
    return list(itertools.product(domain_orders(m, domain), repeat=n))


def variable_count(n: int, m: int, domain: str) -> int:
    """Zahl der Variablen des Modells: Profile mal Ausgabeordnungen (die Ausgabe ist immer eine beliebige strikte Ordnung)."""
    return len(domain_orders(m, domain)) ** n * math.factorial(m)


def size_ok(n: int, m: int, domain: str) -> bool:
    return variable_count(n, m, domain) <= C.MAX_VARIABLES
