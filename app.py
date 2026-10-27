"""Satz von Arrow: unmöglich per Löser - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Gelber Kandidat der Linie „Abstimmen und Fair Teilen“: Wohlfahrtsfunktionen für wenige Wähler und Alternativen als Erfüllbarkeitsproblem. Ein Löser (CP-SAT) sucht eine Funktion, die Pareto, Unabhängigkeit irrelevanter Alternativen und Nichtdiktatur erfüllt, meldet
die Unmöglichkeit (Arrow) oder liefert Beispiele und die Zahl der Lösungen; ein Löschverfahren findet einen minimalen unlösbaren Kern. Der Kern liegt in arw_algorithm.py.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import arw_algorithm as A
import arw_constants as C
import arw_evaluation as ev
import arw_scenario as S
from arw_evaluation import Settings, analyse, seconds_text
from arw_layout import dunkles_design, kopf_css
from arw_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    sidebar_presets,
    sync_query_params,
)
from arw_visualization import build_cases, build_counts, build_domain, build_follow, build_grid

st.set_page_config(page_title="Satz von Arrow – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _core(settings):
    return ev.core_of(settings)


@st.cache_data(show_spinner=False)
def _series_cases():
    return ev.series_cases()


@st.cache_data(show_spinner=False)
def _series_counts():
    return ev.series_counts()


@st.cache_data(show_spinner=False)
def _series_domain():
    return ev.series_domain()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in arw_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧮 Satz von Arrow: unmöglich per Löser")
st.markdown(
    """
Eine Gruppe soll aus den **Rangfolgen ihrer Mitglieder** eine **gemeinsame Rangfolge** bilden. Der **Satz von Arrow** sagt: ab drei Alternativen gibt es keine Regel, die drei einleuchtende Forderungen zugleich erfüllt: **Pareto** (sind sich alle einig, dass A vor B steht, steht A auch im Ergebnis vor B), **Unabhängigkeit irrelevanter Alternativen** (die Ordnung von A und B im Ergebnis hängt nur davon ab, wie die Wähler A und B ordnen, nicht von C) und **Nichtdiktatur** (kein Wähler bestimmt immer allein).
Diese Demo **bestätigt das für kleine Fälle mit einem Löser**: jede mögliche Regel ist eine Antwort auf die Frage „welche Ergebnisordnung gehört zu welchem Profil?“, die Forderungen sind lineare Bedingungen, und der Löser antwortet **lösbar** (mit Beispielen und der Zahl der Lösungen) oder **unlösbar** (mit einem minimalen Kern der Bedingungen, die schon genügen). Lockert man ein Axiom oder schränkt die Ordnungen ein, wird es lösbar.
Verwandt: `wahlaxiome-demo` (Axiome und Gegenbeispiele bei bekannten Regeln), `wahlregeln-demo` (Regeln für Präferenzen) und `sat-phasenuebergang-demo` (Erfüllbarkeit als Rechenproblem).

