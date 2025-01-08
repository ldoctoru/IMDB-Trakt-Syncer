# Use a lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install IMDBTraktSyncer
RUN pip install IMDBTraktSyncer --upgrade

# Create a volume for persistent data
VOLUME ["/data"]

# Set the default persistent directory as an environment variable
ENV PERSISTENT_DIR=/data

# Keep the container running by starting an interactive bash session
CMD ["bash", "-c", "while true; do sleep 30; done"]