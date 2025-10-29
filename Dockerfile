FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for pdfquery
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application
COPY radiology_report_generator.py .

# Create directories for credentials and output
RUN mkdir -p /app/credentials /app/output /app/temp_pdfs

# Set environment variable placeholder (will be overridden at runtime)
ENV GOOGLE_API_KEY=""

# Volume mounts for:
# - credentials: Google Drive API credentials
# - output: Generated reports
VOLUME ["/app/credentials", "/app/output"]

# Run the application
CMD ["python", "radiology_report_generator.py"]
