"""Einmalige Messung der README-Zahlen (nicht Teil der App): feste Fälle, Ausgabe auf stdout. Alle Fälle sind exakt gelöst (kein Zufall); die Rechenzeiten hängen vom Rechner ab und stehen nur zur Orientierung dabei."""

import sys
import time

sys.path.insert(0, ".")
import arw_algorithm as A
import arw_constants as C
import arw_evaluation as ev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

t0 = time.time()
print("PRESETS")
for name, p in C.PRESETS.items():
    a = ev.analyse(ev.Settings(**p))
    print(name, "|", ev.verdict_state(a)[1])

print("KERNE (minimaler unlösbarer Kern, Löschverfahren)")
for n, m in ((2, 3), (3, 3), (4, 3), (2, 4)):
    groups = A.groups_for(n, m, C.AXIOMS)
    t = time.time()
    core = A.minimal_core(n, m, "alle", groups)
    print(f"n={n} m={m}: {len(core)} von {len(groups)} Gruppen ({round(time.time() - t, 1)} s):", [A.group_text(g) for g in core])

for title, fn, table, verdict in (("REIHE 1 (Lösbarkeit)", ev.series_cases, ev.cases_table, ev.verdict_cases),
                                  ("REIHE 2 (Zahl der Regeln)", ev.series_counts, ev.counts_table, ev.verdict_counts),
                                  ("REIHE 3 (einspitzig)", ev.series_domain, ev.domain_table, ev.verdict_domain)):
    t = time.time()
    rows = fn()
    print(title, round(time.time() - t, 1), "s")
    for r in table(rows):
        print("   ", r)
    print("   ", verdict(rows))
print("sec", round(time.time() - t0, 1))
