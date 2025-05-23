# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install PowerShell Core and dependencies
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	curl \
	ca-certificates \
	apt-transport-https \
	gnupg \
	libc6 \
	libgcc1 \
	libgssapi-krb5-2 \
	libstdc++6 \
	zlib1g \
	wget && \
	# Download and import Microsoft repository GPG keys
	wget -q "https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb" && \
	dpkg -i packages-microsoft-prod.deb && \
	rm packages-microsoft-prod.deb && \
	# Update package list and install PowerShell
	apt-get update && \
	apt-get install -y powershell && \
	# Clean up
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/command_history

# Expose the port
EXPOSE 8080

# Create a non-root user and switch to it
RUN useradd -m mcpuser && \
	chown -R mcpuser:mcpuser /app
USER mcpuser

# Set the PowerShell execution policy for the container
RUN pwsh -Command "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force"

# Command to run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
