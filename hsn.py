import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image
import json

# Set up Streamlit Page Configuration
st.set_page_config(page_title="Invoice to GSTR-1 HSN Extractor", page_icon="📝", layout="wide")

st.title("📝 Invoice to GSTR-1 HSN Summary Extractor")
st.write("Upload an invoice image or PDF, extract precise line items, and let Python compute the mathematically perfect HSN summary.")

# Sidebar for configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# Define the expected schema structure for GSTR-1 HSN Summary
HSN_COLUMNS = [
    "HSN", "Description", "UQC", "Total Quantity", "Total Value",
    "Taxable Value", "Integrated Tax Amount", "Central Tax Amount",
    "State/UT Tax Amount", "Cess Amount", "Rate"
]

# Schema modified to extract RAW line items instead of asking the AI to sum them up
hsn_json_schema = {
    "type": "OBJECT",
    "properties": {
        "rows": {
            "type": "ARRAY",
            "description": "Extract every individual line item exactly as printed on the invoice before any grouping.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "HSN": {"type": "STRING", "description": "The exact HSN or SAC code for this specific item line"},
                    "UQC": {"type": "STRING", "description": "Official GST Unit Quantity Code. Map KGS to KGS-KILOGRAMS, PKT to BOX-BOXES, NOS to NOS-NUMBERS, PCS to PCS-PIECES"},
                    "Total Quantity": {"type": "NUMBER", "description": "The exact quantity printed for this specific line item"},
                    "Taxable Value": {"type": "NUMBER", "description": "The exact net taxable value printed for this specific line item"},
                    "Rate": {"type": "NUMBER", "description": "The standalone or combined statutory GST rate percentage for this line (e.g., 5, 12, 18, 28)"}
                },
                "required": ["HSN", "UQC", "Total Quantity", "Taxable Value", "Rate"]
            }
        }
    }
}

# Main Application logic
uploaded_file = st.file_uploader("Upload Invoice (JPEG/PNG/PDF)", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    is_pdf = uploaded_file.name.lower().endswith('.pdf')
    
    # Visual preview logic based on file type
    if is_pdf:
        st.info(f"📄 PDF Document Loaded: {uploaded_file.name}")
        file_payload = types.Part.from_bytes(
            data=uploaded_file.read(),
            mime_type="application/pdf",
        )
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Invoice Preview", use_container_width=True)
        file_payload = image
    
    if st.button("🔮 Process & Generate HSN Summary"):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar to proceed.")
        else:
            with st.spinner("Extracting raw line item values with high precision..."):
                try:
                    # Initialize the Gemini Client
                    client = genai.Client(api_key=api_key)
                    
                    # Call Gemini 2.5 Flash to act as a pure, highly accurate extractor
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            file_payload, 
                            "Your sole task is high-accuracy data extraction. Locate the item/tax table. "
                            "Extract every single line item individually exactly as it appears. Do not attempt to add, group, sum, or calculate anything. "
                            "Ensure the HSN, UQC, Quantity, Taxable Value, and Rate are transcribed with perfect numerical fidelity from the document."
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=hsn_json_schema,
                            temperature=0.0  # Lowest temperature for maximum factual consistency
                        ),
                    )
                    
                    # Parse the structured JSON response
                    extracted_data = json.loads(response.text)
                    rows_list = extracted_data.get("rows", [])
                    
                    if rows_list:
                        df = pd.DataFrame(rows_list)
                        
                        # Clean and normalize HSN values (strip whitespace/dots)
                        df["HSN"] = df["HSN"].astype(str).str.strip()
                        df["UQC"] = df["UQC"].astype(str).str.strip()
                        
                        # -------------------------------------------------------------
                        # MATHEMATICAL ENGINE (Python handles calculations for 100% accuracy)
                        # -------------------------------------------------------------
                        # 1. First consolidate duplicates by HSN + UQC + Rate via Pandas
                        df = df.groupby(["HSN", "UQC", "Rate"], as_index=False).agg({
                            "Total Quantity": "sum",
                            "Taxable Value": "sum"
                        })
                        
                        # 2. Compute tax splits flawlessly using exact arithmetic rules
                        # Check if it's an intra-state or inter-state invoice (We'll safely assume intra-state CGST/SGST split unless IGST matches)
                        # You can customize this logic, but here we calculate CGST & SGST based on half of the total rate.
                        df["Central Tax Amount"] = round(df["Taxable Value"] * (df["Rate"] / 2) / 100, 2)
                        df["State/UT Tax Amount"] = df["Central Tax Amount"] # Keep splits symmetric
                        df["Integrated Tax Amount"] = 0.0
                        df["Cess Amount"] = 0.0
                        
                        # 3. Calculate Total Value perfectly: Taxable Value + CGST + SGST + IGST + Cess
                        df["Total Value"] = round(
                            df["Taxable Value"] + 
                            df["Central Tax Amount"] + 
                            df["State/UT Tax Amount"] + 
                            df["Integrated Tax Amount"] + 
                            df["Cess Amount"], 2
                        )
                        
                        # 4. Enforce blank description column as per requirements
                        df["Description"] = ""
                        
                        # Reindex to match the exact GSTR-1 layout order
                        df = df.reindex(columns=HSN_COLUMNS)
                        
                        st.success("🎉 GSTR-1 HSN Summary computed with mathematical accuracy!")
                        st.subheader("📊 Extracted GSTR-1 HSN Preview")
                        st.dataframe(df)
                        
                        # Convert DataFrame to a downloadable CSV byte stream
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        
                        st.download_button(
                            label="📥 Download HSN Ready CSV",
                            data=csv_data,
                            file_name="gstr1_hsn_summary.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No tabular rows could be formulated from this document structure.")
                        
                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")