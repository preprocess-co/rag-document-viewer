# Use --platform to specify architecture
FROM --platform=linux/amd64 ubuntu:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies including Python3 and pip3
RUN apt update && apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    libglib2.0-0 \
    libfreetype6 \
    libfontconfig1 \
    libcairo2 \
    libpng16-16 \
    libjpeg-turbo8 \
    libxml2 \
    wget \
    libreoffice \
    && apt upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip (optional, for convenience)
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

RUN python3 -m pip config set global.break-system-packages true

# Set working directory
WORKDIR /var/app

# Copy and install PDF2htmlEX
RUN wget "https://raw.githubusercontent.com/preprocess-co/rag-document-viewer/refs/heads/main/install.sh" -O ./install.sh
RUN chmod +x install.sh && ./install.sh

# Copy Python requirements and install dependencies
RUN wget "https://raw.githubusercontent.com/preprocess-co/rag-document-viewer/refs/heads/main/demo/install.txt"
# COPY install.txt install.txt
RUN pip3 install --no-cache-dir --upgrade -r install.txt

# Copy application code
RUN wget "https://raw.githubusercontent.com/preprocess-co/rag-document-viewer/refs/heads/main/demo/server.py"
# COPY server.py server.py

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:80", "--capture-output", "server:app", "--timeout=600", "--workers=10"]