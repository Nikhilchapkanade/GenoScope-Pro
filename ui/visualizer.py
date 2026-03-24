# ui/visualizer.py
import py3Dmol
from stmol import showmol
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
import streamlit as st
import streamlit.components.v1 as components
import tempfile
import os


# ═══════════════════════════════════════════════════════════════
# 1.  ORIGINAL 3D STRUCTURE VIEWS
# ═══════════════════════════════════════════════════════════════

def render_3d_structure(pdb_data: str, mutation: str = None):
    """Renders the interactive 3D molecule — cartoon mode."""
    if not pdb_data:
        return

    view = py3Dmol.view(width=800, height=600)
    view.addModel(pdb_data, "pdb")
    view.setStyle({"cartoon": {"color": "spectrum"}})
    view.zoomTo()

    if mutation:
        m = re.match(r"[A-Z](\d+)[A-Z]", mutation.upper())
        if m:
            pos = int(m.group(1))
            view.addStyle({"resi": str(pos)}, {"stick": {"color": "red", "radius": 0.3}})
            view.zoomTo({"resi": str(pos)})

    showmol(view, height=600, width=800)


def render_surface_view(pdb_data: str, mutation: str = None):
    """Renders protein as a translucent surface with mutation highlighted."""
    if not pdb_data:
        return

    view = py3Dmol.view(width=800, height=600)
    view.addModel(pdb_data, "pdb")

    # Translucent surface with spectrum coloring
    view.addSurface(
        py3Dmol.VDW,
        {"opacity": 0.7, "colorscheme": {"prop": "b", "gradient": "roygb", "min": 0, "max": 100}}
    )

    # Highlight mutation site as a solid red sphere
    if mutation:
        m = re.match(r"[A-Z](\d+)[A-Z]", mutation.upper())
        if m:
            pos = int(m.group(1))
            view.addStyle(
                {"resi": str(pos)},
                {"sphere": {"color": "#ff2255", "radius": 1.5}}
            )
            view.addLabel(
                f"Mut: {mutation.upper()}",
                {
                    "position": {"resi": str(pos)},
                    "backgroundColor": "#1a1a2e",
                    "fontColor": "#ff2255",
                    "fontSize": 14,
                    "borderRadius": 8,
                },
            )
            view.zoomTo({"resi": str(pos)})
    else:
        view.zoomTo()

    showmol(view, height=600, width=800)


def render_comparison_3d(pdb_data: str, mutation: str = None):
    """Side-by-side wild-type vs mutant comparison views."""
    if not pdb_data:
        return

    col_wt, col_mut = st.columns(2)

    with col_wt:
        st.markdown("#### 🟢 Wild-Type")
        view_wt = py3Dmol.view(width=450, height=500)
        view_wt.addModel(pdb_data, "pdb")
        view_wt.setStyle({"cartoon": {"color": "spectrum"}})
        if mutation:
            m = re.match(r"[A-Z](\d+)[A-Z]", mutation.upper())
            if m:
                pos = int(m.group(1))
                view_wt.addStyle(
                    {"resi": str(pos)},
                    {"stick": {"color": "#00ff88", "radius": 0.25}}
                )
                view_wt.addLabel(
                    f"WT: pos {pos}",
                    {
                        "position": {"resi": str(pos)},
                        "backgroundColor": "#0a2a1a",
                        "fontColor": "#00ff88",
                        "fontSize": 12,
                        "borderRadius": 6,
                    },
                )
                view_wt.zoomTo({"resi": str(pos)})
        else:
            view_wt.zoomTo()
        showmol(view_wt, height=500, width=450)

    with col_mut:
        st.markdown("#### 🔴 Mutant Highlight")
        view_mut = py3Dmol.view(width=450, height=500)
        view_mut.addModel(pdb_data, "pdb")

        # Show cartoon in grey for contrast
        view_mut.setStyle({"cartoon": {"color": "#555555"}})

        # Add surface around mutation site
        if mutation:
            m = re.match(r"[A-Z](\d+)[A-Z]", mutation.upper())
            if m:
                pos = int(m.group(1))
                # Highlight the mutant residue
                view_mut.addStyle(
                    {"resi": str(pos)},
                    {"stick": {"color": "#ff2255", "radius": 0.4}}
                )
                # Add a translucent surface around the mutation
                view_mut.addSurface(
                    py3Dmol.VDW,
                    {"opacity": 0.4, "color": "#ff2255"},
                    {"resi": str(pos)}
                )
                # Neighbouring residues (±5) glow
                for offset in range(-5, 6):
                    if offset == 0:
                        continue
                    view_mut.addStyle(
                        {"resi": str(pos + offset)},
                        {"cartoon": {"color": "#ff8866"}}
                    )
                view_mut.addLabel(
                    f"MUT: {mutation.upper()}",
                    {
                        "position": {"resi": str(pos)},
                        "backgroundColor": "#2a0a1a",
                        "fontColor": "#ff2255",
                        "fontSize": 14,
                        "borderRadius": 6,
                    },
                )
                view_mut.zoomTo({"resi": str(pos)})
        else:
            view_mut.zoomTo()
        showmol(view_mut, height=500, width=450)


