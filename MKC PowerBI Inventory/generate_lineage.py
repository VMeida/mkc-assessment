"""
PowerBI Data Lineage Diagram Generator
=======================================
Reads MKC PowerBI Inventory Excel file and produces:
  1. lineage_output/lineage.png/.svg  – static matplotlib diagram
  2. lineage_output/lineage.gv        – Graphviz DOT source
  3. lineage_output/lineage_interactive.html – pyvis interactive HTML

Usage:
    python generate_lineage.py --input "MKC PowerBI Inventory (1).xlsx"
    python generate_lineage.py --input FILE --workspace "Sales"
    python generate_lineage.py --input FILE --report "Agronomy Scorecard"
    python generate_lineage.py --input FILE --format pyvis
"""

import argparse
import os
import sys
import textwrap
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_COLORS = {
    0: "#4E79A7",   # Server       – steel blue
    1: "#F28E2B",   # Database     – orange
    2: "#59A14F",   # Dataflow     – green
    3: "#E15759",   # Report       – red-pink
    4: "#76B7B2",   # Workspace    – teal
    5: "#B07AA1",   # SharePoint   – purple
    6: "#FF9DA7",   # API          – light red
}

TIER_LABELS = {
    0: "Server",
    1: "Database",
    2: "Dataflow",
    3: "Report",
    4: "Workspace",
    5: "SharePoint",
    6: "API",
}

TIER_ORDER = {
    "server":     0,
    "database":   1,
    "dataflow":   2,
    "report":     3,
    "workspace":  4,
    "sharepoint": 5,
    "api":        6,
}

# Graphviz shapes (used only for .dot file generation)
DOT_SHAPES = {
    0: "cylinder",
    1: "folder",
    2: "parallelogram",
    3: "box",
    4: "doubleoctagon",
    5: "note",
    6: "diamond",
}

# matplotlib marker sizes per tier
MARKER_SIZES = {
    0: 3000,
    1: 2500,
    2: 2000,
    3: 1500,
    4: 3000,
    5: 2000,
    6: 2000,
}


# ---------------------------------------------------------------------------
# 1. I/O
# ---------------------------------------------------------------------------

def load_excel(path: str):
    """Read both sheets from the Excel file. No transformation here."""
    df1 = pd.read_excel(path, sheet_name="Source Mapping", header=0, dtype=str)
    df2 = pd.read_excel(path, sheet_name="DFW Lineage", header=0, dtype=str)
    return df1, df2


# ---------------------------------------------------------------------------
# 2. Normalisation
# ---------------------------------------------------------------------------

def normalize_df1(df1: pd.DataFrame) -> pd.DataFrame:
    """Clean and classify Source Mapping rows."""
    # Keep only the first 7 columns (the extra Workspace/Server cols are duplicates)
    df1 = df1.iloc[:, :7].copy()
    df1.columns = ["workspace", "report", "conn_type", "path_or_df", "server", "db", "table"]

    for col in df1.columns:
        df1[col] = df1[col].astype(str).str.strip()

    # Replace Excel error strings with empty
    for err in ("#N/A", "#REF!", "#VALUE!", "nan"):
        df1.replace(err, "", inplace=True)

    df1["server"] = df1["server"].str.upper()
    df1["db"]     = df1["db"].str.upper()
    df1["conn_type_lower"] = df1["conn_type"].str.lower()

    df1["is_dataflow"]   = df1["conn_type_lower"].str.startswith("dataflow")
    df1["is_sharepoint"] = df1["conn_type_lower"].isin(["sharepointlist", "sharepoint"])
    df1["is_api"]        = df1["conn_type_lower"] == "api"
    df1["is_direct_sql"] = (
        ~df1["is_dataflow"] & ~df1["is_sharepoint"] & ~df1["is_api"] &
        df1["server"].str.len().gt(0) &
        ~df1["server"].isin(["0", ""])
    )

    # Rows with server='0' / db='0' are actually SharePoint – reclassify
    mask_fake_sql = (df1["server"] == "0") | (df1["db"] == "0")
    df1.loc[mask_fake_sql & ~df1["is_dataflow"], "is_sharepoint"] = True
    df1.loc[mask_fake_sql & ~df1["is_dataflow"], "is_direct_sql"] = False

    # Warn about unknown workspaces
    unknown_ws = df1[df1["workspace"] == ""]["report"].unique()
    if len(unknown_ws):
        print(f"[WARN] {len(unknown_ws)} report(s) have no workspace in Sheet1: "
              f"{list(unknown_ws[:5])}{'...' if len(unknown_ws)>5 else ''}")

    return df1


