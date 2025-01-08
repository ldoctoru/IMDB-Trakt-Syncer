# Use a lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PERSISTENT_DIR=/data
ENV XDG_CONFIG_HOME=/data
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages:$PYTHONPATH

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    cron \
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

# Install IMDBTraktSyncer
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install --no-cache-dir IMDBTraktSyncer

# Create persistent data directory
RUN mkdir -p /data && chmod -R 777 /data

# Modify IMDBTraktSyncer to save settings in /data
RUN sed -i 's|credentials.txt|/data/credentials.txt|g' /usr/local/lib/python3.10/site-packages/IMDBTraktSyncer/*.py \
    && sed -i 's|log.txt|/data/log.txt|g' /usr/local/lib/python3.10/site-packages/IMDBTraktSyncer/*.py

# Set working directory
WORKDIR /data

# Configure cron to run IMDBTraktSyncer every 12 hours
RUN echo "0 */12 * * * /usr/local/bin/IMDBTraktSyncer >> /data/cron.log 2>&1" > /etc/cron.d/imdbtrakt-cron \
    && chmod 0644 /etc/cron.d/imdbtrakt-cron \
    && crontab /etc/cron.d/imdbtrakt-cron

# Ensure cron logs are written to /data/cron.log
RUN touch /data/cron.log && chmod 666 /data/cron.log

# Default command
CMD ["bash", "-c", "IMDBTraktSyncer && tail -f /dev/null"]