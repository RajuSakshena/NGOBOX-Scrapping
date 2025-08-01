FROM python:3.10-slim

# Install system dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libnspr4 libnss3 libxss1 xdg-utils libu2f-udev libvulkan1 \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Set environment variables so Chrome runs properly
ENV CHROME_BIN=/usr/bin/google-chrome
ENV DISPLAY=:99

# Set work directory
WORKDIR /app

# Copy everything
COPY . .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit port
EXPOSE 8501

# Start the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]






