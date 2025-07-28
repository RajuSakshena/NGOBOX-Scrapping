import streamlit as st
from main_scraper import run_scraper
import os

st.set_page_config(page_title="NGOBOX Scraper", layout="centered")
st.title("🧾 NGOBOX Grant & Tender Scraper")
st.write("Click the button below to run the scraper and see logs")

if st.button("🚀 Run Scraper"):
    with st.spinner("Running the scraper... please wait ~30 sec."):
        run_scraper()

    file_path = "output/relevant_grants.xlsx"
    st.write("Checking for output file path →", file_path)

    if os.path.exists(file_path):
        st.success("✅ Done! File generated.")
        with open(file_path, "rb") as f:
            st.download_button(
                label="📥 Download Excel File",
                data=f,
                file_name="relevant_grants.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("❌ No file generated.")
        st.write("❗ Looks like the scraper did not generate the Excel file.")
        st.write("List current files in project:")
        # List directory to help debug
        for root, dirs, files in os.walk("."):
            st.write(root, files)
