FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY ../../requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . ./src/api/

# Expose port
EXPOSE 8000

# Command to run the FastAPI application
CMD ["fastapi", "run", "src/api/main.py", "--host", "0.0.0.0", "--port", "8000"]