import streamlit as st
import subprocess
import os

st.set_page_config(page_title="NGOBOX Scraper", layout="wide")

st.title("📄 NGOBOX Grants & Tenders Scraper")
st.markdown("Click the button below to run the scraper and download the latest Excel file.")

if st.button("🚀 Run Scraper"):
    with st.spinner("Running scraper... Please wait ⏳"):
        try:
            result = subprocess.run(["python", "main_scraper.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ Scraper finished successfully!")
                if os.path.exists("relevant_grants.xlsx"):
                    with open("relevant_grants.xlsx", "rb") as f:
                        st.download_button("📥 Download Excel", f, file_name="relevant_grants.xlsx")
            else:
                st.error("❌ Scraper failed!")
                st.text(result.stderr)
        except Exception as e:
            st.error(f"Exception occurred: {e}")
