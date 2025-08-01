import streamlit as st
import subprocess
import os
import sys

# Ensure we are in the same directory as app.py (important for Streamlit Cloud)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set page configuration
st.set_page_config(page_title="NGOBOX Scraper", layout="wide")

def run_scraper_and_stream_logs():
    """Run main_scraper.py and stream logs to Streamlit."""
    # Launch main_scraper.py as a subprocess
    process = subprocess.Popen(
        [sys.executable, "main_scraper.py"],  # sys.executable ensures correct Python env
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    logs = ""
    log_placeholder = st.empty()

    # Stream stdout line by line
    for line in process.stdout:
        logs += line
        log_placeholder.text(logs)  # Update logs in the app

    process.wait()  # Wait for process to complete

    return process.returncode


def main():
    st.title("📄 NGOBOX Grants & Tenders Scraper")
    st.markdown("Click the button below to run the scraper and download the latest Excel file.")

    if st.button("🚀 Run Scraper"):
        with st.spinner("Running scraper... Please wait ⏳"):
            return_code = run_scraper_and_stream_logs()

            if return_code == 0:
                st.success("✅ Scraper finished successfully!")
                excel_path = "output/relevant_grants.xlsx"

                if os.path.exists(excel_path):
                    with open(excel_path, "rb") as f:
                        st.download_button("📥 Download Excel", f, file_name="relevant_grants.xlsx")
                else:
                    st.warning("⚠️ Excel file not found. Check logs for details.")
            else:
                st.error("❌ Scraper failed. Check logs above for details.")


if __name__ == "__main__":
    main()
