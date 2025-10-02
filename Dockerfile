FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY gunicorn.docker.conf.py .

# Expose port
EXPOSE 8000

# Run with --preload for postfork() best practice
# This uses gunicorn.docker.conf.py which calls client.postfork()
CMD ["gunicorn", "--config", "gunicorn.docker.conf.py", "--preload", "app:app"] 