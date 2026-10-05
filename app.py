import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image
import os
import base64
import io
import json
import re
import fitz  # PyMuPDF
import pdfplumber

# 1. Page Configuration
st.set_page_config(
    page_title="G-Tax - Tax Simplified",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dynamically resolve file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename):
    return os.path.join(BASE_DIR, filename)

def sanitize_for_filename(value):
    value = str(value or "").strip()
    for ch in [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        value = value.replace(ch, "")
    return value or "Unnamed"

def make_filename(feature_name, ext="csv"):
    trade = sanitize_for_filename(st.session_state.get("trade_name", ""))
    month = sanitize_for_filename(st.session_state.get("month", ""))
    fy = sanitize_for_filename(st.session_state.get("fy", ""))
    return f"{feature_name}_{trade}_{month}_{fy}.{ext}"

def get_base64_bg(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            overflow-y: hidden !important;
        }}
        </style>
        """
    return ""

# Inject background image or fallback premium obsidian gradient
bg_css = get_base64_bg(get_path("bg.png"))
if bg_css:
    st.markdown(bg_css, unsafe_allow_html=True)
else:
    st.markdown(
        """
        <style>
        .stApp { 
            background: radial-gradient(circle at 50% 20%, #1A0B2E 0%, #0B0813 60%, #05030A 100%);
            overflow-y: hidden !important; 
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

# Deep Obsidian, Vibranium Purple, and Gold Custom Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #F4F4F9 !important;
    }

    /* --- GLOBAL VIEWPORT COMPRESSION --- */
    div.block-container {
        padding-top: 1.8rem !important; 
        padding-bottom: 0.5rem !important;
        max-width: 95% !important;
    }

    /* --- GRADIENT TITLES & HEADINGS --- */
    .hero-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 5.5rem !important;  
        font-weight: 700 !important;
        text-align: center;
        background: linear-gradient(135deg, #FFF099 0%, #D4AF37 50%, #AA7C11 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        letter-spacing: -2px;
        text-transform: uppercase;  
        filter: drop-shadow(0px 0px 20px rgba(157, 78, 221, 0.45));
    }
    
    .hero-subtitle {
        font-size: 1.8rem !important;
        font-style: italic;
        font-weight: 500;
        color: #D4AF37 !important;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 0.8rem;
        letter-spacing: 1px;
        text-shadow: 0px 0px 10px rgba(157, 78, 221, 0.3);
    }
    
    .hero-meta {
        text-align: center;
        font-size: 1.1rem !important;
        color: #C77DFF !important;
        opacity: 0.9;
        margin-bottom: 1.5rem;
    }
    
    .footer-text {
        text-align: center;
        font-size: 0.95rem;
        color: #E0C068 !important;
        margin-top: 2.5rem;
        opacity: 0.85;
    }

    /* ---- CARDS & GLASSMORPHISM CONTAINER ---- */
    div[data-testid="stExpander"], div[data-testid="stForm"], .stCard {
        background: rgba(16, 10, 26, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(157, 78, 221, 0.35) !important; 
        border-radius: 12px !important;
        padding: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8), 0 0 15px rgba(123, 44, 191, 0.2);
    }

    /* --- FORM INPUTS & DROPDOWNS --- */
    div[data-testid="stTextInput"] > div, 
    div[data-testid="stNumberInput"] > div, 
    div[data-testid="stSelectbox"] > div {
        background: rgba(11, 8, 19, 0.85) !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
        border-radius: 8px !important;
        color: #F4F4F9 !important;
    }

    div[data-testid="stTextInput"] input, 
    div[data-testid="stNumberInput"] input {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    label {
        color: #E0C068 !important;
        font-weight: 600 !important;
    }

    /* --- CORE BUTTON UNIFICATION --- */
    div.stButton > button {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.0rem !important;      
        font-weight: 700 !important;
        padding: 10px 20px !important;      
        border-radius: 8px !important;
        transition: all 0.3s ease-in-out !important;
        border: none !important;
        width: 100% !important;
    }

    /* PRIMARY NAVIGATION BUTTON - VIBRANIUM PURPLE GRADIENT WITH GOLD GLOW */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7B2CBF 0%, #5A189A 50%, #3C096C 100%) !important;
        color: #FFF099 !important;
        border: 1px solid #D4AF37 !important;
        box-shadow: 0px 0px 15px rgba(157, 78, 221, 0.6) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #9D4EDD 0%, #7B2CBF 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0px 0px 22px rgba(212, 175, 55, 0.8) !important;
        transform: translateY(-1px);
    }

    /* SECONDARY NAVIGATION BUTTON - OBSIDIAN GLASS WITH PURPLE BORDER */
    div.stButton > button[kind="secondary"] {
        background: rgba(157, 78, 221, 0.12) !important;
        color: #F4F4F9 !important;
        border: 1px solid rgba(157, 78, 221, 0.5) !important;
    }

    div.stButton > button[kind="secondary"]:hover {
        background: rgba(157, 78, 221, 0.28) !important;
        color: #FFF099 !important;
        border-color: #D4AF37 !important;
        box-shadow: 0px 0px 12px rgba(157, 78, 221, 0.5) !important;
    }

    /* --- SCREEN HEADERS & NOTES --- */
    .nav-title-fixed {
        font-family: 'Space Grotesk', sans-serif !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #D4AF37 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 0px;
        margin-bottom: 12px;
        font-weight: 700;
        font-size: 2.0rem; 
        letter-spacing: 0.5px;
        filter: drop-shadow(0px 2px 8px rgba(157, 78, 221, 0.4));
    }
    
    .prov-note {
        background: rgba(60, 9, 108, 0.45);
        border-left: 4px solid #D4AF37;
        padding: 10px 14px;
        font-size: 0.9rem;
        color: #F4F4F9;
        margin-bottom: 18px;
        border-radius: 0 8px 8px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 10px rgba(157, 78, 221, 0.2);
    }

    div.back-btn-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 15px;
    }

    div.back-btn-container div.stButton > button {
        font-size: 0.85rem !important;       
        padding: 6px 18px !important;        
        min-height: 34px !important;         
        width: auto !important;              
        background: rgba(157, 78, 221, 0.15) !important;
        color: #E0C068 !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
    }

    div.back-btn-container div.stButton > button:hover {
        background: rgba(157, 78, 221, 0.35) !important;
        color: #FFFFFF !important;
        border-color: #D4AF37 !important;
        box-shadow: 0px 0px 10px rgba(212, 175, 55, 0.4) !important;
    }

    /* DATAFRAMES & TABLES ENHANCEMENTS */
    div[data-testid="stDataFrame"] {
        background: rgba(11, 8, 19, 0.6) !important;
        border-radius: 8px;
        padding: 4px;
        border: 1px solid rgba(157, 78, 221, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# Helper to render a PDF preview
def render_pdf_preview(file_bytes, caption="Uploaded Document Preview (Page 1 of PDF)"):
    with st.expander("📄 View PDF Preview Panel", expanded=False):
        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        preview_pixmap = pdf_doc[0].get_pixmap(dpi=150)
        preview_image = Image.open(io.BytesIO(preview_pixmap.tobytes("png")))
        st.image(preview_image, caption=caption, use_container_width=True)
        if len(pdf_doc) > 1:
            st.caption(f"This PDF has {len(pdf_doc)} pages — all pages will be sent for extraction.")
        pdf_doc.close()

# Shared navigation helpers
def back_to_navigation():
    st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
    if st.button("← Back to GSTR-1 Dashboard", use_container_width=False, key="back_to_nav"):
        st.session_state.page = "gstr1_dashboard"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def back_to_gstr3b_menu():
    st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
    if st.button("← Back to GSTR 3B Options", use_container_width=False, key="back_to_3b"):
        st.session_state.page = "gstr3b_menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Session State Initialization
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "docs_df" not in st.session_state:
    st.session_state.docs_df = pd.DataFrame(columns=["Nature of Document", "Sr. No. From", "Sr. No. To", "Total Number", "Cancelled"])

if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "trade_name" not in st.session_state:
    st.session_state.trade_name = ""
if "gstin" not in st.session_state:
    st.session_state.gstin = ""
if "fy" not in st.session_state:
    st.session_state.fy = "2026-27"
if "month" not in st.session_state:
    st.session_state.month = "Jul"

# Schemas
GSTR1_COLUMNS = [
    "GSTIN/UIN of Recipient", "Receiver Name", "Invoice Number", "Invoice date",
    "Invoice Value", "Place Of Supply", "Reverse Charge", "Applicable % of Tax Rate",
    "Invoice Type", "E-Commerce GSTIN", "Rate", "Taxable Value", "Cess Amount"
]

gstr1_json_schema = {
    "type": "OBJECT",
    "properties": {
        "rows": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "GSTIN/UIN of Recipient": {"type": "STRING", "description": "15-character GSTIN of the buyer"},
                    "Receiver Name": {"type": "STRING", "description": "Legal/Trade Name of the buyer/recipient"},
                    "Invoice Number": {"type": "STRING", "description": "Unique alphanumeric invoice number"},
                    "Invoice date": {"type": "STRING", "description": "Invoice date formatted strictly as DD-MMM-YY (e.g., 14-Jul-26)"},
                    "Invoice Value": {"type": "NUMBER", "description": "Total gross invoice value including taxes"},
                    "Place Of Supply": {"type": "STRING", "description": "Format: State Code-State Name (e.g., 33-Tamil Nadu)"},
                    "Reverse Charge": {"type": "STRING", "enum": ["Y", "N"]},
                    "Applicable % of Tax Rate": {"type": "STRING"},
                    "Invoice Type": {"type": "STRING", "enum": ["Regular B2B", "Deemed Exp", "SEZ supplies with payment", "SEZ supplies without payment"]},
                    "E-Commerce GSTIN": {"type": "STRING"},
                    "Rate": {"type": "NUMBER", "description": "The specific itemized GST Rate percentage"},
                    "Taxable Value": {"type": "NUMBER", "description": "The net taxable value for this specific tax rate bracket"},
                    "Cess Amount": {"type": "NUMBER"}
                },
                "required": ["GSTIN/UIN of Recipient", "Invoice Number", "Invoice date", "Invoice Value", "Place Of Supply", "Reverse Charge", "Invoice Type", "Rate", "Taxable Value"]
            }
        }
    }
}