def normalize_df2(df2: pd.DataFrame) -> pd.DataFrame:
    """Clean DFW Lineage and build lookup dicts as attributes."""
    # Flexible column rename: use positional order
    cols = ["workspace_id", "workspace", "report_id", "report",
            "dataset_id", "dataset", "dataflow_id", "dataflow"]
    df2 = df2.iloc[:, :8].copy()
    df2.columns = cols[:df2.shape[1]]

    for col in df2.columns:
        df2[col] = df2[col].astype(str).str.strip()
    df2.replace({"nan": "", "#N/A": "", "#REF!": ""}, inplace=True)

    return df2


def build_lookup_dicts(df2: pd.DataFrame):
    """Extract mapping dicts from DFW Lineage."""
    # dataflow_name -> UUID
    df_has_df = df2[df2["dataflow"].str.len() > 0]
    dataflow_id_map = (
        df_has_df.groupby("dataflow")["dataflow_id"].first().to_dict()
        if "dataflow_id" in df2.columns else {}
    )

    # report_name -> set of workspace names (Sheet2 is source of truth)
    report_workspace_map = (
        df2[df2["workspace"].str.len() > 0]
        .groupby("report")["workspace"]
        .apply(set)
        .to_dict()
    )

    # report_name -> set of dataflow names (Sheet2 direct mapping)
    df_report_df = df2[df2["dataflow"].str.len() > 0]
    report_dataflow_map = (
        df_report_df.groupby("report")["dataflow"]
        .apply(set)
        .to_dict()
    )

    return dataflow_id_map, report_workspace_map, report_dataflow_map


# ---------------------------------------------------------------------------
# 3. Graph Construction
# ---------------------------------------------------------------------------

def _nid(tier_prefix: str, name: str) -> str:
    """Create a collision-safe node ID."""
    return f"{tier_prefix}::{name}"


def add_source_nodes(G: nx.DiGraph, df1: pd.DataFrame):
    """Add Server, Database, SharePoint, and API nodes."""
    # SQL Servers
    servers = df1[df1["server"].str.len() > 0]["server"].unique()
    for srv in servers:
        if srv in ("0", ""):
            continue
        nid = _nid("srv", srv)
        if nid not in G:
            G.add_node(nid, label=srv, tier=0, tier_name="server",
                       source_type="sql")

    # Databases (keyed by server+db combination, labelled as just db)
    sql_rows = df1[df1["server"].str.len() > 0]
    for _, row in sql_rows.iterrows():
        srv, db = row["server"], row["db"]
        if not db or db == "0":
            continue
        nid = _nid("db", db)
        if nid not in G:
            G.add_node(nid, label=db, tier=1, tier_name="database",
                       source_type="sql", server=srv)

    # SharePoint – aggregate into one node
    sp_rows = df1[df1["is_sharepoint"]]
    if len(sp_rows):
        nid = _nid("sp", "SharePoint")
        if nid not in G:
            G.add_node(nid, label="SharePoint", tier=5,
                       tier_name="sharepoint", source_type="sharepoint")

    # API – aggregate into one node
    api_rows = df1[df1["is_api"]]
    if len(api_rows):
        nid = _nid("api", "External API")
        if nid not in G:
            G.add_node(nid, label="External API", tier=6,
                       tier_name="api", source_type="api")


def add_dataflow_nodes(G: nx.DiGraph, df1: pd.DataFrame,
                       dataflow_id_map: dict):
    """Add Dataflow nodes."""
    df_rows = df1[df1["is_dataflow"]]
    for df_name in df_rows["path_or_df"].unique():
        if not df_name:
            continue
        nid = _nid("df", df_name)
        if nid not in G:
            pbi_id = dataflow_id_map.get(df_name, "")
            G.add_node(nid, label=df_name, tier=2, tier_name="dataflow",
                       pbi_id=pbi_id)


def add_report_nodes(G: nx.DiGraph, df2: pd.DataFrame,
                     report_workspace_map: dict):
    """Add Report nodes (using Sheet2 as source of truth for coverage)."""
    for rpt in df2["report"].unique():
        if not rpt:
            continue
        nid = _nid("rpt", rpt)
        if nid not in G:
            ws_set = report_workspace_map.get(rpt, set())
            ws = next(iter(ws_set), "")
            G.add_node(nid, label=rpt, tier=3, tier_name="report",
                       workspace=ws)


