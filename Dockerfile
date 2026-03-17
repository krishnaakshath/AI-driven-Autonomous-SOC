FROM python:3.10-slim

# Set environment variables to ensure Python runs optimally in Docker
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    DEBIAN_FRONTEND=noninteractive

# Set the working directory directly in the container
WORKDIR /app

# Install system dependencies required for compilation and running certain ML/crypto libraries
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpcap-dev \\
    libpq-dev \\
    python3-dev \\
    gcc \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container WORKDIR
COPY . .

# Expose the standard Streamlit port
EXPOSE 8501

# Add a healthcheck so Docker knows when the application is actually up and running
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Command to run the Streamlit application
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