B2CS_COLUMNS = [
    "Type", "Place Of Supply", "Rate", "Applicable % of Tax Rate", 
    "Taxable Value", "Cess Amount", "E-Commerce GSTIN"
]

b2cs_json_schema = {
    "type": "OBJECT",
    "properties": {
        "rows": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "Type": {"type": "STRING", "enum": ["E", "OE"], "description": "Use 'E' if sold through E-commerce, else 'OE'"},
                    "Place Of Supply": {"type": "STRING", "description": "Strict format: Code-State Name (e.g., 33-Tamil Nadu)"},
                    "Rate": {"type": "NUMBER", "description": "The GST Rate percentage (e.g., 5, 12, 18, 28)"},
                    "Applicable % of Tax Rate": {"type": "STRING", "description": "Leave blank unless a specific statutory rule applies"},
                    "Taxable Value": {"type": "NUMBER", "description": "The net taxable value for this specific tax rate bracket"},
                    "Cess Amount": {"type": "NUMBER", "description": "Cess amount if applicable, else leave blank"},
                    "E-Commerce GSTIN": {"type": "STRING", "description": "15-character GSTIN if Type is 'E', else blank"}
                },
                "required": ["Type", "Place Of Supply", "Rate", "Taxable Value"]
            }
        }
    }
}

HSN_COLUMNS = [
    "HSN", "Description", "UQC", "Total Quantity", "Total Value",
    "Taxable Value", "Integrated Tax Amount", "Central Tax Amount",
    "State/UT Tax Amount", "Cess Amount", "Rate"
]

hsn_json_schema = {
    "type": "OBJECT",
    "properties": {
        "rows": {
            "type": "ARRAY",
            "description": "Extract every individual line item exactly as printed on the invoice before any grouping.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "HSN": {"type": "STRING", "description": "The exact HSN/SAC code. Minimum 4 digits for turnover <= 5Cr, 6 digits for > 5Cr"},
                    "UQC": {"type": "STRING", "description": "Official GST Unit Quantity Code. Map KGS to KGS-KILOGRAMS, PKT to BOX-BOXES, NOS to NOS-NUMBERS, PCS to PCS-PIECES"},
                    "Total Quantity": {"type": "NUMBER", "description": "The exact quantity printed for this specific line item"},
                    "Taxable Value": {"type": "NUMBER", "description": "The exact net taxable value printed for this specific line item"},
                    "Rate": {"type": "NUMBER", "description": "The statutory GST rate percentage for this line (e.g., 5, 12, 18, 28)"}
                },
                "required": ["HSN", "UQC", "Total Quantity", "Taxable Value", "Rate"]
            }
        }
    }
}

DOCS_COLUMNS = ["Nature of Document", "Sr. No. From", "Sr. No. To", "Total Number", "Cancelled"]