def add_workspace_nodes(G: nx.DiGraph, df2: pd.DataFrame):
    """Add Workspace nodes."""
    for ws in df2["workspace"].unique():
        if not ws:
            continue
        nid = _nid("ws", ws)
        if nid not in G:
            G.add_node(nid, label=ws, tier=4, tier_name="workspace")


def _add_edge_safe(G, src, dst, **attrs):
    """Add edge only if both nodes exist."""
    if src in G and dst in G:
        if G.has_edge(src, dst):
            G[src][dst]["weight"] = G[src][dst].get("weight", 1) + 1
        else:
            G.add_edge(src, dst, weight=1, **attrs)


def add_all_edges(G: nx.DiGraph, df1: pd.DataFrame, df2: pd.DataFrame,
                  report_dataflow_map: dict):
    """Wire up all edges for every tier."""
    # ---- Dataflow rows: DB -> Dataflow -> Report ----
    df_rows = df1[df1["is_dataflow"]].copy()
    for _, row in df_rows.iterrows():
        df_nid = _nid("df", row["path_or_df"])
        rpt_nid = _nid("rpt", row["report"])
        srv_nid = _nid("srv", row["server"]) if row["server"] else None
        db_nid  = _nid("db",  row["db"])     if row["db"] and row["db"] != "0" else None

        if srv_nid and db_nid:
            _add_edge_safe(G, srv_nid, db_nid, edge_type="server_to_db")
            _add_edge_safe(G, db_nid,  df_nid, edge_type="db_to_dataflow")
        elif db_nid:
            _add_edge_safe(G, db_nid, df_nid, edge_type="db_to_dataflow")

        _add_edge_safe(G, df_nid, rpt_nid, edge_type="dataflow_to_report")

    # ---- Direct SQL rows: DB -> Report ----
    direct_rows = df1[df1["is_direct_sql"]].copy()
    for _, row in direct_rows.iterrows():
        rpt_nid = _nid("rpt", row["report"])
        srv_nid = _nid("srv", row["server"]) if row["server"] else None
        db_nid  = _nid("db",  row["db"])     if row["db"] and row["db"] != "0" else None

        if srv_nid and db_nid:
            _add_edge_safe(G, srv_nid, db_nid,  edge_type="server_to_db")
        if db_nid:
            _add_edge_safe(G, db_nid,  rpt_nid, edge_type="direct_to_report")
        elif srv_nid:
            _add_edge_safe(G, srv_nid, rpt_nid, edge_type="direct_to_report")

    # ---- SharePoint rows: SharePoint -> Report ----
    sp_rows = df1[df1["is_sharepoint"]]
    sp_nid = _nid("sp", "SharePoint")
    for rpt in sp_rows["report"].unique():
        if rpt:
            _add_edge_safe(G, sp_nid, _nid("rpt", rpt),
                           edge_type="sharepoint_to_report")

    # ---- API rows: API -> Report ----
    api_rows = df1[df1["is_api"]]
    api_nid = _nid("api", "External API")
    for rpt in api_rows["report"].unique():
        if rpt:
            _add_edge_safe(G, api_nid, _nid("rpt", rpt),
                           edge_type="api_to_report")

    # ---- Report -> Workspace (from Sheet2) ----
    for _, row in df2.iterrows():
        rpt = row["report"]
        ws  = row["workspace"]
        if rpt and ws:
            _add_edge_safe(G, _nid("rpt", rpt), _nid("ws", ws),
                           edge_type="report_to_workspace")


def build_graph(df1: pd.DataFrame, df2: pd.DataFrame) -> nx.DiGraph:
    """Build the full NetworkX DiGraph from both DataFrames."""
    dataflow_id_map, report_workspace_map, report_dataflow_map = build_lookup_dicts(df2)

    G = nx.DiGraph()
    add_source_nodes(G, df1)
    add_dataflow_nodes(G, df1, dataflow_id_map)
    add_report_nodes(G, df2, report_workspace_map)
    add_workspace_nodes(G, df2)
    add_all_edges(G, df1, df2, report_dataflow_map)

    print(f"[INFO] Graph built: {G.number_of_nodes()} nodes, "
          f"{G.number_of_edges()} edges")
    return G


# ---------------------------------------------------------------------------
# 4. Filtering
# ---------------------------------------------------------------------------

