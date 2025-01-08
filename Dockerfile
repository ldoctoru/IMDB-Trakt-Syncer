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
    apt-transport-https && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone the IMDB-Trakt-Syncer repository into the /app directory
RUN git clone https://github.com/RileyXX/IMDB-Trakt-Syncer.git /app

# Set the working directory to /app
WORKDIR /app/IMDBTraktSyncer

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose a volume for persistent data (e.g., credentials)
VOLUME ["/config"]

# Entry point for running the script
ENTRYPOINT ["python", "/app/IMDBTraktSyncerIMDBTraktSyncer.py"]

# Default command (can be overridden)
CMD ["--help"]