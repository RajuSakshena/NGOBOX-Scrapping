import streamlit as st
from main_scraper import run_scraper
import os

st.set_page_config(page_title="NGOBOX Scraper", layout="centered")
st.title("📊 NGOBOX Grants & Tenders Scraper")
st.write("Click the button below to scrape Grants and Tenders data (first 5 pages only).")

if st.button("🚀 Run Scraper"):
    with st.spinner("⏳ Scraping in progress... please wait..."):
        run_scraper()

    file_path = "relevant_grants.xlsx"
    st.write(f"📁 Checking for output file path → `{file_path}`")

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.success("✅ Scraping complete! File generated.")
            st.download_button(
                label="📥 Download Excel File",
                data=f,
                file_name="relevant_grants.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("❌ No file generated.")
        st.info("Make sure the `run_scraper()` function saves the file to the root directory (not inside `output/`).")