def filter_graph(G: nx.DiGraph, workspace: str = None,
                 report: str = None) -> nx.DiGraph:
    """Return a subgraph containing only nodes relevant to the filter."""
    if not workspace and not report:
        return G

    keep = set()

    if report:
        rpt_nid = _nid("rpt", report)
        if rpt_nid not in G:
            print(f"[WARN] Report '{report}' not found in graph.")
            return G
        keep.add(rpt_nid)
        keep |= nx.ancestors(G, rpt_nid)
        keep |= nx.descendants(G, rpt_nid)

    if workspace:
        ws_nid = _nid("ws", workspace)
        if ws_nid not in G:
            print(f"[WARN] Workspace '{workspace}' not found in graph.")
            return G
        keep.add(ws_nid)
        keep |= nx.ancestors(G, ws_nid)

    return G.subgraph(keep).copy()


# ---------------------------------------------------------------------------
# 5. Rendering – Matplotlib static diagram
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int = 18) -> str:
    return "\n".join(textwrap.wrap(text, width))


def render_matplotlib(G: nx.DiGraph, output_dir: Path,
                      title: str = "MKC PowerBI Data Lineage"):
    """Draw the graph using networkx multipartite layout + matplotlib."""
    if G.number_of_nodes() == 0:
        print("[WARN] Empty graph – skipping matplotlib render.")
        return

    # Assign subset key = tier for multipartite_layout
    # SP and API nodes (tier 5,6) are placed at tier 0 column (source side)
    for n, d in G.nodes(data=True):
        tier = d.get("tier", 3)
        d["subset"] = min(tier, 4)   # collapse SP/API into column 0 visually

    # Compute layout
    pos = nx.multipartite_layout(G, subset_key="subset", align="vertical",
                                 scale=3.0)

    # Jitter nodes in same tier slightly so labels don't stack exactly
    from collections import defaultdict
    tier_counts: dict = defaultdict(int)
    for n, (x, y) in pos.items():
        tier_counts[round(x, 2)] += 1

    fig_height = max(14, G.number_of_nodes() * 0.28)
    fig_width  = max(24, fig_height * 1.6)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.axis("off")

    # Draw edges first (behind nodes)
    direct_edge_types = {"direct_to_report", "sharepoint_to_report",
                         "api_to_report"}

    edge_norm  = [(u, v) for u, v, d in G.edges(data=True)
                  if d.get("edge_type") not in direct_edge_types]
    edge_direct = [(u, v) for u, v, d in G.edges(data=True)
                   if d.get("edge_type") in direct_edge_types]

    nx.draw_networkx_edges(G, pos, edgelist=edge_norm, ax=ax,
                           edge_color="#BBBBBB", arrows=True,
                           arrowsize=10, width=0.7,
                           connectionstyle="arc3,rad=0.05",
                           min_source_margin=12, min_target_margin=12)

    nx.draw_networkx_edges(G, pos, edgelist=edge_direct, ax=ax,
                           edge_color="#FF6B6B", style="dashed", arrows=True,
                           arrowsize=10, width=0.8,
                           connectionstyle="arc3,rad=0.05",
                           min_source_margin=12, min_target_margin=12)

    # Draw nodes grouped by tier
    for tier_val in sorted(set(d.get("tier", 3) for _, d in G.nodes(data=True))):
        nodes_in_tier = [n for n, d in G.nodes(data=True)
                         if d.get("tier") == tier_val]
        color  = TIER_COLORS.get(tier_val, "#AAAAAA")
        msize  = MARKER_SIZES.get(tier_val, 1500)
        nx.draw_networkx_nodes(G, pos, nodelist=nodes_in_tier, ax=ax,
                               node_color=color, node_size=msize,
                               alpha=0.92)

    # Labels
    labels = {n: _wrap(d.get("label", n.split("::")[-1]), 16)
              for n, d in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=5.5, font_color="white",
                            font_weight="bold")

    # Legend
    legend_items = []
    present_tiers = sorted(set(d.get("tier", 3) for _, d in G.nodes(data=True)))
    for t in present_tiers:
        patch = mpatches.Patch(color=TIER_COLORS.get(t, "#AAA"),
                               label=TIER_LABELS.get(t, "Unknown"))
        legend_items.append(patch)
    # Add edge-type legend
    legend_items.append(
        mpatches.Patch(color="#BBBBBB", label="Via Dataflow (normal)"))
    legend_items.append(
        mpatches.Patch(color="#FF6B6B", linestyle="--",
                       label="Direct DB / SP / API connection"))
    ax.legend(handles=legend_items, loc="upper left",
              fontsize=8, framealpha=0.8)

    plt.tight_layout()
    png_path = output_dir / "lineage.png"
    svg_path = output_dir / "lineage.svg"
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.savefig(svg_path, bbox_inches="tight")
    plt.close()
    print(f"[OK] Static diagram → {png_path}")
    print(f"[OK] Static diagram → {svg_path}")