docs_json_schema = {
    "type": "OBJECT",
    "properties": {
        "documents": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "Nature of Document": {"type": "STRING", "description": "e.g., Invoices for outward supply, Debit Note, Credit Note"},
                    "Sr. No. From": {"type": "STRING", "description": "Starting serial number"},
                    "Sr. No. To": {"type": "STRING", "description": "Ending serial number"},
                    "Total Number": {"type": "INTEGER", "description": "Total count of documents issued"},
                    "Cancelled": {"type": "INTEGER", "description": "Count of cancelled documents"}
                },
                "required": ["Nature of Document", "Sr. No. From", "Sr. No. To", "Total Number", "Cancelled"]
            }
        }
    }
}

# Standard GST Nature of Document options for dropdown
NATURE_OF_DOCUMENTS_OPTIONS = [
    "Invoices for outward supply",
    "Invoices for inward supply from unregistered person",
    "Revised Invoice",
    "Debit Note",
    "Credit Note",
    "Receipt voucher",
    "Payment Voucher",
    "Refund voucher",
    "Delivery Challan for job work",
    "Delivery Challan for supply on approval",
    "Delivery Challan in case of liquid gas",
    "Delivery Challan in cases other than by way of supply"
]

# --- GSTR-3B AUTOMATION HELPER FUNCTIONS ---
def extract_gstr1_data(pdf_file):
    """Parses outward tax values from GSTR-1 Summary PDF."""
    total_taxable_value = 0.0
    total_igst = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            for line in text.split('\n'):
                if "Total Outward Supplies" in line or "Total B2B" in line:
                    numbers = re.findall(r'[-+]?\d*\.\d+|\d+', line.replace(',', ''))
                    if len(numbers) >= 4:
                        total_taxable_value += float(numbers[-4])
                        total_igst += float(numbers[-3])
                        total_cgst += float(numbers[-2])
                        total_sgst += float(numbers[-1])
                        
    if total_taxable_value == 0:
        total_taxable_value, total_igst, total_cgst, total_sgst = 500000.00, 45000.00, 22500.00, 22500.00
        st.warning("⚠️ Standard PDF text pattern mismatch. Using default values for preview.")

    return {
        "txval": total_taxable_value,
        "iamt": total_igst,
        "camt": total_cgst,
        "samt": total_sgst,
        "csamt": 0.0
    }

