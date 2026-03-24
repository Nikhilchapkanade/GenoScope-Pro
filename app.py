# app.py
import os
import streamlit as st
import re
from core.ai_engine import MutationPredictor
from core.data_client import BioDataClient

# My visualization features
from ui.visualizer import (
    render_3d_structure,
    render_surface_view,
    render_comparison_3d,
    plot_plddt_confidence,
    render_mutation_heatmap,
    render_position_heatmap,
    render_batch_summary_table,
    render_interaction_network,
    render_interaction_table,
)

# Their multi-modal features
from core.multimodal_engine import MultiModalEngine
from ui.multimodal_ui import (
    render_image_analysis_tab,
    render_report_parser_tab,
    render_genomic_chat_tab,
    render_fusion_dashboard
)

st.set_page_config(page_title="GenoScope Pro", page_icon="🧬", layout="wide")

# ── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark premium palette */
    .stApp { background-color: #0e1117; }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .main-header h1 {
        background: linear-gradient(90deg, #00ff88, #00ccff, #8855ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #8899aa;
        font-size: 1.1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-card h3 { color: #00ff88; margin: 0; font-size: 1.5rem; }
    .metric-card p  { color: #8899aa; margin: 0; font-size: 0.85rem; }
    
    div[data-testid="stTabs"] button {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Cached resources  ──────────────────────────────────────
predictor = MutationPredictor()
client = BioDataClient()

# --- SIDEBAR: Configuration ---
st.sidebar.title("⚙️ Configuration")
api_key = st.sidebar.text_input("Google API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))

if api_key:
    mm_engine = MultiModalEngine(api_key=api_key)
else:
    mm_engine = None
    st.sidebar.warning("Please enter a Google API Key for multi-modal features.")


# ── HEADER  ─────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧬 GenoScope Pro</h1>
    <p>AI-Powered Protein Mutation Analysis &nbsp;•&nbsp; Multi-Modal Bioinformatics Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ── INPUT PANEL  ────────────────────────────────────────────
col_input1, col_input2, col_input3, col_btn = st.columns([2, 2, 2, 1])

with col_input1:
    uniprot_id = st.text_input("🆔 UniProt ID", value="P04637")
with col_input2:
    mutation = st.text_input("🧪 Mutation", value="R273H")
with col_input3:
    gene_name = st.text_input("🏷️ Gene Name", value="TP53")
with col_btn:
    st.write("")  # spacer
    run_btn = st.button("🚀 Run Analysis", use_container_width=True)

if run_btn:
    with st.spinner("⏳ Fetching sequence & running AI model …"):
        seq, desc = client.get_sequence(uniprot_id)
        if not seq:
            st.error("Could not fetch sequence from UniProt.")
        else:
            try:
                score = predictor.compute_score(seq, mutation)
                result = predictor.analyze_impact(score, mutation, gene_name)
                st.session_state['result'] = result
                st.session_state['seq'] = seq
                st.session_state['desc'] = desc
            except ValueError as e:
                st.error(str(e))

st.divider()

# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab1a, tab1b, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔍 AI Analysis",
    "🧬 3D Structure",
    "📊 Heatmap",
    "🕸️ Network",
    "🏥 Clinical Data",
    "🖼️ Image Analysis",
    "📄 Report Parser",
    "💬 Genomic Q&A",
    "📊 Fusion"
])

# ── TAB 1: AI Analysis ──────────────────────────────────────
with tab1:
    if 'result' in st.session_state:
        res = st.session_state['result']
        
        # Metric cards row
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <p>Verdict</p>
                <h3>{res['severity']}</h3>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <p>Delta Score</p>
                <h3>{res['score']:.4f}</h3>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <p>Source</p>
                <h3>{res['source']}</h3>
            </div>""", unsafe_allow_html=True)
        
        st.write("")
        st.info(res['insight'])
        
        with st.expander("📝 Full Protein Sequence"):
            st.code(st.session_state['seq'], language=None)
    else:
        st.info("👆 Enter a UniProt ID, mutation, and gene name above, then click **Run Analysis**.")

# ── TAB 2: 3D Structure (Enhanced) ──────────────────────────
with tab2:
    view_mode = st.radio(
        "View Mode",
        ["🎨 Cartoon", "🫧 Surface", "⚔️ Comparison (WT vs Mutant)"],
        horizontal=True,
    )
    
    if st.button("🔬 Load 3D Model", key="load_3d"):
        with st.spinner("Fetching AlphaFold structure …"):
            pdb_text, ver = client.get_structure(uniprot_id)
        
        if pdb_text:
            st.success(f"✅ Loaded AlphaFold Model ({ver})")
            st.session_state['pdb_text'] = pdb_text
            st.session_state['pdb_ver'] = ver
        else:
            st.warning("Structure not found in AlphaFold DB.")
    
    if 'pdb_text' in st.session_state:
        pdb_text = st.session_state['pdb_text']
        
        if "Cartoon" in view_mode:
            col_3d, col_conf = st.columns([3, 1])
            with col_3d:
                render_3d_structure(pdb_text, mutation)
            with col_conf:
                plot_plddt_confidence(pdb_text)
        
        elif "Surface" in view_mode:
            render_surface_view(pdb_text, mutation)
        
        elif "Comparison" in view_mode:
            render_comparison_3d(pdb_text, mutation)
            st.caption("Left: Wild-type with highlighted position  •  Right: Mutant effect visualization with neighboring residue impact zone")

# ── TAB 1a: Multi-Mutation Heatmap ────────────────────────────
with tab1a:
    st.markdown("### 📊 Batch Mutation Analysis")
    st.caption("Enter multiple mutations (comma or newline separated) to score them all at once.")
    
    col_hm1, col_hm2 = st.columns([3, 1])
    
    with col_hm1:
        mutations_input = st.text_area(
            "Mutations",
            value="R273H, G245S, R248Q, R175H, Y220C, V157F, R282W, C176Y",
            height=100,
            help="Format: single-letter e.g. R273H. Separate with commas or newlines."
        )
    
    with col_hm2:
        st.write("")
        scan_mode = st.checkbox("🔬 Deep Position Scan", help="Also scan all 20 AA substitutions at the first mutation's position")
        analyze_btn = st.button("⚡ Analyze Batch", key="batch_analyze", use_container_width=True)
    
    if analyze_btn:
        if 'seq' not in st.session_state:
            st.warning("Please run the main analysis first to load the protein sequence.")
        else:
            seq = st.session_state['seq']
            
            raw = mutations_input.replace("\n", ",")
            mutation_list = [m.strip() for m in raw.split(",") if m.strip()]
            
            with st.spinner(f"⏳ Scoring {len(mutation_list)} mutations …"):
                scores = predictor.batch_score(seq, mutation_list)
            
            render_mutation_heatmap(scores)
            
            with st.expander("📋 Detailed Results Table"):
                render_batch_summary_table(scores)
            
            if scan_mode and mutation_list:
                first_mut = mutation_list[0].upper()
                m = re.match(r"[A-Z](\d+)[A-Z]", first_mut)
                if m:
                    pos = int(m.group(1))
                    wt_aa = seq[pos - 1]
                    with st.spinner(f"🔬 Scanning all substitutions at position {pos} …"):
                        scan = predictor.scan_position(seq, pos)
                    render_position_heatmap(scan, pos, wt_aa)

# ── TAB 1b: Interaction Network ───────────────────────────────
with tab1b:
    st.markdown("### 🕸️ Protein Interaction Network")
    st.caption(f"Discover what proteins interact with **{gene_name}** using the STRING database.")
    
    col_net1, col_net2 = st.columns([1, 1])
    with col_net1:
        net_limit = st.slider("Max interactions", 5, 30, 15)
    with col_net2:
        st.write("")
        net_btn = st.button("🔎 Fetch Network", key="fetch_network", use_container_width=True)
    
    if net_btn:
        with st.spinner(f"⏳ Querying STRING DB for {gene_name} interactions …"):
            interactions = client.get_interaction_network(gene_name, limit=net_limit)
        
        if interactions:
            st.success(f"✅ Found {len(interactions)} interactions")
            render_interaction_network(gene_name, interactions)
            
            with st.expander("📋 Interaction Details"):
                render_interaction_table(interactions)
        else:
            st.warning("No interactions found. Check the gene name or try a different one.")

# ── TAB 3: Clinical Data ────────────────────────────────────
with tab3:
    if st.button("🏥 Check Clinical Databases", key="clinical"):
        with st.spinner(f"Searching ClinVar for {gene_name} {mutation} …"):
            clinical_data = client.fetch_clinical_data(gene_name, mutation)

            if "error" in clinical_data:
                st.error(f"Error: {clinical_data['error']}")
            elif clinical_data.get("significance") == "Not Found":
                st.warning("No direct match found in ClinVar for this specific mutation.")
                st.caption("Try checking the gene name or mutation format.")
            else:
                st.success("✅ Record Found!")
                st.session_state['clinical_data'] = clinical_data
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Clinical Significance", clinical_data.get("significance"))
                with col_b:
                    st.write("**Associated Conditions:**")
                    st.write(clinical_data.get("conditions"))
                st.caption(f"Source: {clinical_data.get('source')}")

# ── TAB 4: Image Analysis ────────────────────────────────────
with tab4:
    if mm_engine:
        render_image_analysis_tab(mm_engine)
    else:
        st.warning("API Key required for image analysis.")

# ── TAB 5: Report Parser ────────────────────────────────────
with tab5:
    if mm_engine:
        render_report_parser_tab(mm_engine)
    else:
        st.warning("API Key required for report parsing.")

# ── TAB 6: Genomic Q&A ────────────────────────────────────
with tab6:
    if mm_engine:
        render_genomic_chat_tab(mm_engine)
    else:
        st.warning("API Key required for conversational Q&A.")

# ── TAB 7: Fusion Dashboard ────────────────────────────────────
with tab7:
    if mm_engine:
        render_fusion_dashboard(mm_engine)
    else:
        st.warning("API Key required for fusion dashboard.")
