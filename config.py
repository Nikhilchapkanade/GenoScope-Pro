# config.py
from typing import Dict

MODEL_NAME = "facebook/esm2_t6_8M_UR50D"

KNOWN_MUTATIONS: Dict[str, Dict[str, str]] = {
    'TP53_R175H': {
        'severity': '🔴 Likely Deleterious',
        'summary': 'Hotspot mutation inactivating p53 tumor suppressor function.'
    },
    'TP53_R248Q': {
        'severity': '🔴 Likely Deleterious',
        'summary': 'Disrupts DNA-binding domain, loss of transcriptional activity.'
    },
    'TP53_R273H': {
        'severity': '🔴 Likely Deleterious',
        'summary': 'Gain-of-function properties, enhancing cancer cell survival.'
    }
}

# Standard Amino Acid Mapping
AA_MAP = {
    'A': 'Ala', 'R': 'Arg', 'N': 'Asn', 'D': 'Asp', 'C': 'Cys',
    'Q': 'Gln', 'E': 'Glu', 'G': 'Gly', 'H': 'His', 'I': 'Ile',
    'L': 'Leu', 'K': 'Lys', 'M': 'Met', 'F': 'Phe', 'P': 'Pro',
    'S': 'Ser', 'T': 'Thr', 'W': 'Trp', 'Y': 'Tyr', 'V': 'Val'
}

# Multi-Modal Constants
GEMINI_MODEL = "gemini-2.5-flash"
SUPPORTED_IMAGE_TYPES = ["jpg", "jpeg", "png"]
MAX_IMAGE_SIZE_MB = 10

IMAGE_ANALYSIS_PROMPT = """You are a bioinformatics imaging specialist. 
Analyze the provided microscopy/histopathology image. Output a structured JSON containing:
- findings: brief description of apparent cell morphology or tissue structures
- anomalies: any observed abnormalities
- relevant_genes: potential genes associated with this type of tissue/finding (list of strings)
Do not provide a medical diagnosis."""

REPORT_PARSING_PROMPT = """You are a genomic data extraction engine. 
Extract mutations from the provided report text. Output a JSON list where each object has:
- gene: gene symbol (e.g., TP53)
- mutation: mutation identifier (e.g., R273H)
- context: sentence/phrase where it was found
If no clear mutation is found, return an empty list."""

QA_SYSTEM_PROMPT = """You are an expert genomics AI assistant. 
Answer questions related to genomic mutations, protein structures, and clinical significance.
Keep answers concise, accurate, and biologically sound. Provide context when asked about specific mutations."""
