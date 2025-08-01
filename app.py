import streamlit as st
import subprocess

st.set_page_config(page_title="NGOBOX Scraper", layout="wide")

st.title("📄 NGOBOX Web Scraper")
st.write("Click below to run the scraper. Output will be saved to `relevant_grants.xlsx`.")

if st.button("Run Scraper"):
    with st.spinner("Scraping in progress..."):
        result = subprocess.run(["python", "main_scraper.py"], capture_output=True, text=True)
        st.text(result.stdout)
        st.error(result.stderr) if result.stderr else st.success("✅ Scraping completed.")