def extract_gstr2b_excel(excel_file):
    """Extracts Eligible ITC from GSTR-2B Excel File."""
    try:
        df = pd.read_excel(excel_file, sheet_name=None)
        summary_sheet = [sheet for sheet in df.keys() if 'summary' in sheet.lower() or 'itc' in sheet.lower()]
        
        eligible_itc = {"iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0}
        
        if summary_sheet:
            data = df[summary_sheet[0]]
            for index, row in data.iterrows():
                row_str = " ".join([str(val) for val in row.values])
                if "itc available" in row_str.lower() or "eligible itc" in row_str.lower() or "all other itc" in row_str.lower():
                    numbers = [float(s) for s in re.findall(r'[-+]?\d*\.\d+|\d+', row_str.replace(',', '')) if float(s) > 0]
                    if len(numbers) >= 3:
                        eligible_itc["iamt"] = numbers[0]
                        eligible_itc["camt"] = numbers[1]
                        eligible_itc["samt"] = numbers[2]
                        if len(numbers) >= 4:
                            eligible_itc["csamt"] = numbers[3]
                        break
        else:
            st.warning("⚠️ 'Summary' sheet not pinpointed explicitly in Excel file.")
            
        return eligible_itc
    except Exception as e:
        st.error(f"Error processing Excel: {e}")
        return {"iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0}

def extract_gstr2b_pdf(pdf_file):
    """Extracts Eligible ITC from GSTR-2B PDF File using pdfplumber."""
    eligible_itc = {"iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0}
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split('\n'):
                    # Look for the primary "All other ITC" row in Part A
                    if "All other ITC" in line and ("4(A)(5)" in line or "Supplies from" in line):
                        numbers = re.findall(r'[-+]?\d[\d,]*\.\d{2}', line)
                        cleaned_numbers = [float(n.replace(',', '')) for n in numbers]
                        if len(cleaned_numbers) >= 3:
                            eligible_itc["iamt"] = cleaned_numbers[0]
                            eligible_itc["camt"] = cleaned_numbers[1]
                            eligible_itc["samt"] = cleaned_numbers[2]
                            if len(cleaned_numbers) >= 4:
                                eligible_itc["csamt"] = cleaned_numbers[3]
                            return eligible_itc
    except Exception as e:
        st.error(f"Error processing GSTR-2B PDF: {e}")
    return eligible_itc


# --- SCREEN 1: LANDING PAGE ---
if st.session_state.page == "landing":
    col_logo, _ = st.columns([1, 4])
    with col_logo:
        if os.path.exists(get_path("logo_p.png")):
            img_p = Image.open(get_path("logo_p.png"))
            st.image(img_p, width=150)
        else:
            st.markdown("<p style='color: #D4AF37; margin-top:0;'><b>[P] Prism Labs</b></p>", unsafe_allow_html=True)
        
    _, center_col, _ = st.columns([1, 1.8, 1])
    with center_col:
        st.write("<br>", unsafe_allow_html=True)
        st.markdown('<h1 class="hero-title">G-Tax</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-subtitle">— Tax Simplified —</p>', unsafe_allow_html=True)
        st.markdown('<p class="hero-meta">By Prism Labs ⓘ</p>', unsafe_allow_html=True)
        
        if st.button("Get Started", type="primary", use_container_width=True):
            st.session_state.page = "setup"
            st.rerun()
            
        st.markdown('<p class="footer-text">Engineered by Aazam & Subahan</p>', unsafe_allow_html=True)

# --- SCREEN 2: CONFIGURATION & AUTHENTICATION ---
elif st.session_state.page == "setup":
    col_logo, _ = st.columns([1, 4])
    with col_logo:
        if os.path.exists(get_path("logo_g.png")):
            img_g = Image.open(get_path("logo_g.png"))
            st.image(img_g, width=80)
        
    _, form_col, _ = st.columns([1.2, 2, 1.2])
    with form_col:
        st.write("<br>", unsafe_allow_html=True)
        with st.expander("Configuration", expanded=True):
            st.session_state.api_key = st.text_input("API Key", type="password", value=st.session_state.api_key, placeholder="Enter your secret API key")
            
        st.write("") 
        with st.expander("Authentication", expanded=True):
            st.session_state.trade_name = st.text_input("Trade Name", value=st.session_state.trade_name, placeholder="Enter registered trade name")
            st.session_state.gstin = st.text_input("GSTIN", value=st.session_state.gstin, placeholder="Enter 15-digit GSTIN")
            
            col_fy, col_month = st.columns(2)
            fy_options = ["2025-26", "2026-27"]
            fy_index = fy_options.index(st.session_state.fy) if st.session_state.fy in fy_options else 1
            with col_fy:
                st.session_state.fy = st.selectbox("Financial Year", options=fy_options, index=fy_index)
                
            month_options = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
            month_index = month_options.index(st.session_state.month) if st.session_state.month in month_options else 3
            with col_month:
                st.session_state.month = st.selectbox("Month", options=month_options, index=month_index)

        st.write("<br>", unsafe_allow_html=True) 
        col_back, col_submit = st.columns([1, 1])
        with col_back:
            if st.button("Back", use_container_width=True):
                st.session_state.page = "landing"
                st.rerun()
        with col_submit:
            if st.button("Continue", type="primary", use_container_width=True):
                if not st.session_state.trade_name or not st.session_state.gstin:
                    st.error("Please enter both Trade Name and GSTIN.")
                else:
                    st.session_state.page = "returns"
                    st.rerun()

# --- SCREEN 3: RETURNS DASHBOARD ---
elif st.session_state.page == "returns":
    col_logo, _ = st.columns([1, 4])
    with col_logo:
        if os.path.exists(get_path("logo_g.png")):
            img_g = Image.open(get_path("logo_g.png"))
            st.image(img_g, width=80)

    _, main_container, _ = st.columns([1.0, 2.0, 1.0])
    with main_container:
        with st.container():
            st.markdown('<h2 class="nav-title-fixed">GST Returns Filing Dashboard</h2>', unsafe_allow_html=True)
            st.markdown('<div class="prov-note">📜 <b>Statutory Note (Sec 37 & Sec 39):</b> GSTR-1 outward details must be furnished on or before the 11th of the succeeding month (or 13th for QRMP). GSTR-3B summary returns must be discharged self-assessing net cash liabilities.</div>', unsafe_allow_html=True)
            
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                if st.button("GSTR 1 (Outward Supplies)", use_container_width=True):
                    st.session_state.page = "gstr1_dashboard"
                    st.rerun()
            with row1_col2:
                if st.button("GSTR 3B (Summary & ITC)", use_container_width=True):
                    st.session_state.page = "gstr3b_menu"
                    st.rerun()
            
            st.markdown("<hr style='margin: 15px 0; border: 0.5px solid rgba(157, 78, 221, 0.3);'>", unsafe_allow_html=True)
            
            nav_col1, nav_col2 = st.columns(2)
            with nav_col1:
                if st.button("Back", use_container_width=True):
                    st.session_state.page = "setup"
                    st.rerun()
            with nav_col2:
                if st.button("Continue", type="primary", use_container_width=True):
                    pass

# --- SCREEN 3B MENU: GSTR 3B OPTIONS ---
elif st.session_state.page == "gstr3b_menu":
    col_logo, _ = st.columns([1, 4])
    with col_logo:
        if os.path.exists(get_path("logo_g.png")):
            img_g = Image.open(get_path("logo_g.png"))
            st.image(img_g, width=80)

    _, main_container, _ = st.columns([1.0, 2.0, 1.0])
    with main_container:
        with st.container():
            st.markdown('<h2 class="nav-title-fixed">GSTR 3B Processing Mode</h2>', unsafe_allow_html=True)
            st.markdown('<div class="prov-note">⚖️ <b>Rule 88A Compliance:</b> Input Tax Credit of IGST shall be completely exhausted towards IGST, CGST & SGST before utilizing CGST or SGST credit.</div>', unsafe_allow_html=True)
            
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                if st.button("Manual Calculator", use_container_width=True):
                    st.session_state.page = "gstr3b_manual"
                    st.rerun()
            with row1_col2:
                if st.button("Automatic JSON Pipeline", use_container_width=True):
                    st.session_state.page = "gstr3b_automatic"
                    st.rerun()

            st.markdown("<hr style='margin: 15px 0; border: 0.5px solid rgba(157, 78, 221, 0.3);'>", unsafe_allow_html=True)

            st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
            if st.button("← Back to Returns", use_container_width=False):
                st.session_state.page = "returns"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- SCREEN 3B MANUAL: ACCURATE GST CALCULATOR ---
elif st.session_state.page == "gstr3b_manual":
    st.markdown('<h2 class="nav-title-fixed">📊 GSTR-3B Rule 88A Set-Off Calculator</h2>', unsafe_allow_html=True)
    st.markdown('<div class="prov-note"><b>Statutory Compliance:</b> Under Section 49 read with Rule 88A, IGST ITC must be 100% utilized prior to utilizing CGST/SGST ITC. Cross-utilization of CGST against SGST or vice-versa is strictly prohibited.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Opening ITC (₹)")
        op_igst = st.number_input("IGST Opening", min_value=0.0, value=0.0, step=100.0, key="op_igst")
        op_cgst = st.number_input("CGST Opening", min_value=0.0, value=0.0, step=100.0, key="op_cgst")
        op_sgst = st.number_input("SGST Opening", min_value=0.0, value=0.0, step=100.0, key="op_sgst")

    with c2:
        st.markdown("#### Output Liability (₹)")
        liab_igst = st.number_input("IGST Output Liability", min_value=0.0, value=0.0, step=100.0, key="liab_igst")
        liab_cgst = st.number_input("CGST Output Liability", min_value=0.0, value=0.0, step=100.0, key="liab_cgst")
        liab_sgst = st.number_input("SGST Output Liability", min_value=0.0, value=0.0, step=100.0, key="liab_sgst")

    with c3:
        st.markdown("#### Current Eligible ITC (₹)")
        curr_igst = st.number_input("IGST Current Eligible", min_value=0.0, value=0.0, step=100.0, key="curr_igst")
        curr_cgst = st.number_input("CGST Current Eligible", min_value=0.0, value=0.0, step=100.0, key="curr_cgst")
        curr_sgst = st.number_input("SGST Current Eligible", min_value=0.0, value=0.0, step=100.0, key="curr_sgst")

    # TOTAL AVAILABLE ITC
    tot_avail_igst = op_igst + curr_igst
    tot_avail_cgst = op_cgst + curr_cgst
    tot_avail_sgst = op_sgst + curr_sgst

    # --- ACCURATE RULE 88A SET-OFF LOGIC ---
    # Step 1: IGST ITC used first against IGST liability
    setoff_igst_from_igst = min(liab_igst, tot_avail_igst)
    rem_liab_igst = liab_igst - setoff_igst_from_igst
    rem_avail_igst = tot_avail_igst - setoff_igst_from_igst

    # Step 2: Remaining IGST ITC used against CGST liability, then SGST liability
    setoff_cgst_from_igst = min(liab_cgst, rem_avail_igst)
    rem_liab_cgst = liab_cgst - setoff_cgst_from_igst
    rem_avail_igst -= setoff_cgst_from_igst

    setoff_sgst_from_igst = min(liab_sgst, rem_avail_igst)
    rem_liab_sgst = liab_sgst - setoff_sgst_from_igst
    rem_avail_igst -= setoff_sgst_from_igst

    # Remaining IGST liability (if any) paid via CGST, then SGST
    setoff_igst_from_cgst = min(rem_liab_igst, tot_avail_cgst)
    rem_liab_igst -= setoff_igst_from_cgst
    rem_avail_cgst = tot_avail_cgst - setoff_igst_from_cgst

    setoff_igst_from_sgst = min(rem_liab_igst, tot_avail_sgst)
    rem_liab_sgst -= setoff_igst_from_sgst
    rem_avail_sgst = tot_avail_sgst - setoff_igst_from_sgst

    net_cash_igst = max(0.0, rem_liab_igst)

    # Step 3: CGST ITC used against CGST liability (Rule: No cross set-off against SGST)
    setoff_cgst_from_cgst = min(rem_liab_cgst, rem_avail_cgst)
    net_cash_cgst = max(0.0, rem_liab_cgst - setoff_cgst_from_cgst)
    unutil_cgst = max(0.0, rem_avail_cgst - setoff_cgst_from_cgst)

    # Step 4: SGST ITC used against SGST liability (Rule: No cross set-off against CGST)
    setoff_sgst_from_sgst = min(rem_liab_sgst, rem_avail_sgst)
    net_cash_sgst = max(0.0, rem_liab_sgst - setoff_sgst_from_sgst)
    unutil_sgst = max(0.0, rem_avail_sgst - setoff_sgst_from_sgst)

    total_net_cash = net_cash_igst + net_cash_cgst + net_cash_sgst
    unutil_igst = max(0.0, rem_avail_igst)

    st.markdown("---")
    st.markdown("### Total Available ITC")
    df_part2 = pd.DataFrame({
        "Tax Head": ["IGST", "CGST", "SGST / UTGST"],
        "Total Available ITC (₹)": [tot_avail_igst, tot_avail_cgst, tot_avail_sgst]
    })
    st.table(df_part2)

    st.markdown("### Rule 88A Set-Off Simulation & Net Cash Payable")
    df_part3 = pd.DataFrame({
        "Tax Head": ["IGST", "CGST", "SGST / UTGST"],
        "Output Liability (₹)": [liab_igst, liab_cgst, liab_sgst],
        "Set-off from IGST ITC (₹)": [setoff_igst_from_igst, setoff_cgst_from_igst, setoff_sgst_from_igst],
        "Set-off from CGST ITC (₹)": [setoff_igst_from_cgst, setoff_cgst_from_cgst, 0.0],
        "Set-off from SGST ITC (₹)": [setoff_igst_from_sgst, 0.0, setoff_sgst_from_sgst],
        "Net Cash Payable (₹)": [net_cash_igst, net_cash_cgst, net_cash_sgst]
    })
    st.table(df_part3)
    st.metric("Total Net Cash Payable (₹)", f"₹ {total_net_cash:,.2f}")

    st.markdown("### Unutilized ITC Carry Forward Balance")
    df_part4 = pd.DataFrame({
        "Tax Head": ["IGST Unutilized", "CGST Unutilized", "SGST Unutilized"],
        "Unutilized Balance (₹)": [unutil_igst, unutil_cgst, unutil_sgst]
    })
    st.table(df_part4)

    export_df = pd.DataFrame({
        "Tax Head": ["IGST", "CGST", "SGST / UTGST"],
        "Opening ITC": [op_igst, op_cgst, op_sgst],
        "Current Output Liability": [liab_igst, liab_cgst, liab_sgst],
        "Current Eligible ITC": [curr_igst, curr_cgst, curr_sgst],
        "Total Available ITC": [tot_avail_igst, tot_avail_cgst, tot_avail_sgst],
        "Set-off from IGST": [setoff_igst_from_igst, setoff_cgst_from_igst, setoff_sgst_from_igst],
        "Set-off from CGST": [setoff_igst_from_cgst, setoff_cgst_from_cgst, 0.0],
        "Set-off from SGST": [setoff_igst_from_sgst, 0.0, setoff_sgst_from_sgst],
        "Net Cash Payable": [net_cash_igst, net_cash_cgst, net_cash_sgst],
        "Unutilized ITC Balance": [unutil_igst, unutil_cgst, unutil_sgst]
    })
    
    col_csv, col_json = st.columns(2)
    with col_csv:
        st.download_button(
            "📥 Download Summary CSV",
            data=export_df.to_csv(index=False).encode('utf-8'),
            file_name=make_filename("GST_3B_SetOff_Calculator", ext="csv"),
            mime="text/csv",
            use_container_width=True
        )
    with col_json:
        st.download_button(
            "📥 Download Summary JSON",
            data=export_df.to_json(orient="records", indent=4),
            file_name=make_filename("GST_3B_SetOff_Calculator", ext="json"),
            mime="application/json",
            use_container_width=True
        )

    back_to_gstr3b_menu()

# --- SCREEN 3B AUTOMATIC ---
elif st.session_state.page == "gstr3b_automatic":
    st.markdown('<h2 class="nav-title-fixed">📊 Automated GSTR-3B Payload Generator</h2>', unsafe_allow_html=True)
    st.markdown('<div class="prov-note">📄 <b>Rule 88D Compliance:</b> Auto-extracts GSTR-1 Outward Liabilities and matches Eligible ITC with static GSTR-2B statements to eliminate mismatches.</div>', unsafe_allow_html=True)

    st.markdown("### 📥 Document Uploads")
    col1, col2 = st.columns(2)
    with col1:
        gstr1_file = st.file_uploader("Upload GSTR-1 Summary (PDF)", type=["pdf"], key="gstr3b_pdf")
    with col2:
        gstr2b_file = st.file_uploader("Upload GSTR-2B (PDF or Excel)", type=["pdf", "xlsx", "xls"], key="gstr3b_2b")

    st.markdown("---")
    st.markdown("### 💼 Manual Opening ITC Fill")
    st.caption("Fill opening balance details to consolidate with current month's GSTR-2B eligible ITC.")
    op_col1, op_col2, op_col3, op_col4 = st.columns(4)
    with op_col1:
        auto_op_igst = st.number_input("Opening IGST ITC (₹)", min_value=0.0, value=0.0, step=100.0, key="auto_op_igst")
    with op_col2:
        auto_op_cgst = st.number_input("Opening CGST ITC (₹)", min_value=0.0, value=0.0, step=100.0, key="auto_op_cgst")
    with op_col3:
        auto_op_sgst = st.number_input("Opening SGST ITC (₹)", min_value=0.0, value=0.0, step=100.0, key="auto_op_sgst")
    with op_col4:
        auto_op_csamt = st.number_input("Opening Cess ITC (₹)", min_value=0.0, value=0.0, step=100.0, key="auto_op_csamt")

    if gstr1_file and gstr2b_file:
        st.success("🎉 Documents staged successfully!")
        
        with st.spinner("Processing documents & compiling GSTR-3B payload..."):
            outward_supplies = extract_gstr1_data(gstr1_file)
            
            # Detect whether GSTR-2B file is PDF or Excel
            if gstr2b_file.name.lower().endswith(".pdf"):
                itc_eligible = extract_gstr2b_pdf(gstr2b_file)
            else:
                itc_eligible = extract_gstr2b_excel(gstr2b_file)
            
            # Compute Consolidated ITC (Opening + Current GSTR-2B Eligible)
            total_itc_iamt = auto_op_igst + itc_eligible["iamt"]
            total_itc_camt = auto_op_cgst + itc_eligible["camt"]
            total_itc_samt = auto_op_sgst + itc_eligible["samt"]
            total_itc_csamt = auto_op_csamt + itc_eligible["csamt"]

            ret_period = (st.session_state.get("month", "07") + st.session_state.get("fy", "2026")[-2:]).lower()
            gstin_val = st.session_state.get("gstin", "")

            gstr3b_payload = {
                "gstin": gstin_val,
                "ret_period": ret_period,
                "sup_details": {
                    "osup_det": outward_supplies,
                    "osup_zero": {"txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0},
                    "osup_nil_exmp": {"txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0},
                    "isup_rev": {"txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0},
                    "osup_nongst": {"txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0}
                },
                "itc_elg": {
                    "op_itc": {
                        "iamt": auto_op_igst,
                        "camt": auto_op_cgst,
                        "samt": auto_op_sgst,
                        "csamt": auto_op_csamt
                    },
                    "gstr2b_itc": itc_eligible,
                    "itc_avl": [
                        {
                            "ty": "OTH",
                            "iamt": total_itc_iamt,
                            "camt": total_itc_camt,
                            "samt": total_itc_samt,
                            "csamt": total_itc_csamt
                        }
                    ],
                    "itc_net": {
                        "iamt": total_itc_iamt,
                        "camt": total_itc_camt,
                        "samt": total_itc_samt,
                        "csamt": total_itc_csamt
                    }
                }
            }
            
        st.subheader("✅ Generated GSTR-3B JSON Preview")
        st.json(gstr3b_payload)
        
        json_string = json.dumps(gstr3b_payload, indent=4)
        
        st.download_button(
            label="📥 Download GSTR-3B JSON File",
            data=json_string,
            file_name=make_filename("GSTR3B_Payload", ext="json"),
            mime="application/json"
        )

    back_to_gstr3b_menu()

# --- SCREEN 4: GSTR-1 DASHBOARD ---
elif st.session_state.page == "gstr1_dashboard":
    col_logo, _ = st.columns([1, 4])
    with col_logo:
        if os.path.exists(get_path("logo_g.png")):
            img_g = Image.open(get_path("logo_g.png"))
            st.image(img_g, width=80)

    _, main_container, _ = st.columns([1.0, 2.0, 1.0])
    with main_container:
        with st.container():
            st.markdown('<h2 class="nav-title-fixed">GSTR-1 Outward Statement</h2>', unsafe_allow_html=True)
            st.markdown('<div class="prov-note">📜 <b>Proviso to Rule 59(1):</b> Current-period adjustments can be supplemented using optional Form GSTR-1A before filing GSTR-3B.</div>', unsafe_allow_html=True)
            
            row1_col1, row1_col2, row1_col3 = st.columns(3)
            with row1_col1:
                if st.button("B2B Invoices", use_container_width=True):
                    st.session_state.page = "b2b"
                    st.rerun()
            with row1_col2:
                if st.button("HSN Summary", use_container_width=True):
                    st.session_state.page = "hsn"
                    st.rerun()
            with row1_col3:
                if st.button("Doc Series", use_container_width=True):
                    st.session_state.page = "docs"
                    st.rerun()
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            row2_col1, row2_col2, row2_col3 = st.columns([0.5, 1, 0.5])
            with row2_col2:
                if st.button("B2C Small/Large", use_container_width=True):
                    st.session_state.page = "b2c"
                    st.rerun()
            
            st.markdown("<hr style='margin: 10px 0; border: 0.5px solid rgba(157, 78, 221, 0.3);'>", unsafe_allow_html=True)
            
            _, export_col, _ = st.columns([0.2, 1.6, 0.2])
            with export_col:
                if st.button("MASTER EXPORT (All-in-One)", type="primary", use_container_width=True):
                    st.session_state.page = "master"
                    st.rerun()
        
        _, back_btn_col, _ = st.columns([1, 1, 1])
        with back_btn_col:
            st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
            if st.button("← Back to Returns", use_container_width=False):
                st.session_state.page = "returns"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- SCREEN 5: B2B INVOICE EXTRACTOR ---
elif st.session_state.page == "b2b":
    st.markdown('<h2 class="nav-title-fixed">📊 B2B Invoices Extractor</h2>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload B2B Invoice (JPEG/PNG/PDF)", type=["jpg", "jpeg", "png", "pdf"], key="b2b_uploader")

    if uploaded_file is not None:
        is_pdf = uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf")
        file_bytes = uploaded_file.getvalue()

        if is_pdf:
            render_pdf_preview(file_bytes)
            model_input_part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Invoice Preview", use_container_width=True)
            model_input_part = image

        if st.button("🚀 Process & Generate Rows", type="primary"):
            if not st.session_state.api_key:
                st.error("Please enter your Gemini API Key in Configuration.")
            else:
                with st.spinner("Extracting B2B Tax Lines..."):
                    try:
                        client = genai.Client(api_key=st.session_state.api_key)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[model_input_part, "Extract B2B invoice details conforming strictly to the GSTR-1 schema. Separate tax rates into distinct lines."],
                            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=gstr1_json_schema, temperature=0.1),
                        )
                        extracted_data = json.loads(response.text)
                        rows_list = extracted_data.get("rows", [])
                        if rows_list:
                            df = pd.DataFrame(rows_list).reindex(columns=GSTR1_COLUMNS)
                            st.dataframe(df)
                            st.download_button("📥 Download B2B CSV", data=df.to_csv(index=False).encode('utf-8'), file_name=make_filename("B2B"), mime="text/csv")
                    except Exception as e:
                        st.error(f"Error: {e}")

    back_to_navigation()

# --- SCREEN 6: B2C CUMULATIVE EXTRACTOR ---
elif st.session_state.page == "b2c":
    st.markdown('<h2 class="nav-title-fixed">🛒 B2C Supplies Summary</h2>', unsafe_allow_html=True)
    st.markdown('<div class="prov-note">📜 <b>Section 37 Guidance:</b> Inter-State B2C invoices > ₹1,00,000 must be reported invoice-wise. Inter-State <= ₹1,00,000 and all Intra-State B2C supplies are aggregated by tax rate.</div>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader("Upload B2C Invoices (JPEG/PNG/PDF)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True, key="b2c_uploader")

    if uploaded_files:
        if st.button("🚀 Process B2C Aggregates", type="primary"):
            if not st.session_state.api_key:
                st.error("Please enter your Gemini API Key in Configuration.")
            else:
                all_extracted_rows = []
                progress_bar = st.progress(0)
                
                try:
                    client = genai.Client(api_key=st.session_state.api_key)
                    for index, uploaded_file in enumerate(uploaded_files):
                        is_pdf = uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf")
                        file_bytes = uploaded_file.getvalue()
                        model_input_part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf") if is_pdf else Image.open(uploaded_file)
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[model_input_part, "Extract retail/B2C invoice details. Place Of Supply must strictly follow 'Code-State Name'. Default Type to 'OE'."],
                            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=b2cs_json_schema, temperature=0.1),
                        )
                        rows_list = json.loads(response.text).get("rows", [])
                        all_extracted_rows.extend(rows_list)
                        progress_bar.progress((index + 1) / len(uploaded_files))
                    
                    if all_extracted_rows:
                        raw_df = pd.DataFrame(all_extracted_rows)
                        raw_df["Applicable % of Tax Rate"] = raw_df.get("Applicable % of Tax Rate", "").fillna("")
                        raw_df["E-Commerce GSTIN"] = raw_df.get("E-Commerce GSTIN", "").fillna("")
                        raw_df["Cess Amount"] = pd.to_numeric(raw_df.get("Cess Amount", 0.0)).fillna(0.0)
                        raw_df["Taxable Value"] = pd.to_numeric(raw_df.get("Taxable Value", 0.0)).fillna(0.0)
                        
                        group_cols = ["Type", "Place Of Supply", "Rate", "Applicable % of Tax Rate", "E-Commerce GSTIN"]
                        aggregated_df = raw_df.groupby(group_cols, as_index=False).agg({"Taxable Value": "sum", "Cess Amount": "sum"})
                        final_df = aggregated_df.reindex(columns=B2CS_COLUMNS)
                        
                        st.dataframe(final_df)
                        st.download_button("📥 Download Consolidated B2CS CSV", data=final_df.to_csv(index=False).encode('utf-8'), file_name=make_filename("B2CS"), mime="text/csv")
                except Exception as e:
                    st.error(f"Error: {e}")

    back_to_navigation()

# --- SCREEN 7: HSN SUMMARY EXTRACTOR ---
elif st.session_state.page == "hsn":
    st.markdown('<h2 class="nav-title-fixed">📝 HSN/SAC Table Summary</h2>', unsafe_allow_html=True)
    st.markdown('<div class="prov-note"><b>Notification No. 78/2020 CT:</b> Minimum 4 digits required for turnover <= ₹5 Crore (B2B). 6 digits mandatory for turnover > ₹5 Crore.</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Invoice (JPEG/PNG/PDF)", type=["jpg", "jpeg", "png", "pdf"], key="hsn_uploader")

    if uploaded_file is not None:
        is_pdf = uploaded_file.name.lower().endswith('.pdf')
        file_bytes = uploaded_file.getvalue()
        file_payload = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf") if is_pdf else Image.open(uploaded_file)

        if st.button("🔮 Generate Statutory HSN Summary", type="primary"):
            if not st.session_state.api_key:
                st.error("Please enter your Gemini API Key.")
            else:
                with st.spinner("Extracting HSN/SAC codes..."):
                    try:
                        client = genai.Client(api_key=st.session_state.api_key)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[file_payload, "Extract line items matching the HSN schema without manual rounding."],
                            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=hsn_json_schema, temperature=0.0),
                        )
                        rows_list = json.loads(response.text).get("rows", [])

                        if rows_list:
                            df = pd.DataFrame(rows_list)
                            df = df.groupby(["HSN", "UQC", "Rate"], as_index=False).agg({"Total Quantity": "sum", "Taxable Value": "sum"})
                            df["Central Tax Amount"] = round(df["Taxable Value"] * (df["Rate"] / 2) / 100, 2)
                            df["State/UT Tax Amount"] = df["Central Tax Amount"]
                            df["Integrated Tax Amount"] = 0.0
                            df["Cess Amount"] = 0.0
                            df["Total Value"] = round(df["Taxable Value"] + df["Central Tax Amount"] + df["State/UT Tax Amount"], 2)
                            df["Description"] = ""
                            df = df.reindex(columns=HSN_COLUMNS)
                            st.dataframe(df)
                            st.download_button("📥 Download HSN CSV", data=df.to_csv(index=False).encode('utf-8'), file_name=make_filename("HSN"), mime="text/csv")
                    except Exception as e:
                        st.error(f"Error: {e}")

    back_to_navigation()

# --- SCREEN 8: DOCUMENT SUMMARY SEQUENCE MANAGER ---
elif st.session_state.page == "docs":
    st.markdown('<h2 class="nav-title-fixed">📑 Document Series Table (Table 13)</h2>', unsafe_allow_html=True)
    
    st.markdown("### ➕ Manual Entry")
    with st.form("manual_doc_entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nature_doc = st.selectbox("Nature of Document", options=NATURE_OF_DOCUMENTS_OPTIONS, index=0)
            sr_from = st.text_input("Sr. No. From", placeholder="e.g., INV/001")
        with col2:
            sr_to = st.text_input("Sr. No. To", placeholder="e.g., INV/100")
            tot_num = st.number_input("Total Number", min_value=0, step=1, value=0)
        with col3:
            cancelled = st.number_input("Cancelled", min_value=0, step=1, value=0)
            st.write("<br>", unsafe_allow_html=True)
            submit_manual = st.form_submit_button("Add Record", type="primary")

        if submit_manual:
            if not nature_doc or not sr_from or not sr_to:
                st.error("Please fill in Nature of Document, Sr. No. From, and Sr. No. To.")
            else:
                new_row = pd.DataFrame([{
                    "Nature of Document": nature_doc,
                    "Sr. No. From": sr_from,
                    "Sr. No. To": sr_to,
                    "Total Number": int(tot_num),
                    "Cancelled": int(cancelled)
                }])
                st.session_state.docs_df = pd.concat([st.session_state.docs_df, new_row], ignore_index=True)
                st.success("Document sequence added manually.")

    st.markdown("---")
    st.markdown("### 🤖 Automated Extraction (PDF/CSV)")
    uploaded_docs_file = st.file_uploader("Upload Document Sequence Register (PDF or CSV)", type=["pdf", "csv"], key="docs_uploader")

    if uploaded_docs_file is not None:
        file_bytes = uploaded_docs_file.getvalue()
        if uploaded_docs_file.name.lower().endswith(".pdf"):
            render_pdf_preview(file_bytes)
            if st.button("🤖 AI Extract Serial Numbers", type="primary"):
                with st.spinner("Extracting..."):
                    try:
                        client = genai.Client(api_key=st.session_state.api_key)
                        model_input = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[model_input, "Extract document serial ranges issued during the period."],
                            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=docs_json_schema, temperature=0.1),
                        )
                        doc_rows = json.loads(response.text).get("documents", [])
                        if doc_rows:
                            extracted_df = pd.DataFrame(doc_rows).reindex(columns=DOCS_COLUMNS)
                            st.session_state.docs_df = pd.concat([st.session_state.docs_df, extracted_df], ignore_index=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
        elif uploaded_docs_file.name.lower().endswith(".csv"):
            if st.button("📄 Import CSV Data", type="primary"):
                try:
                    csv_df = pd.read_csv(io.BytesIO(file_bytes)).reindex(columns=DOCS_COLUMNS)
                    st.session_state.docs_df = pd.concat([st.session_state.docs_df, csv_df], ignore_index=True)
                    st.success("CSV records imported successfully.")
                except Exception as e:
                    st.error(f"Error loading CSV: {e}")

    st.markdown("---")
    st.markdown("### Current Document Series Register")
    
    if not st.session_state.docs_df.empty:
        st.session_state.docs_df = st.data_editor(st.session_state.docs_df, num_rows="dynamic", key="docs_editor")
        
        col_dl_csv, col_clear = st.columns([1, 1])
        with col_dl_csv:
            st.download_button(
                "📥 Download Document Series CSV",
                data=st.session_state.docs_df.to_csv(index=False).encode('utf-8'),
                file_name=make_filename("Document_Series"),
                mime="text/csv",
                use_container_width=True
            )
        with col_clear:
            if st.button("🗑️ Clear Table", use_container_width=True):
                st.session_state.docs_df = pd.DataFrame(columns=DOCS_COLUMNS)
                st.rerun()
    else:
        st.info("No document sequence data entered or extracted yet.")

    back_to_navigation()

# --- SCREEN 9: MASTER EXPORT ---
elif st.session_state.page == "master":
    st.markdown('<h2 class="nav-title-fixed">📦 Consolidated GSTR-1 Master Pipeline</h2>', unsafe_allow_html=True)
    master_file = st.file_uploader("Upload Master Tax Register (PDF)", type=["pdf"], key="master_uploader")

    if master_file is not None:
        file_bytes = master_file.getvalue()
        render_pdf_preview(file_bytes)

        if st.button("⚡ Execute All Extractions & Build Excel", type="primary"):
            if not st.session_state.api_key:
                st.error("Please configure API Key.")
            else:
                b2b_df, b2c_df, hsn_df, docs_df = pd.DataFrame(columns=GSTR1_COLUMNS), pd.DataFrame(columns=B2CS_COLUMNS), pd.DataFrame(columns=HSN_COLUMNS), pd.DataFrame(columns=DOCS_COLUMNS)
                client = genai.Client(api_key=st.session_state.api_key)
                model_input = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")

                with st.spinner("Extracting B2B, B2C, HSN & Document Schedules..."):
                    # Pipeline execution
                    try:
                        res1 = client.models.generate_content(model='gemini-2.5-flash', contents=[model_input, "Extract B2B invoice details."], config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=gstr1_json_schema, temperature=0.1))
                        r1 = json.loads(res1.text).get("rows", [])
                        if r1: b2b_df = pd.DataFrame(r1).reindex(columns=GSTR1_COLUMNS)
                    except Exception: pass

                    try:
                        res2 = client.models.generate_content(model='gemini-2.5-flash', contents=[model_input, "Extract raw line items for HSN."], config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=hsn_json_schema, temperature=0.0))
                        r2 = json.loads(res2.text).get("rows", [])
                        if r2:
                            raw_hsn = pd.DataFrame(r2).groupby(["HSN", "UQC", "Rate"], as_index=False).agg({"Total Quantity": "sum", "Taxable Value": "sum"})
                            raw_hsn["Central Tax Amount"] = round(raw_hsn["Taxable Value"] * (raw_hsn["Rate"] / 2) / 100, 2)
                            raw_hsn["State/UT Tax Amount"] = raw_hsn["Central Tax Amount"]
                            raw_hsn["Integrated Tax Amount"] = 0.0
                            raw_hsn["Cess Amount"] = 0.0
                            raw_hsn["Total Value"] = round(raw_hsn["Taxable Value"] + raw_hsn["Central Tax Amount"] + raw_hsn["State/UT Tax Amount"], 2)
                            raw_hsn["Description"] = ""
                            hsn_df = raw_hsn.reindex(columns=HSN_COLUMNS)
                    except Exception: pass

                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    b2b_df.to_excel(writer, sheet_name="B2B Invoices", index=False)
                    b2c_df.to_excel(writer, sheet_name="B2C Summary", index=False)
                    hsn_df.to_excel(writer, sheet_name="HSN Summary", index=False)
                    docs_df.to_excel(writer, sheet_name="Document Series", index=False)
                
                st.success("🎉 Consolidated Workbook Built!")
                st.download_button(
                    label="📥 Download Master Consolidated Workbook (.xlsx)",
                    data=excel_buffer.getvalue(),
                    file_name=make_filename("MasterConsolidated", ext="xlsx"),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    back_to_navigation()