# Use a multi-platform compatible base image
FROM --platform=$BUILDPLATFORM python:3.9-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    xvfb \
    git \
    curl \
    gnupg \
    chromium \
    chromium-driver \
    gcc \
    libffi-dev \
    python3-dev \
    build-essential \
    apt-transport-https && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone the IMDB-Trakt-Syncer repository into /app
RUN git clone https://github.com/ldoctoru/IMDB-Trakt-Syncer.git /app

# Set the working directory
WORKDIR /app/IMDBTraktSyncer

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Expose a volume for persistent data (e.g., credentials)
VOLUME ["/config"]

# Copy the entrypoint script into the container
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the custom entrypoint script
ENTRYPOINT ["/entrypoint.sh"]