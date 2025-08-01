if st.button("🚀 Run Scraper"):
    with st.spinner("Running scraper... Please wait ⏳"):
        process = subprocess.Popen(
            ["python", "main_scraper.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        log_placeholder = st.empty()
        logs = ""
        for line in process.stdout:
            logs += line
            log_placeholder.text(logs)
        process.wait()

        if process.returncode == 0:
            st.success("✅ Scraper finished successfully!")
            ...
