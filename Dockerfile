# Use a Python base image with a specific version
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies including build tools
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver

# Copy requirements.txt and install Python dependencies.
# We do this before copying the rest of the app to leverage Docker's build cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application files
COPY . /app

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit app when the container launches
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
