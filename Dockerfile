# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for the database with proper permissions
RUN mkdir -p /app/instance && chmod 777 /app/instance

# Copy the rest of the application
COPY . .

# Update SQLAlchemy configuration to use instance folder
RUN sed -i 's/sqlite:\/\/\/quiz.db/sqlite:\/\/\/\/app\/instance\/quiz.db/g' app.py

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"] 