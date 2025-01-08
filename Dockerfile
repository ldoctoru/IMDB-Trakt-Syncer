# Use a lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PERSISTENT_DIR=/data
ENV XDG_CONFIG_HOME=/data

# Add the Python packages path to PYTHONPATH
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages:$PYTHONPATH

# Set the working directory
WORKDIR /app

# Install required system dependencies for Chrome/Chromium and WebDriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libxss1 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    && apt-get clean

# Install Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install \
    && rm google-chrome-stable_current_amd64.deb

# Upgrade pip and install IMDBTraktSyncer
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install --no-cache-dir IMDBTraktSyncer

# Verify installation
RUN python3 -c "import IMDBTraktSyncer; print('IMDBTraktSyncer is installed correctly')"

# Create a persistent data directory
RUN mkdir -p /data

# Change to persistent directory for all operations
WORKDIR /data

# Set the default command to run IMDBTraktSyncer and keep the container alive
CMD ["bash", "-c", "IMDBTraktSyncer && tail -f /dev/null"]