Weiter unten: die **Kernfrage**, der Abschnitt **🔬 Feste Reihen** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So wird gerechnet", expanded=True):
    st.markdown(
        """
1. **Profile und Ergebnisse.** Ein **Profil** gibt für jeden der n Wähler eine strikte Ordnung der m Alternativen an (m! Möglichkeiten je Wähler, also (m!)ⁿ Profile bei allen Ordnungen). Eine **Wohlfahrtsfunktion** ordnet jedem Profil eine strikte Ordnung als Ergebnis zu.
2. **Variablen.** Zu jedem Profil p und jeder Ergebnisordnung o gibt es eine Ja-Nein-Variable x(p, o); je Profil ist genau eine gleich 1. Das sind Profile mal m! Variablen.
3. **Pareto.** Stehen bei allen Wählern in p die Alternative a vor b, sind alle Ergebnisordnungen mit b vor a verboten.
4. **Unabhängigkeit.** Zwei Profile, in denen jeder Wähler a und b gleich ordnet, müssen a und b im Ergebnis gleich ordnen: die Summe der Variablen aller Ergebnisordnungen mit a vor b ist in beiden Profilen gleich.
5. **Nichtdiktatur.** Für jeden Wähler i gibt es mindestens ein Profil, in dem das Ergebnis nicht seiner Ordnung entspricht.
6. **Antwort.** Der Löser (CP-SAT) sucht eine Belegung. Meldet er unlösbar (gegengeprüft mit einem zweiten Modell), bestätigt das den Satz für diese Größe. Ein **minimaler Kern** entsteht durch Weglassen: jede Bedingungsgruppe wird entfernt, wenn der Rest unlösbar bleibt; je nach Reihenfolge der Gruppen kommen verschiedene minimale Kerne heraus, auch kleinere als der gezeigte.
7. **Gegenprobe.** Eine gefundene Funktion wird unabhängig von der Modellrechnung nach den Definitionen der Axiome nachgeprüft.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Größe**")
    n = st.slider("Zahl der Wähler", *bounds("n_slider"), key="n_slider", help="Wie viele Wähler eine Rangfolge angeben. Bei drei Alternativen sind bis zu vier Wähler rechenbar, bei vier Alternativen zwei.")
    m = st.slider("Zahl der Alternativen", *bounds("m_slider"), key="m_slider", help="Wie viele Alternativen geordnet werden. Mit zwei Alternativen ist alles erfüllbar; Arrow gilt ab drei.")
    domain = st.selectbox("Erlaubte Ordnungen der Wähler", list(C.DOMAINS), format_func=C.DOMAINS.get, key="domain_select", help="Alle strikten Ordnungen, oder nur einspitzige (jede Anfangsstrecke der Ordnung ist ein Abschnitt der Achse A < B < C …).")
    st.markdown("**Axiome**")
    pareto = st.toggle("Pareto", key="pareto_toggle", help="Sind sich alle Wähler einig, a vor b zu stellen, steht a im Ergebnis vor b.")
    iia = st.toggle("Unabhängigkeit irrelevanter Alternativen", key="iia_toggle", help="Die Ordnung von a und b im Ergebnis hängt nur davon ab, wie die Wähler a und b ordnen.")
    nd = st.toggle("Nichtdiktatur", key="nd_toggle", help="Es gibt keinen Wähler, dessen Ordnung in jedem Profil das Ergebnis ist.")

sync_query_params({"n_slider": int(n), "m_slider": int(m), "pareto_toggle": bool(pareto), "iia_toggle": bool(iia), "nd_toggle": bool(nd), "domain_select": domain})

settings = Settings(n=int(n), m=int(m), pareto=bool(pareto), iia=bool(iia), nd=bool(nd), domain=domain)
with st.spinner("Löse das Modell …"):
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
if a.too_big:
    st.info(f"Mit {settings.n} Wählern und {settings.m} Alternativen ({C.DOMAIN_PHRASE[settings.domain]}) hätte das Modell {S.variable_count(settings.n, settings.m, settings.domain)} Variablen; die Demo rechnet höchstens {C.MAX_VARIABLES}.")
else:
    r = a.result
    m1, m2, m3 = st.columns(3)
    m1.metric("Ergebnis des Lösers", r.status, delta=f"in {seconds_text(r.seconds)}", delta_color="off")
    m2.metric("Variablen", f"{r.variables}", delta=f"{r.profiles} Profile", delta_color="off")
    m3.metric("Lösungen", ev.count_text(a).replace("genau ", "") if r.status == "lösbar" else "keine", delta="Aufzählung bis 500" if r.status == "lösbar" else "Löser meldet unlösbar" if r.status == "unlösbar" else "Zeitgrenze erreicht", delta_color="off")
    if r.status == "lösbar":
        st.markdown("**Eine gefundene Wohlfahrtsfunktion** (Auszug aus den Profilen)")
        st.table(ev.example_rows(a))
        st.caption(f"Art dieser Funktion: {A.classify(r.swf, settings.n)}. Gegenprobe nach den Definitionen: " + ", ".join(f"{C.AXIOM_NAMES[k]} {'erfüllt' if v else 'verletzt'}" for k, v in a.checked.items()) + ".")
        grid = build_grid(a)
        if grid is not None:
            st.markdown("**Die ganze Funktion bei zwei Wählern**")
            st.plotly_chart(grid, width="stretch", key="grid_chart")
            st.caption("Zeilen: Ordnung von Wähler 1, Spalten: Ordnung von Wähler 2, Zelle: Ergebnis (je Ergebnisordnung eine Farbe). Eine Diktatur von Wähler 1 zeigt waagerechte Streifen (das Ergebnis ist in jeder Zeile gleich der Zeilenordnung), eine Diktatur von Wähler 2 senkrechte.")
        st.markdown("**Wem folgt das Ergebnis?**")
        st.plotly_chart(build_follow(a), width="stretch", key="follow_chart")
        st.caption("Anteil der Profile, in denen das Ergebnis genau der Ordnung eines Wählers entspricht. Eine Diktatur hat bei einem Wähler 100 %.")
        st.markdown("**Arten der gefundenen Lösungen**")
        st.table(ev.kind_rows(a))
    elif r.status == "unlösbar":
        st.markdown("**Warum unlösbar? Ein minimaler Kern**")
        st.caption("Ein Kern ist eine Teilmenge der Bedingungen, die allein schon unlösbar ist; entfernt man eine, wird der Rest lösbar. Er wird auf Klick durch Weglassen berechnet (bei größeren Fällen einige Sekunden).")
        if st.button("Minimalen Kern berechnen", key="core_button"):
            t0 = time.perf_counter()
            with st.spinner("Suche einen minimalen Kern …"):
                _core(settings)
            st.session_state["core_for"] = (settings, time.perf_counter() - t0)
        if st.session_state.get("core_for", (None, 0))[0] == settings:
            core = _core(settings)
            st.table(ev.core_rows(core))
            st.caption(f"{len(core)} von {len(a.groups)} Bedingungsgruppen genügen (Rechenzeit dieser Sitzung {seconds_text(st.session_state['core_for'][1])}). Der Kern ist minimal, aber weder der kleinste noch eindeutig; welche Pareto-Gruppen er enthält, ergibt sich aus der Reihenfolge der Gruppen.")
    with st.expander("Größe des Modells"):
        st.table(ev.summary_rows(a))

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Gibt es eine Regel, die alle gewählten Forderungen erfüllt?")
kind, text = ev.verdict_state(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Reihen --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Feste Reihen")
st.caption("Feste Programme, unabhängig von den Reglern: alle Fälle exakt gelöst (kein Zufall in der Rechnung; der Löser läuft mit einem Faden und festem Zufalls-Seed). Die Rechenzeiten sind Messungen dieser Sitzung und hängen vom Rechner ab. Jede Reihe rechnet auf Klick einige Sekunden.")
tab1, tab2, tab3 = st.tabs(["Welche Kombination ist unmöglich?", "Wie viele Regeln bleiben?", "Hilft ein engerer Bereich?"])
with tab1:
    st.markdown("**Lösbarkeit je Größe und Axiomauswahl.** Nur alle drei Axiome zusammen sind ab drei Alternativen unlösbar; jede Lockerung ist lösbar.")
    if st.button("Reihe rechnen", key="cases_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_cases()
        st.session_state["cases_done"] = time.perf_counter() - t0
    if "cases_done" in st.session_state:
        rows = _series_cases()
        st.plotly_chart(build_cases(rows), width="stretch", key="cases_chart")
        st.table(ev.cases_table(rows))
        kind, text = ev.verdict_cases(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {seconds_text(st.session_state['cases_done'])} (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab2:
    st.markdown("**Zahl der Wohlfahrtsfunktionen mit Pareto und Unabhängigkeit** (ohne Nichtdiktatur): ab drei Alternativen bleiben nur die Diktaturen, bei zwei Alternativen mehr.")
    if st.button("Reihe rechnen", key="counts_button"):
        t0 = time.perf_counter()
        with st.spinner("Zähle die Lösungen …"):
            _series_counts()
        st.session_state["counts_done"] = time.perf_counter() - t0
    if "counts_done" in st.session_state:
        rows = _series_counts()
        st.plotly_chart(build_counts(rows), width="stretch", key="counts_chart")
        st.table(ev.counts_table(rows))
        kind, text = ev.verdict_counts(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {seconds_text(st.session_state['counts_done'])} (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab3:
    st.markdown("**Alle drei Axiome auf allen Ordnungen gegen einspitzige Ordnungen.** Schränkt man die Meinungen auf einspitzige ein (alle ordnen entlang derselben Achse), ist die Forderung für die gerechneten Größen erfüllbar (allgemein für ungerade Wählerzahl).")
    if st.button("Reihe rechnen", key="domain_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_domain()
        st.session_state["domain_done"] = time.perf_counter() - t0
    if "domain_done" in st.session_state:
        rows = _series_domain()
        st.plotly_chart(build_domain(rows), width="stretch", key="domain_chart")
        st.table(ev.domain_table(rows))
        kind, text = ev.verdict_domain(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {seconds_text(st.session_state['domain_done'])} (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Das Ergebnis ist eine strikte Ordnung** | Arrows Satz gilt auch für Ergebnisse mit Gleichstand (schwache Ordnungen); hier sind nur strikte Ordnungen als Ergebnis zugelassen, das schränkt die Funktion stärker ein und ist nicht dasselbe Modell. | – |
| **Wenige Wähler und Alternativen** | Der Löser meldet die Unmöglichkeit nur für die gerechneten Größen (höchstens 20.000 Variablen); der allgemeine Satz gilt für beliebige Größen, braucht aber einen Beweis auf Papier. | `wahlaxiome-demo` (Einzelfälle bei bekannten Regeln) |
| **Alle Ordnungen kommen vor** | Auf eingeschränkten Bereichen (einspitzig) ist die Forderung erfüllbar; echte Meinungen sind nicht immer einspitzig. | diese Demo (Reihe „Hilft ein engerer Bereich?“) |
| **Wohlfahrt ist eine Rangfolge** | Verfahren, die Nutzen vergleichen oder Stärken berücksichtigen, verlassen Arrows Rahmen (rein ordinale Angaben). | `quadratisches-waehlen-demo` (Stärke der Meinung) |
| **Axiome in dieser Form** | Schwächere Fassungen (zum Beispiel nur Bereiche mit Mehrheitsrelationen) sind nicht gerechnet. | – |
| **Modell, kein Befund über Abstimmungen** | Die Zahlen sagen, was die Rechnung für diese Größen liefert, nicht, wie sich echte Wähler verhalten. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Profile.** Sei $A$ die Menge der $m$ Alternativen, $\mathcal{L}$ die Menge der strikten Ordnungen auf $A$ ($|\mathcal{L}| = m!$) und $\mathcal{D} \subseteq \mathcal{L}$ der erlaubte Bereich. Ein Profil ist $p \in \mathcal{D}^n$. Eine Wohlfahrtsfunktion ist $f : \mathcal{D}^n \to \mathcal{L}$.

**Variablen.** $x_{p,o} \in \{0, 1\}$ mit $\sum_{o \in \mathcal{L}} x_{p,o} = 1$ für jedes Profil $p$; $x_{p,o} = 1$ heißt $f(p) = o$.

**Pareto.** Für Profile $p$ und Alternativen $a \ne b$ mit $a \succ_{p_i} b$ für alle $i$: $x_{p,o} = 0$ für alle $o$ mit $b \succ_o a$.

**Unabhängigkeit.** Für Alternativen $a \ne b$ und Profile $p, q$ mit $\bigl(a \succ_{p_i} b \iff a \succ_{q_i} b\bigr)$ für alle $i$:
$$\sum_{o:\, a \succ_o b} x_{p,o} = \sum_{o:\, a \succ_o b} x_{q,o}.$$

**Nichtdiktatur.** Für jeden Wähler $i$:
$$\sum_{p} x_{p,\,p_i} \le |\mathcal{D}|^n - 1.$$

**Satz von Arrow.** Für $m \ge 3$ und $\mathcal{D} = \mathcal{L}$ ist das System unlösbar (Arrow 1951). Ohne Nichtdiktatur sind die Lösungen genau die $n$ Diktaturen $f(p) = p_i$. Auf dem Bereich der einspitzigen Ordnungen bezüglich einer Achse ist es für die gerechneten Größen lösbar; allgemein erfüllt für ungerade $n$ die Mehrheitsrelation alle drei Axiome.

**Minimaler unlösbarer Kern.** Eine Menge von Bedingungsgruppen $G$ ist ein minimaler unlösbarer Kern, wenn das System mit genau diesen Gruppen unlösbar ist und mit jeder echten Teilmenge lösbar. Das Löschverfahren entfernt der Reihe nach jede Gruppe, deren Wegfall das System unlösbar lässt; es findet einen minimalen, nicht unbedingt den kleinsten Kern, und je nach Reihenfolge der Gruppen verschiedene.

**Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Arrow, „Social Choice and Individual Values“, 1951; Geanakoplos, „Three Brief Proofs of Arrow’s Impossibility Theorem“, Economic Theory 2005; Tang und Lin, „A Computer-Aided Proof of Arrow’s Theorem“, Artificial Intelligence 2009; Black, „On the Rationale of Group Decision-making“, 1948 (einspitzige Präferenzen).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