def plot_plddt_confidence(pdb_data: str):
    """Extracts B-factors (pLDDT) and plots confidence graph."""
    if not pdb_data:
        return

    lines = pdb_data.splitlines()
    res_plddt = {}
    for line in lines:
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            resnum = int(line[22:26].strip())
            plddt = float(line[60:66])
            res_plddt[resnum] = plddt

    if not res_plddt:
        return

    df = pd.DataFrame(list(res_plddt.items()), columns=['Residue', 'pLDDT'])

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Residue"], df["pLDDT"], color='blue', linewidth=1)
    ax.axhline(y=90, color='green', linestyle='--', alpha=0.5)
    ax.axhline(y=70, color='orange', linestyle='--', alpha=0.5)
    ax.axhline(y=50, color='red', linestyle='--', alpha=0.5)
    ax.set_title("AlphaFold Confidence (pLDDT) per Residue")
    ax.set_xlabel("Residue ID")
    ax.set_ylabel("Confidence Score")

    st.pyplot(fig)


# ═══════════════════════════════════════════════════════════════
# 2.  MULTI-MUTATION HEATMAP
# ═══════════════════════════════════════════════════════════════

def render_mutation_heatmap(scores_dict: dict):
    """Renders a Plotly heatmap of mutation scores.
    
    scores_dict: {mutation_str: delta_score} e.g. {'R273H': -1.2, 'G245S': -0.4}
    """
    if not scores_dict:
        st.warning("No scores to display.")
        return

    mutations = list(scores_dict.keys())
    scores = [v if v is not None else 0 for v in scores_dict.values()]

    # Sort by score
    paired = sorted(zip(mutations, scores), key=lambda x: x[1])
    mutations = [p[0] for p in paired]
    scores = [p[1] for p in paired]

    # Bar chart
    colors = []
    for s in scores:
        if s < -0.5:
            colors.append("#ff2255")
        elif s < 0:
            colors.append("#ff8844")
        else:
            colors.append("#00cc66")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=mutations,
        y=scores,
        marker_color=colors,
        text=[f"{s:.3f}" for s in scores],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Delta Score: %{y:.4f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text="🧬 Mutation Pathogenicity Scores",
            font=dict(size=20, color="#e0e0e0"),
        ),
        xaxis_title="Mutation",
        yaxis_title="Delta Score (log-likelihood ratio)",
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#c0c0c0"),
        yaxis=dict(zeroline=True, zerolinecolor="#555555"),
        height=450,
    )

    # Add threshold annotations
    fig.add_hline(y=-0.5, line_dash="dash", line_color="#ff2255",
                  annotation_text="Deleterious threshold", annotation_position="top left")
    fig.add_hline(y=0, line_dash="dot", line_color="#888888")

    st.plotly_chart(fig, use_container_width=True)


