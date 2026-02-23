import os
import json
import streamlit as st
import google.generativeai as genai
from PIL import Image
from typing import Dict, List, Any
from config import GEMINI_MODEL, IMAGE_ANALYSIS_PROMPT, REPORT_PARSING_PROMPT, QA_SYSTEM_PROMPT

class MultiModalEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.vision_model = genai.GenerativeModel(GEMINI_MODEL)
        self.text_model = genai.GenerativeModel(GEMINI_MODEL)
        
    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """Analyzes a medical image using Gemini Vision."""
        try:
            response = self.vision_model.generate_content(
                [IMAGE_ANALYSIS_PROMPT, image],
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e)}

    def parse_genomic_report(self, text: str) -> List[Dict[str, str]]:
        """Parses mutations from genomic lab report text."""
        try:
            response = self.text_model.generate_content(
                f"{REPORT_PARSING_PROMPT}\n\nReport Text:\n{text}",
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            st.error(f"Failed to parse report: {str(e)}")
            return []

    def answer_question(self, question: str, context: str = "") -> str:
        """Answers a user question, optionally with context."""
        try:
            prompt = QA_SYSTEM_PROMPT
            if context:
                prompt += f"\n\nContext to consider:\n{context}"
            prompt += f"\n\nUser Question: {question}"
            
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def fuse_multimodal_data(self, inputs: Dict[str, Any]) -> str:
        """Fuses data from multiple modalities into a comprehensive summary."""
        try:
            prompt = "You are a lead bioinformatician. Summarize these multi-modal findings into a cohesive risk assessment report. Be concise but comprehensive.\n\n"
            
            if "ai_analysis" in inputs and inputs["ai_analysis"]:
                prompt += f"ESM2 AI Analysis:\n{json.dumps(inputs['ai_analysis'], indent=2)}\n\n"
            
            if "clinvar" in inputs and inputs["clinvar"]:
                prompt += f"ClinVar Database Match:\n{json.dumps(inputs['clinvar'], indent=2)}\n\n"
                
            if "image_anomalies" in inputs and inputs["image_anomalies"]:
                prompt += f"Image Anomalies Observed:\n{json.dumps(inputs['image_anomalies'], indent=2)}\n\n"
                
            if "report_mutations" in inputs and inputs["report_mutations"]:
                prompt += f"Mutations found in Uploaded PDF Report:\n{json.dumps(inputs['report_mutations'], indent=2)}\n\n"
                
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Fusion Error: {str(e)}"
