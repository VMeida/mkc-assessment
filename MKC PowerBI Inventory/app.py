"""
app.py – MKC PowerBI Data Lineage Explorer
==========================================
Streamlit app with interactive cytoscape graph.

Node visual conventions
  • Leaf nodes     : solid-fill rectangles
  • Server groups  : dashed-border outer rectangle (sub-container inside Sources)
  • Sources group  : dotted-border outer rectangle (wraps all servers + SP + API)
  • Workspaces     : dotted-border outer rectangle on the right (wraps reports)

Run:
    .venv/bin/streamlit run app.py
"""

import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx
import streamlit as st
from st_cytoscape import cytoscape

# Import reusable graph-building code from generate_lineage.py
sys.path.insert(0, str(Path(__file__).parent))
from generate_lineage import (
    TIER_COLORS,
    TIER_LABELS,
    build_graph,
    load_excel,
    normalize_df1,
    normalize_df2,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXCEL_FILE = Path(__file__).parent / "MKC PowerBI Inventory (1).xlsx"

DIRECT_EDGE_TYPES = {"direct_to_report", "sharepoint_to_report", "api_to_report"}

# Pixel x-positions per tier for the preset layout
TIER_X = {
    5: 180,   # SharePoint  (inside sources compound)
    6: 180,   # API         (inside sources compound)
    0: 180,   # Server      (compound – auto-sized; x drives label placement)
    1: 180,   # Database    (inside server compounds)
    2: 520,   # Dataflow    (standalone middle column)
    3: 860,   # Report      (inside workspace compounds)
    4: 860,   # Workspace   (compound – auto-sized)
}

NODE_SPACING_Y = 70    # vertical px between leaf nodes of the same tier
GROUP_GAP_Y   = 50    # extra vertical gap between groups (servers or workspaces)


# ---------------------------------------------------------------------------
# Data loading – cached across Streamlit reruns
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading PowerBI inventory…")
def load_graph() -> nx.DiGraph:
    df1, df2 = load_excel(str(EXCEL_FILE))
    df1 = normalize_df1(df1)
    df2 = normalize_df2(df2)
    return build_graph(df1, df2)


# ---------------------------------------------------------------------------
# Position computation
# ---------------------------------------------------------------------------

def compute_positions(G: nx.DiGraph) -> dict[str, dict]:
    """
    Return {node_id: {"x": float, "y": float}} for every leaf node.
    Compound nodes (servers, workspaces, sources group) are excluded —
    Cytoscape auto-sizes them around their children.
    """
    positions: dict[str, dict] = {}

    # ── DB nodes: group by server, stacked vertically ──────────────────────
    db_by_server: dict[str, list[str]] = defaultdict(list)
    for nid, attrs in G.nodes(data=True):
        if attrs.get("tier") == 1:
            db_by_server[attrs.get("server", "OTHER")].append(nid)

    y = 40
    for srv in sorted(db_by_server):
        for db_nid in sorted(db_by_server[srv],
                             key=lambda n: G.nodes[n].get("label", "")):
            positions[db_nid] = {"x": float(TIER_X[1]), "y": float(y)}
            y += NODE_SPACING_Y
        y += GROUP_GAP_Y   # gap between server sub-groups

    # ── SharePoint and API nodes (below DBs, inside sources compound) ───────
    sp_api = [(nid, attrs) for nid, attrs in G.nodes(data=True)
              if attrs.get("tier") in (5, 6)]
    for i, (nid, _) in enumerate(sp_api):
        positions[nid] = {"x": float(TIER_X[5]), "y": float(y + i * NODE_SPACING_Y)}

    # ── Dataflow nodes: spread vertically in center column ──────────────────
    df_nodes = sorted(
        [n for n, d in G.nodes(data=True) if d.get("tier") == 2],
        key=lambda n: G.nodes[n].get("label", ""),
    )
    n_df = len(df_nodes)
    # Aim to vertically center dataflows relative to total height of DB column
    db_count = sum(len(v) for v in db_by_server.values())
    total_db_height = db_count * NODE_SPACING_Y + len(db_by_server) * GROUP_GAP_Y
    df_step = max(NODE_SPACING_Y - 5, total_db_height // max(n_df, 1))
    df_y_start = 40
    for i, nid in enumerate(df_nodes):
        positions[nid] = {"x": float(TIER_X[2]), "y": float(df_y_start + i * df_step)}

    # ── Report nodes: group by workspace, stacked vertically ────────────────
    rpt_by_ws: dict[str, list[str]] = defaultdict(list)
    for nid, attrs in G.nodes(data=True):
        if attrs.get("tier") == 3:
            rpt_by_ws[attrs.get("workspace", "__unknown__")].append(nid)

    y = 40
    for ws in sorted(rpt_by_ws):
        for rpt_nid in sorted(rpt_by_ws[ws],
                              key=lambda n: G.nodes[n].get("label", "")):
            positions[rpt_nid] = {"x": float(TIER_X[3]), "y": float(y)}
            y += NODE_SPACING_Y
        y += GROUP_GAP_Y   # gap between workspace groups

    return positions


# ---------------------------------------------------------------------------
# Cytoscape element builder
# ---------------------------------------------------------------------------

def build_elements(
    G: nx.DiGraph,
    positions: dict,
    group_sources: bool,
    group_workspaces: bool,
    show_sources: bool,
    show_dataflows: bool,
    show_direct: bool,
    selected_nid: str | None = None,
) -> list[dict]:
    """
    Convert a NetworkX DiGraph to Cytoscape element dicts.

    Compound-node hierarchy (when grouping enabled):
        _sources_group  (dotted outer rectangle)
          └── srv::*   (dashed inner rectangle, one per server)
                └── db::*  (leaf rectangles)
          └── sp::*  (leaf)
          └── api::* (leaf)
        ws::*          (dotted outer rectangle, one per workspace)
          └── rpt::*  (leaf rectangles)
        df::*          (standalone leaf rectangles in the middle)

    When selected_nid is set, direct neighbours are highlighted and all
    other nodes/edges are dimmed.
    """
    elements: list[dict] = []

    # ── Determine which node IDs are visible ────────────────────────────────
    visible: set[str] = set()
    for nid, attrs in G.nodes(data=True):
        tier = attrs.get("tier", 3)
        if not show_sources and tier in (0, 1, 5, 6):
            continue
        if not show_dataflows and tier == 2:
            continue
        visible.add(nid)

    # ── Neighbourhood for highlight/dim logic ───────────────────────────────
    # neighborhood: node IDs that should be bright (selected + direct neighbours)
    # hl_edges:     (src, dst) pairs whose edge should be highlighted
    neighborhood: set[str] = set()
    hl_edges: set[tuple]   = set()

    if selected_nid and selected_nid in G:
        neighborhood.add(selected_nid)
        for pred in G.predecessors(selected_nid):
            neighborhood.add(pred)
            hl_edges.add((pred, selected_nid))
        for succ in G.successors(selected_nid):
            neighborhood.add(succ)
            hl_edges.add((selected_nid, succ))

        # Pull in compound-node parents so their containers are not dimmed
        for nbr in list(neighborhood):
            if nbr not in G:
                continue
            nbr_attrs = G.nodes[nbr]
            nbr_tier  = nbr_attrs.get("tier", -1)
            if nbr_tier == 1:                           # DB → add its server
                srv = nbr_attrs.get("server", "")
                if srv:
                    neighborhood.add(f"srv::{srv}")
            if nbr_tier == 3:                           # Report → add workspace
                ws = nbr_attrs.get("workspace", "")
                if ws:
                    neighborhood.add(f"ws::{ws}")

        # Add sources-group container if any source-tier node is highlighted
        if any(G.nodes.get(n, {}).get("tier") in (0, 1, 5, 6)
               for n in neighborhood if n in G):
            neighborhood.add("_sources_group")

    # ── Synthetic compound: sources group ───────────────────────────────────
    has_source_nodes = any(
        G.nodes[n].get("tier") in (0, 1, 5, 6) for n in visible
    )
    add_sources_group = group_sources and show_sources and has_source_nodes
    if add_sources_group:
        sg_classes = ["group-sources"]
        if neighborhood:
            sg_classes.append(
                "neighbor-hl" if "_sources_group" in neighborhood else "dimmed"
            )
        elements.append({
            "data": {"id": "_sources_group", "label": "Data Sources"},
            "classes": " ".join(sg_classes),
        })

    # ── Node elements ────────────────────────────────────────────────────────
    for nid in visible:
        attrs = G.nodes[nid]
        tier  = attrs.get("tier", 3)

        node_data: dict = {
            "id":         nid,
            "label":      attrs.get("label", nid.split("::")[-1]),
            "tier":       tier,
            "tier_name":  attrs.get("tier_name", ""),
            "pbi_id":     attrs.get("pbi_id", ""),
            "workspace":  attrs.get("workspace", ""),
            "server":     attrs.get("server", ""),
        }

        classes: list[str] = []

        # ── Compound parent assignment ──────────────────────────────────────
        if group_sources and show_sources:
            if tier == 0:                         # Server → sources group
                if add_sources_group:
                    node_data["parent"] = "_sources_group"
                classes.append("group-server")

            elif tier == 1:                       # DB → its server compound
                srv     = attrs.get("server", "")
                srv_nid = f"srv::{srv}"
                if srv_nid in visible:
                    node_data["parent"] = srv_nid
                elif add_sources_group:
                    node_data["parent"] = "_sources_group"

            elif tier in (5, 6):                  # SP / API → sources group
                if add_sources_group:
                    node_data["parent"] = "_sources_group"

        if group_workspaces and tier == 3:        # Report → its workspace
            ws     = attrs.get("workspace", "")
            ws_nid = f"ws::{ws}"
            if ws_nid in visible:
                node_data["parent"] = ws_nid

        if group_workspaces and tier == 4:        # Workspace → compound container
            classes.append("group-workspace")

        # ── Highlight / dim class ───────────────────────────────────────────
        if neighborhood:
            if nid == selected_nid:
                classes.append("selected-hl")
            elif nid in neighborhood:
                classes.append("neighbor-hl")
            else:
                classes.append("dimmed")

        element: dict = {"data": node_data}
        if classes:
            element["classes"] = " ".join(classes)

        # Preset position for leaf nodes only (compound nodes auto-fit)
        is_compound = (
            (tier == 0 and group_sources and add_sources_group)
            or (tier == 4 and group_workspaces)
        )
        if not is_compound and nid in positions:
            element["position"] = positions[nid]

        elements.append(element)

    # ── Edge elements ────────────────────────────────────────────────────────
    for src, dst, eattrs in G.edges(data=True):
        if src not in visible or dst not in visible:
            continue

        etype = eattrs.get("edge_type", "")

        # report→workspace containment replaces the explicit edge when grouping
        if group_workspaces and etype == "report_to_workspace":
            continue

        is_direct = etype in DIRECT_EDGE_TYPES
        if not show_direct and is_direct:
            continue

        # Source-tier visibility gate
        src_tier = G.nodes[src].get("tier", 3)
        dst_tier = G.nodes[dst].get("tier", 3)
        if not show_sources and (src_tier in (0, 1, 5, 6) or dst_tier in (0, 1, 5, 6)):
            continue
        if not show_dataflows and (src_tier == 2 or dst_tier == 2):
            continue

        # ── Edge highlight / dim class ──────────────────────────────────────
        if neighborhood:
            if (src, dst) in hl_edges:
                edge_cls = "edge-direct edge-hl" if is_direct else "edge-hl"
            else:
                edge_cls = "edge-dimmed"
        else:
            edge_cls = "edge-direct" if is_direct else "edge-normal"

        elements.append({
            "data": {
                "id":        f"e__{src}__{dst}",
                "source":    src,
                "target":    dst,
                "edge_type": etype,
            },
            "classes": edge_cls,
        })

    return elements


# ---------------------------------------------------------------------------
# Cytoscape stylesheet
# ---------------------------------------------------------------------------

def build_stylesheet(edge_routing: str) -> list[dict]:
    """Build the full Cytoscape.js CSS stylesheet."""

    curve_style = {
        "Orthogonal (taxi)":  "taxi",
        "Curved (bezier)":    "bezier",
        "Straight":           "straight",
    }.get(edge_routing, "bezier")

    edge_base = {
        "curve-style":              curve_style,
        "target-arrow-shape":       "triangle",
        "target-arrow-color":       "#999",
        "line-color":               "#666688",
        "width":                    1.5,
        "arrow-scale":              0.9,
    }
    if curve_style == "bezier":
        # Give each edge a visible arc; parallel edges between the same
        # pair of tiers get automatically separated by Cytoscape.
        edge_base["control-point-step-size"] = 60
    elif curve_style == "taxi":
        edge_base["taxi-direction"] = "horizontal"
        edge_base["taxi-turn"]      = "50%"

    return [
        # ── Base node ──────────────────────────────────────────────────────
        {
            "selector": "node",
            "style": {
                "shape":            "rectangle",
                "label":            "data(label)",
                "font-size":        "11px",
                "font-family":      "monospace, sans-serif",
                "text-valign":      "center",
                "text-halign":      "center",
                "text-wrap":        "wrap",
                "text-max-width":   "120px",
                "color":            "#ffffff",
                "border-width":     1,
                "border-color":     "#444",
                "padding":          "6px",
            },
        },
        # ── Leaf node colors (solid fill) ───────────────────────────────────
        {
            "selector": "node[tier = 1]",   # Database
            "style": {"background-color": TIER_COLORS[1],
                      "font-size": "10px"},
        },
        {
            "selector": "node[tier = 2]",   # Dataflow
            "style": {"background-color": TIER_COLORS[2]},
        },
        {
            "selector": "node[tier = 3]",   # Report
            "style": {"background-color": TIER_COLORS[3]},
        },
        {
            "selector": "node[tier = 5]",   # SharePoint
            "style": {"background-color": TIER_COLORS[5],
                      "font-size": "10px"},
        },
        {
            "selector": "node[tier = 6]",   # API
            "style": {"background-color": TIER_COLORS[6],
                      "font-size": "10px"},
        },

        # ── Sources outer group (dotted border, semi-transparent) ──────────
        {
            "selector": ".group-sources",
            "style": {
                "background-color":   "#0d1117",
                "background-opacity": 0.5,
                "border-color":       TIER_COLORS[0],
                "border-width":       2,
                "border-style":       "dotted",
                "color":              TIER_COLORS[0],
                "font-size":          "13px",
                "font-weight":        "bold",
                "text-valign":        "top",
                "text-halign":        "center",
                "text-margin-y":      -6,
                "padding":            "22px",
            },
        },
        # ── Server sub-group (dashed border) ──────────────────────────────
        {
            "selector": ".group-server",
            "style": {
                "background-color":   "#1c2a3a",
                "background-opacity": 0.6,
                "border-color":       TIER_COLORS[0],
                "border-width":       1.5,
                "border-style":       "dashed",
                "color":              TIER_COLORS[0],
                "font-size":          "11px",
                "font-weight":        "bold",
                "text-valign":        "top",
                "text-halign":        "center",
                "text-margin-y":      -4,
                "padding":            "14px",
            },
        },
        # ── Workspace group (dotted border, teal tint) ────────────────────
        {
            "selector": ".group-workspace",
            "style": {
                "background-color":   "#0d1f1e",
                "background-opacity": 0.5,
                "border-color":       TIER_COLORS[4],
                "border-width":       2,
                "border-style":       "dotted",
                "color":              TIER_COLORS[4],
                "font-size":          "12px",
                "font-weight":        "bold",
                "text-valign":        "top",
                "text-halign":        "center",
                "text-margin-y":      -5,
                "padding":            "18px",
            },
        },

        # ── Edges ──────────────────────────────────────────────────────────
        {
            "selector": "edge",
            "style": edge_base,
        },
        {
            "selector": "edge.edge-direct",
            "style": {
                "line-color":           "#FF6B6B",
                "target-arrow-color":   "#FF6B6B",
                "line-style":           "dashed",
                "width":                1.5,
            },
        },

        # ── Selected state ─────────────────────────────────────────────────
        {
            "selector": "node:selected",
            "style": {
                "border-color":   "#FFD700",
                "border-width":   3,
                "overlay-color":  "#FFD700",
                "overlay-opacity": 0.15,
            },
        },
        {
            "selector": "edge:selected",
            "style": {"line-color": "#FFD700", "width": 3},
        },

        # ── Neighbourhood highlighting ──────────────────────────────────────
        # These rules come last so they override tier-based colors.
        {
            "selector": "node.selected-hl",
            "style": {
                "border-color":    "#FFD700",
                "border-width":    4,
                "overlay-color":   "#FFD700",
                "overlay-opacity": 0.20,
                "opacity":         1,
            },
        },
        {
            "selector": "node.neighbor-hl",
            "style": {
                "border-color":  "#FFD700",
                "border-width":  2,
                "opacity":       1,
            },
        },
        {
            "selector": "node.dimmed",
            "style": {"opacity": 0.12},
        },
        # Highlighted normal edge → gold
        {
            "selector": "edge.edge-hl",
            "style": {
                "line-color":          "#FFD700",
                "target-arrow-color":  "#FFD700",
                "width":               2.5,
                "opacity":             1,
            },
        },
        # Highlighted direct (dashed) edge → gold dashed
        {
            "selector": "edge.edge-hl.edge-direct",
            "style": {
                "line-color":          "#FFD700",
                "target-arrow-color":  "#FFD700",
                "line-style":          "dashed",
                "width":               2.5,
                "opacity":             1,
            },
        },
        # Non-neighbourhood edges → nearly invisible
        {
            "selector": "edge.edge-dimmed",
            "style": {"opacity": 0.07},
        },
    ]


# ---------------------------------------------------------------------------
# Info panel helper
# ---------------------------------------------------------------------------

def render_info_panel(selected: dict | None, G: nx.DiGraph) -> None:
    """
    st-cytoscape returns selected element IDs as plain strings, e.g.:
        {"nodes": ["db::MKCGP"], "edges": ["e__db::MKCGP__df::Date Dimension"]}
    We look up all details from the NetworkX graph.
    """
    st.markdown("### Selection")

    if not selected:
        st.caption("Click a node or edge to see details.")
        return

    # selected["nodes"] and selected["edges"] are lists of ID strings
    node_ids = selected.get("nodes") or []
    edge_ids = selected.get("edges") or []

    if node_ids:
        nid = node_ids[0]  # string ID, e.g. "db::MKCGP"

        # Synthetic compound nodes (e.g. "_sources_group") are not in G
        if nid not in G:
            st.markdown(f"**{nid.lstrip('_').replace('_', ' ').title()}**")
            st.caption("Group container")
            return

        attrs = G.nodes[nid]
        label     = attrs.get("label", nid.split("::")[-1])
        tier_name = attrs.get("tier_name", "")

        st.markdown(f"**{label}**")
        st.caption(f"Type: {tier_name.capitalize()}")

        pbi = attrs.get("pbi_id", "")
        if pbi:
            st.code(pbi, language=None)

        ws = attrs.get("workspace", "")
        if ws:
            st.text(f"Workspace: {ws}")

        srv = attrs.get("server", "")
        if srv:
            st.text(f"Server: {srv}")

        preds = sorted(G.nodes[p].get("label", p) for p in G.predecessors(nid))
        succs = sorted(G.nodes[s].get("label", s) for s in G.successors(nid))
        if preds:
            with st.expander(f"Sources ({len(preds)})"):
                for p in preds:
                    st.write(f"← {p}")
        if succs:
            with st.expander(f"Feeds ({len(succs)})"):
                for s in succs:
                    st.write(f"→ {s}")

    elif edge_ids:
        eid = edge_ids[0]  # string ID, e.g. "e__db::MKCGP__df::Date Dimension"

        # Recover (src, dst) by matching against all edges in the current graph
        src_nid = dst_nid = None
        for src, dst in G.edges():
            if f"e__{src}__{dst}" == eid:
                src_nid, dst_nid = src, dst
                break

        if src_nid and dst_nid:
            src_lbl = G.nodes[src_nid].get("label", src_nid)
            dst_lbl = G.nodes[dst_nid].get("label", dst_nid)
            st.markdown("**Edge**")
            st.text(f"From : {src_lbl}")
            st.text(f"To   : {dst_lbl}")
            etype = G.edges[src_nid, dst_nid].get("edge_type", "")
            if etype:
                st.caption(f"Type: {etype.replace('_', ' ')}")
        else:
            st.caption(f"Edge: {eid}")
    else:
        st.caption("Click a node or edge to see details.")


# ---------------------------------------------------------------------------
# Main Streamlit app
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="MKC PowerBI Lineage Explorer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── Load data ──────────────────────────────────────────────────────────
    G_full = load_graph()

    def _labels(tier_name: str) -> list[str]:
        return sorted(
            G_full.nodes[n]["label"]
            for n in G_full
            if G_full.nodes[n].get("tier_name") == tier_name
        )

    all_workspaces = _labels("workspace")
    all_reports    = _labels("report")
    all_dataflows  = _labels("dataflow")

    # ── Sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## MKC PowerBI Lineage")
        st.caption("Sources → Dataflows → Dashboards")
        st.divider()

        st.subheader("Filters")
        sel_workspaces = st.multiselect(
            "Workspace(s)", all_workspaces, placeholder="All workspaces"
        )
        sel_dataflows = st.multiselect(
            "Dataflow(s)", all_dataflows, placeholder="All dataflows"
        )
        report_search = st.text_input("Search report", placeholder="e.g. Agronomy")

        st.divider()
        st.subheader("Display options")
        show_sources   = st.checkbox("Source systems (Server / DB)", value=True)
        show_dataflows = st.checkbox("Dataflows", value=True)
        show_direct    = st.checkbox("Direct connections (dashed)", value=True)
        group_sources  = st.checkbox("Group sources into container", value=True)
        group_workspaces = st.checkbox("Group reports by workspace", value=True)

        st.divider()
        st.subheader("Edge routing")
        edge_routing = st.selectbox(
            "Style",
            ["Curved (bezier)", "Orthogonal (taxi)", "Straight"],
        )

    # ── Graph filtering ────────────────────────────────────────────────────
    G = G_full

    if sel_workspaces:
        keep: set[str] = set()
        for ws_label in sel_workspaces:
            ws_nid = f"ws::{ws_label}"
            if ws_nid in G:
                keep.add(ws_nid)
                keep |= nx.ancestors(G, ws_nid)
        G = G.subgraph(keep).copy()

    if sel_dataflows:
        keep = set()
        for df_label in sel_dataflows:
            df_nid = f"df::{df_label}"
            if df_nid in G:
                keep.add(df_nid)
                keep |= nx.ancestors(G, df_nid)
                keep |= nx.descendants(G, df_nid)
        G = G.subgraph(keep).copy()

    if report_search.strip():
        term = report_search.strip().lower()
        matching = [
            n for n in G
            if G.nodes[n].get("tier_name") == "report"
            and term in G.nodes[n].get("label", "").lower()
        ]
        if matching:
            keep = set()
            for rpt_nid in matching:
                keep.add(rpt_nid)
                keep |= nx.ancestors(G, rpt_nid)
                keep |= nx.descendants(G, rpt_nid)
            G = G.subgraph(keep).copy()

    # ── Metrics row ────────────────────────────────────────────────────────
    st.markdown("# MKC PowerBI Data Lineage Explorer")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Workspaces", sum(1 for n in G if G.nodes[n].get("tier_name") == "workspace"))
    c2.metric("Reports",    sum(1 for n in G if G.nodes[n].get("tier_name") == "report"))
    c3.metric("Dataflows",  sum(1 for n in G if G.nodes[n].get("tier_name") == "dataflow"))
    c4.metric("Databases",  sum(1 for n in G if G.nodes[n].get("tier_name") == "database"))
    c5.metric("Total nodes", G.number_of_nodes())

    # ── Resolve selected node from previous render cycle ──────────────────
    # st-cytoscape returns IDs after the user clicks; on the first run it
    # is None.  We read it from session_state so the highlight persists
    # across sidebar-driven reruns (filter changes clear the selection).
    if "selected" not in st.session_state:
        st.session_state["selected"] = None

    # ── Build graph elements ───────────────────────────────────────────────
    positions  = compute_positions(G)

    # Determine which node (if any) should drive the neighbourhood highlight.
    prev = st.session_state["selected"]
    sel_nid = (prev.get("nodes") or [None])[0] if isinstance(prev, dict) else None

    elements   = build_elements(
        G, positions,
        group_sources=group_sources,
        group_workspaces=group_workspaces,
        show_sources=show_sources,
        show_dataflows=show_dataflows,
        show_direct=show_direct,
        selected_nid=sel_nid,
    )
    stylesheet = build_stylesheet(edge_routing)
    layout     = {"name": "preset", "fit": True, "padding": 40}

    # ── Main view: graph + info panel ─────────────────────────────────────
    graph_col, info_col = st.columns([5, 1])

    with graph_col:
        selected = cytoscape(
            elements=elements,
            stylesheet=stylesheet,
            layout=layout,
            selection_type="single",
            height="820px",
            width="100%",
            key="lineage_graph",
        )
        # Persist the selection so the next rerun can apply highlight classes
        if selected is not None:
            st.session_state["selected"] = selected

    with info_col:
        render_info_panel(selected, G)

    # ── Legend ─────────────────────────────────────────────────────────────
    with st.expander("Legend", expanded=False):
        cols = st.columns(4)
        items = [
            (TIER_COLORS[1], "Database (SQL)"),
            (TIER_COLORS[2], "Dataflow"),
            (TIER_COLORS[3], "Report"),
            (TIER_COLORS[4], "Workspace (container)"),
            (TIER_COLORS[5], "SharePoint"),
            (TIER_COLORS[6], "API"),
            ("#666688",      "Normal edge (via dataflow)"),
            ("#FF6B6B",      "Direct connection (no dataflow)"),
        ]
        for i, (color, label) in enumerate(items):
            with cols[i % 4]:
                st.markdown(
                    f'<span style="display:inline-block;width:14px;height:14px;'
                    f'background:{color};border-radius:2px;margin-right:6px;'
                    f'vertical-align:middle"></span>{label}',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
