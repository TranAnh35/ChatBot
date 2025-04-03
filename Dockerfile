#INSTRUCTION args
# Using a  base image for CPU & GPU
ARG BASE_IMAGE=python:3.11
FROM ${BASE_IMAGE} AS base

# Set the working directory in the container
WORKDIR /app

# Copy source code into the container
COPY src/backend /app
#COPY ./app

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose API port (8000 for FastAPI)
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
