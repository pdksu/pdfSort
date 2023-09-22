FROM python:3.9-slim

# Update and install system libraries
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libglib2.0-0
WORKDIR /app

# Copy the requirements and install them
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the bars directory (and its contents) to /app
COPY bars/ /app/bars/

# Copy the templates directory to /app
COPY templates/ /app/templates/

# Copy the entrypoint script
COPY entrypoint.sh /app/

# Adjust the PYTHONPATH to include the /app directory, so Python can find the 'bars' module.
ENV PYTHONPATH=/app
ENTRYPOINT ["/app/entrypoint.sh"]