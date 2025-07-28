import streamlit as st
from main_scraper import run_scraper
import os

st.set_page_config(page_title="NGOBOX Scraper", layout="centered")

st.title("📄 NGOBOX Grant Scraper")

st.write("Click the button below to run the scraper and generate the Excel report:")

if st.button("🚀 Generate Excel File"):
    with st.spinner("Running scraper, please wait..."):
        run_scraper()
    output_path = 'output/relevant_grants.xlsx'
    if os.path.exists(output_path):
        with open(output_path, "rb") as file:
            btn = st.download_button(
                label="📥 Download Excel File",
                data=file,
                file_name="relevant_grants.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.success("✅ Done! Click above to download.")
    else:
        st.error("❌ Excel file not found.")
