"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import arw_constants as C
import arw_scenario as S


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=320):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def short(order) -> str:
    return "".join(S.name(a) for a in order)


def build_follow(a):
    """Anteil der Profile, in denen das Ergebnis der Ordnung von Wähler i entspricht (bei einer Diktatur 100 % für genau einen Wähler)."""
    shares = a.follow
    xs = [f"Wähler {i + 1}" for i in range(len(shares))]
    fig = go.Figure(go.Bar(x=xs, y=[100 * v for v in shares], marker_color=[C.COLOR_VOTER[i % len(C.COLOR_VOTER)] for i in range(len(shares))], hovertemplate="%{x}: %{y:.1f} % der Profile<extra></extra>"))
    fig.update_yaxes(title_text="Ergebnis folgt dem Wähler (% der Profile)", range=[0, 105])
    fig.update_xaxes(type="category")
    return _base(fig, height=280)


def build_grid(a):
    """Bei zwei Wählern: die Wohlfahrtsfunktion als Tabelle; Zeilen die Ordnung von Wähler 1, Spalten die von Wähler 2, die Zelle ist das Ergebnis (Farbe je Ergebnisordnung). Sonst None."""
    if a.settings.n != 2 or a.result is None or a.result.swf is None:
        return None
    orders = S.domain_orders(a.settings.m, a.settings.domain)
    outs = S.linear_orders(a.settings.m)
    index = {o: i for i, o in enumerate(outs)}
    z = [[index[a.result.swf[(p, q)]] for q in orders] for p in orders]
    text = [[short(a.result.swf[(p, q)]) for q in orders] for p in orders]
    palette = ["#4c78a8", "#e0a030", "#2F6B65", "#b04a3a", "#7f7f7f", "#9c6fb6"]
    steps = len(outs)
    scale = []
    for i in range(steps):
        color = palette[i % len(palette)]
        scale += [[i / steps, color], [(i + 1) / steps, color]]
    fig = go.Figure(go.Heatmap(z=z, x=[short(q) for q in orders], y=[short(p) for p in orders], text=text, texttemplate="%{text}", colorscale=scale, zmin=0, zmax=steps, showscale=False, xgap=2, ygap=2,
                               hovertemplate="Wähler 1: %{y}, Wähler 2: %{x}, Ergebnis: %{text}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title_text="Ordnung von Wähler 1")
    fig.update_xaxes(side="top", title_text="Ordnung von Wähler 2", type="category")
    fig.update_yaxes(type="category")
    return _base(fig, height=120 + 52 * len(orders))


def _status_heatmap(rows_labels, columns, cells):
    """Gemeinsame Heatmap: Zellen mit Status (lösbar grün, unlösbar rot, zu groß grau) und Text."""
    code = {"lösbar": 1, "unlösbar": 0, "zu groß": 0.5, "unbekannt": 0.5}
    z = [[code[cells[(r, c)][0]] for c in columns] for r in rows_labels]
    text = [[cells[(r, c)][1] for c in columns] for r in rows_labels]
    fig = go.Figure(go.Heatmap(z=z, x=list(columns), y=list(rows_labels), text=text, texttemplate="%{text}", zmin=0, zmax=1, showscale=False, xgap=2, ygap=2,
                               colorscale=[[0, C.COLOR_NO], [0.49, C.COLOR_NO], [0.5, "#bdbdbd"], [0.51, C.COLOR_OK], [1, C.COLOR_OK]], hovertemplate="%{y}, %{x}: %{text}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(side="top", type="category")
    return fig


def build_cases(rows):
    """Lösbarkeit je Größe (Zeilen) und Axiomauswahl (Spalten)."""
    labels = []
    cells = {}
    columns = []
    for r in rows:
        label = f"{r['n']} Wähler, {r['m']} Alternativen"
        if label not in labels:
            labels.append(label)
        if r["variante"] not in columns:
            columns.append(r["variante"])
        cells[(label, r["variante"])] = (r["status"], f"{r['status']}")
    return _base(_status_heatmap(labels, columns, cells), height=110 + 38 * len(labels))


def build_counts(rows):
    """Zahl der Wohlfahrtsfunktionen mit Pareto und Unabhängigkeit und davon Diktaturen, je Größe."""
    xs = [f"{r['n']} W., {r['m']} A." for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["count"] for r in rows], name="Lösungen", marker_color=C.COLOR_VOTER[0], hovertemplate="%{x}: %{y}<extra>Lösungen</extra>"))
    fig.add_trace(go.Bar(x=xs, y=[r["dictatorships"] for r in rows], name="davon Diktaturen", marker_color=C.COLOR_VOTER[1], hovertemplate="%{x}: %{y}<extra>Diktaturen</extra>"))
    fig.update_yaxes(title_text="Zahl der Wohlfahrtsfunktionen", type="log")
    fig.update_xaxes(type="category")
    fig.update_layout(barmode="group")
    return _base(fig, height=340)


def build_domain(rows):
    """Lösbarkeit aller drei Axiome auf allen Ordnungen gegen einspitzige Ordnungen, je Größe."""
    labels, cells, columns = [], {}, []
    for r in rows:
        label = f"{r['n']} Wähler, {r['m']} Alternativen"
        column = C.DOMAINS[r["domain"]]
        if label not in labels:
            labels.append(label)
        if column not in columns:
            columns.append(column)
        cells[(label, column)] = (r["status"], r["status"])
    return _base(_status_heatmap(labels, columns, cells), height=110 + 38 * len(labels))
