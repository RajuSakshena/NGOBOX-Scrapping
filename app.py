import streamlit as st
from main_scraper import run_scraper
import os

st.set_page_config(page_title="Grant Scraper", layout="centered")

st.title("🧾 NGOBOX Grants & Tenders Scraper")
st.write("Click the button below to fetch opportunities from the latest 5 pages of Grants and Tenders.")

if st.button("🚀 Run Scraper"):
    with st.spinner("Scraping in progress..."):
        run_scraper()

    file_path = "output/relevant_grants.xlsx"
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.success("✅ Scraping complete!")
            st.download_button("📥 Download Excel File", f, file_name="relevant_grants.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("❌ No file generated.")