# ---------------------------------------------------------------------------
# 6. Rendering – Graphviz DOT source file
# ---------------------------------------------------------------------------

def render_dot(G: nx.DiGraph, output_dir: Path):
    """Write a Graphviz .gv source file (no binary required)."""
    lines = [
        "digraph mkc_lineage {",
        "  rankdir=LR;",
        "  splines=ortho;",
        "  nodesep=0.4;",
        "  ranksep=1.5;",
        "  node [fontname=\"Helvetica\" fontsize=10 style=filled];",
        "",
    ]

    # Group nodes by tier for rank= same hints
    from collections import defaultdict
    tiers: dict = defaultdict(list)
    for nid, attrs in G.nodes(data=True):
        tiers[attrs.get("tier", 3)].append(nid)

    for tier_val, node_list in sorted(tiers.items()):
        color = TIER_COLORS.get(tier_val, "#AAAAAA")
        shape = DOT_SHAPES.get(tier_val, "box")
        lines.append(f"  // --- Tier {tier_val}: {TIER_LABELS.get(tier_val)} ---")
        lines.append("  {")
        lines.append("    rank=same;")
        for nid in node_list:
            attrs = G.nodes[nid]
            label = attrs.get("label", nid.split("::")[-1]).replace('"', "'")
            pbi   = attrs.get("pbi_id", "")
            tooltip = f"Tier: {TIER_LABELS.get(tier_val, '')}"
            if pbi:
                tooltip += f"\\nPBI ID: {pbi}"
            safe_nid = nid.replace("::", "__").replace(" ", "_").replace("-", "_")
            lines.append(
                f'    "{safe_nid}" [label="{label}" shape={shape} '
                f'fillcolor="{color}" fontcolor="white" tooltip="{tooltip}"];'
            )
        lines.append("  }")
        lines.append("")

    # Edges
    direct_types = {"direct_to_report", "sharepoint_to_report", "api_to_report"}
    lines.append("  // --- Edges ---")
    for src, dst, attrs in G.edges(data=True):
        safe_src = src.replace("::", "__").replace(" ", "_").replace("-", "_")
        safe_dst = dst.replace("::", "__").replace(" ", "_").replace("-", "_")
        etype = attrs.get("edge_type", "")
        style = ' style=dashed color="#FF6B6B"' if etype in direct_types else ' color="#999999"'
        lines.append(f'  "{safe_src}" -> "{safe_dst}" [{style}];')

    lines.append("}")

    dot_path = output_dir / "lineage.gv"
    dot_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Graphviz DOT source → {dot_path}")
    print(f"     (Render with: dot -Tpng lineage.gv -o lineage_gv.png)")
    print(f"     (Or paste into https://dreampuf.github.io/GraphvizOnline)")


# ---------------------------------------------------------------------------
# 7. Rendering – Pyvis interactive HTML
# ---------------------------------------------------------------------------

def build_tooltip(attrs: dict, G: nx.DiGraph, nid: str) -> str:
    """Build HTML tooltip string for a node."""
    tier_name = attrs.get("tier_name", "")
    label     = attrs.get("label", nid.split("::")[-1])
    parts = [f"<b>{label}</b>", f"<i>Tier: {tier_name}</i>"]

    pbi_id = attrs.get("pbi_id", "")
    if pbi_id:
        parts.append(f"PBI ID: {pbi_id}")

    workspace = attrs.get("workspace", "")
    if workspace:
        parts.append(f"Workspace: {workspace}")

    # Predecessor and successor counts
    preds = list(G.predecessors(nid))
    succs = list(G.successors(nid))
    if preds:
        pred_labels = [G.nodes[p].get("label", p.split("::")[-1])
                       for p in preds[:5]]
        parts.append(f"Sources: {', '.join(pred_labels)}"
                     + ("..." if len(preds) > 5 else ""))
    if succs:
        succ_labels = [G.nodes[s].get("label", s.split("::")[-1])
                       for s in succs[:5]]
        parts.append(f"Feeds: {', '.join(succ_labels)}"
                     + ("..." if len(succs) > 5 else ""))

    return "<br>".join(parts)