def render_position_heatmap(scan_results: dict, position: int, wt_aa: str):
    """Renders a detailed heatmap for all amino acid substitutions at one position.
    
    scan_results: {amino_acid: delta_score}
    """
    if not scan_results:
        st.warning("No scan data.")
        return

    amino_acids = sorted(scan_results.keys())
    scores = [scan_results[aa] if scan_results[aa] is not None else 0 for aa in amino_acids]

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=[scores],
        x=amino_acids,
        y=[f"Pos {position} ({wt_aa})"],
        colorscale=[
            [0.0, "#ff2255"],
            [0.4, "#ff8844"],
            [0.5, "#ffcc00"],
            [0.7, "#88cc44"],
            [1.0, "#00cc66"],
        ],
        text=[[f"{s:.3f}" for s in scores]],
        texttemplate="%{text}",
        hovertemplate="<b>%{x}</b><br>Score: %{z:.4f}<extra></extra>",
        colorbar=dict(title="Score", tickfont=dict(color="#c0c0c0")),
    ))

    fig.update_layout(
        title=dict(
            text=f"🔬 Amino Acid Substitution Scan — Position {position} (WT: {wt_aa})",
            font=dict(size=18, color="#e0e0e0"),
        ),
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#c0c0c0"),
        height=250,
        xaxis_title="Substituted Amino Acid",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_batch_summary_table(scores_dict: dict):
    """Renders a styled summary table of batch mutation results."""
    if not scores_dict:
        return

    rows = []
    for mut, score in scores_dict.items():
        if score is None:
            severity = "⚪ Error"
            score_val = "N/A"
        elif score < -0.5:
            severity = "🔴 Likely Deleterious"
            score_val = f"{score:.4f}"
        elif score < 0:
            severity = "🟠 Possibly Harmful"
            score_val = f"{score:.4f}"
        else:
            severity = "🟢 Likely Benign"
            score_val = f"{score:.4f}"
        rows.append({"Mutation": mut, "Delta Score": score_val, "Verdict": severity})

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# 3.  PROTEIN-PROTEIN INTERACTION NETWORK
# ═══════════════════════════════════════════════════════════════

def render_interaction_network(gene_name: str, interactions: list):
    """Renders an interactive protein interaction network using pyvis."""
    if not interactions:
        st.warning("No interaction data found.")
        return

    from pyvis.network import Network

    net = Network(
        height="600px",
        width="100%",
        bgcolor="#0e1117",
        font_color="#e0e0e0",
        directed=False,
    )

    # Physics for nice layout
    net.barnes_hut(
        gravity=-3000,
        central_gravity=0.3,
        spring_length=150,
        spring_strength=0.05,
    )

    # Collect all unique nodes
    all_nodes = set()
    for edge in interactions:
        all_nodes.add(edge["source"])
        all_nodes.add(edge["target"])

    # Add nodes with styling
    for node in all_nodes:
        if node.upper() == gene_name.upper():
            # Query gene — large red node
            net.add_node(
                node,
                label=node,
                color="#ff2255",
                size=40,
                font={"size": 18, "color": "#ffffff", "bold": True},
                borderWidth=3,
                borderWidthSelected=5,
                shape="dot",
                title=f"🎯 Query Gene: {node}",
            )
        else:
            # Partner — scaled by interaction score
            max_score = max((e["score"] for e in interactions if e["source"] == node or e["target"] == node), default=0.5)
            size = 15 + max_score * 25
            net.add_node(
                node,
                label=node,
                color="#00cc88",
                size=size,
                font={"size": 12, "color": "#c0c0c0"},
                borderWidth=1,
                shape="dot",
                title=f"Partner: {node}\nMax Score: {max_score:.3f}",
            )

    # Add edges with thickness proportional to score
    for edge in interactions:
        score = edge.get("score", 0.5)
        width = 1 + score * 4
        net.add_edge(
            edge["source"],
            edge["target"],
            value=score,
            width=width,
            color={"color": "#335577", "highlight": "#00ccff"},
            title=f"Score: {score:.3f}",
        )

    # Render to temp HTML and embed in Streamlit
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
        net.save_graph(f.name)
        tmp_path = f.name

    with open(tmp_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    components.html(html_content, height=650, scrolling=False)

    # Clean up
    try:
        os.unlink(tmp_path)
    except:
        pass


def render_interaction_table(interactions: list):
    """Renders a sortable table of protein interactions."""
    if not interactions:
        return

    rows = []
    for edge in interactions:
        rows.append({
            "Protein A": edge["source"],
            "Protein B": edge["target"],
            "Combined Score": f"{edge['score']:.3f}",
            "Neighborhood": f"{edge.get('nscore', 0):.3f}",
            "Experiments": f"{edge.get('escore', 0):.3f}",
            "Databases": f"{edge.get('dscore', 0):.3f}",
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("Combined Score", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
