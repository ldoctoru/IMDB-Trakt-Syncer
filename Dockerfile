# Use a lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PERSISTENT_DIR=/data
ENV XDG_CONFIG_HOME=/data

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

# Install IMDBTraktSyncer and dependencies
RUN python -m pip install --upgrade pip \
    && pip install IMDBTraktSyncer

# Create a persistent data directory
RUN mkdir -p /data/settings \
    && rm -rf /usr/local/lib/python3.10/site-packages/IMDBTraktSyncer \
    && ln -s /data/settings /usr/local/lib/python3.10/site-packages/IMDBTraktSyncer

# Change to persistent directory for all operations
WORKDIR /data

# Set the default command to run IMDBTraktSyncer and keep the container running
CMD ["bash", "-c", "IMDBTraktSyncer && tail -f /dev/null"]