def render_pyvis(G: nx.DiGraph, output_dir: Path):
    """Generate an interactive HTML with pyvis hierarchical layout."""
    try:
        from pyvis.network import Network
    except ImportError:
        print("[SKIP] pyvis not installed – skipping interactive HTML.")
        return

    if G.number_of_nodes() == 0:
        print("[WARN] Empty graph – skipping pyvis render.")
        return

    net = Network(
        height="95vh", width="100%", directed=True,
        heading="MKC PowerBI Data Lineage – Interactive",
        bgcolor="#1a1a2e", font_color="#e0e0e0",
    )

    # Hierarchical layout options
    net.set_options("""{
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "LR",
          "sortMethod": "directed",
          "levelSeparation": 300,
          "nodeSpacing": 100,
          "treeSpacing": 200,
          "blockShifting": true,
          "edgeMinimization": true,
          "parentCentralization": true
        }
      },
      "physics": {"enabled": false},
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": {"enabled": true},
        "zoomView": true
      },
      "edges": {
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.6}},
        "smooth": {"enabled": false}
      },
      "nodes": {
        "font": {"size": 11, "face": "monospace"},
        "borderWidth": 1,
        "shadow": {"enabled": true}
      }
    }""")

    direct_types = {"direct_to_report", "sharepoint_to_report",
                    "api_to_report"}

    for nid, attrs in G.nodes(data=True):
        tier  = attrs.get("tier", 3)
        color = TIER_COLORS.get(tier, "#AAAAAA")
        label = attrs.get("label", nid.split("::")[-1])
        short = (label[:24] + "…") if len(label) > 25 else label

        net.add_node(
            nid,
            label=short,
            level=min(tier, 4),
            color={"background": color, "border": "#ffffff",
                   "highlight": {"background": "#FFD700", "border": "#FF6600"}},
            title=build_tooltip(attrs, G, nid),
            shape="box",
            margin={"top": 6, "bottom": 6, "left": 8, "right": 8},
        )

    for src, dst, eattrs in G.edges(data=True):
        etype  = eattrs.get("edge_type", "")
        is_dir = etype in direct_types
        net.add_edge(
            src, dst,
            color={"color": "#FF6B6B" if is_dir else "#666688",
                   "highlight": "#FFD700"},
            dashes=is_dir,
            width=1.5 if is_dir else 1,
        )

    html_path = output_dir / "lineage_interactive.html"
    net.write_html(str(html_path))
    print(f"[OK] Interactive diagram → {html_path}")


# ---------------------------------------------------------------------------
# 8. CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate PowerBI data lineage diagrams from Excel inventory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python generate_lineage.py --input "MKC PowerBI Inventory (1).xlsx"
          python generate_lineage.py --input FILE --workspace "Sales"
          python generate_lineage.py --input FILE --report "Agronomy Scorecard"
          python generate_lineage.py --input FILE --format pyvis
        """),
    )
    p.add_argument("--input", "-i", required=True,
                   help="Path to the Excel inventory file")
    p.add_argument("--output-dir", "-o", default="lineage_output",
                   help="Directory for output files (default: lineage_output)")
    p.add_argument("--workspace", "-w", default=None,
                   help="Filter to a single workspace by name")
    p.add_argument("--report", "-r", default=None,
                   help="Filter to a single report by name")
    p.add_argument("--format", "-f", choices=["matplotlib", "pyvis", "dot", "all"],
                   default="all",
                   help="Output format(s) to generate (default: all)")
    return p.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading {input_path} …")
    df1, df2 = load_excel(str(input_path))

    print("[INFO] Normalizing data …")
    df1 = normalize_df1(df1)
    df2 = normalize_df2(df2)

    print("[INFO] Building graph …")
    G = build_graph(df1, df2)

    # Apply filter
    G_render = filter_graph(G, workspace=args.workspace, report=args.report)
    suffix = ""
    if args.workspace:
        suffix = f" – Workspace: {args.workspace}"
    elif args.report:
        suffix = f" – Report: {args.report}"

    n_nodes = G_render.number_of_nodes()
    n_edges = G_render.number_of_edges()
    print(f"[INFO] Rendering graph ({n_nodes} nodes, {n_edges} edges) …")

    fmt = args.format
    if fmt in ("matplotlib", "all"):
        render_matplotlib(G_render, output_dir,
                          title=f"MKC PowerBI Data Lineage{suffix}")
    if fmt in ("dot", "all"):
        render_dot(G_render, output_dir)
    if fmt in ("pyvis", "all"):
        render_pyvis(G_render, output_dir)

    print(f"\n[DONE] Outputs written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
