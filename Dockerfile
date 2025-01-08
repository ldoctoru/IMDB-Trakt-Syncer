# Use a lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install IMDBTraktSyncer
RUN pip install IMDBTraktSyncer --upgrade

# Create a volume for persistent data
VOLUME ["/config"]

# Set the default persistent directory as an environment variable
ENV PERSISTENT_DIR=/config

# Default command to display help (can be overridden)
CMD ["IMDBTraktSyncer", "--help"]