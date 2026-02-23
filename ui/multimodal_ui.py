import streamlit as st
import json
from config import SUPPORTED_IMAGE_TYPES, MAX_IMAGE_SIZE_MB
from core.multimodal_data_client import ImagePreprocessor, PDFExtractor
from core.multimodal_engine import MultiModalEngine

def render_image_analysis_tab(engine: MultiModalEngine):
    """Renders the Image Analysis tab."""
    st.header("🖼️ Medical Image Analysis")
    st.write("Upload microscopy, histology, or radiological images for AI-driven interpretations relating to genomics.")
    
    uploaded_file = st.file_uploader("Choose an image...", type=SUPPORTED_IMAGE_TYPES)
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(uploaded_file, caption='Uploaded Image', use_container_width=True)
            
        with col2:
            if st.button("🔍 Analyze Image"):
                with st.spinner("Analyzing with Gemini Vision..."):
                    img = ImagePreprocessor.validate_and_load(uploaded_file.getvalue(), MAX_IMAGE_SIZE_MB)
                    if img:
                        results = engine.analyze_image(img)
                        if "error" in results:
                            st.error(results["error"])
                        else:
                            st.subheader("Findings")
                            st.write(results.get("findings", "No specific findings."))
                            
                            st.subheader("Anomalies")
                            st.warning(results.get("anomalies", "None detected."))
                            
                            st.subheader("Potential Associated Genes")
                            genes = results.get("relevant_genes", [])
                            if genes:
                                st.write(", ".join(genes))
                            else:
                                st.write("None specified.")
                            
                            st.session_state['image_analysis'] = results

def render_report_parser_tab(engine: MultiModalEngine):
    """Renders the PDF Report Parser tab."""
    st.header("📄 Genomic Report Parser")
    st.write("Upload clinical or lab reports (PDF) to auto-extract mentioned mutations.")
    
    uploaded_file = st.file_uploader("Choose a PDF report...", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Extract Data"):
            with st.spinner("Extracting and parsing text..."):
                text = PDFExtractor.extract_text(uploaded_file.getvalue())
                if text:
                    with st.expander("Show Raw Extracted Text"):
                        st.text(text)
                        
                    st.write("----")
                    mutations = engine.parse_genomic_report(text)
                    
                    if mutations:
                        st.success(f"Found {len(mutations)} potential mutations!")
                        st.session_state['report_mutations'] = mutations
                        for m in mutations:
                            st.info(f"**Gene:** {m.get('gene')} | **Mutation:** {m.get('mutation')}\n\n*Context:* {m.get('context')}")
                    else:
                        st.warning("No mutations found in this report.")

def render_genomic_chat_tab(engine: MultiModalEngine):
    """Renders the Natural Language Q&A tab."""
    st.header("💬 Genomic Q&A Assistant")
    st.write("Ask questions about genes, mutations, and clinical significance.")
    
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
        
    for msg in st.session_state['chat_history']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    prompt = st.chat_input("E.g., What is the effect of the TP53 R273H mutation?")
    
    if prompt:
        st.session_state['chat_history'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Gather context from previous tabs
                context = ""
                if 'image_analysis' in st.session_state:
                    context += f"Image findings: {json.dumps(st.session_state['image_analysis'])}\n"
                if 'report_mutations' in st.session_state:
                    context += f"PDF mutations: {json.dumps(st.session_state['report_mutations'])}\n"
                if 'result' in st.session_state:
                    context += f"ESM2 Analysis: {json.dumps(st.session_state['result'])}\n"
                    
                response = engine.answer_question(prompt, context)
                st.markdown(response)
                st.session_state['chat_history'].append({"role": "assistant", "content": response})

def render_fusion_dashboard(engine: MultiModalEngine):
    """Renders the Cross-Modal Fusion Dashboard."""
    st.header("📊 Multi-Modal Fusion Dashboard")
    st.write("Aggregates findings across AI Sequence Evaluation, Clinical Data, Image Analysis, and PDF Reports.")
    
    if st.button("Generate Unified Risk Assessment"):
        inputs = {}
        has_data = False
        
        if 'result' in st.session_state:
            inputs['ai_analysis'] = st.session_state['result']
            has_data = True
            
        if 'clinical_data' in st.session_state:
            inputs['clinvar'] = st.session_state['clinical_data']
            has_data = True
            
        if 'image_analysis' in st.session_state:
            inputs['image_anomalies'] = st.session_state['image_analysis'].get("anomalies")
            has_data = True
            
        if 'report_mutations' in st.session_state:
            inputs['report_mutations'] = st.session_state['report_mutations']
            has_data = True
            
        if not has_data:
            st.warning("No data found to fuse. Please run analyses on other tabs first (e.g., Sequence AI, ClinVar, Image, or PDF).")
            return
            
        with st.spinner("LLM Synthesizing Multi-Modal Findings..."):
            synthesis = engine.fuse_multimodal_data(inputs)
            st.success("Analysis Complete")
            st.markdown(synthesis)
