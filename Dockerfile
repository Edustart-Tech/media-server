# Use an official Python runtime as a parent image
FROM python:3.11.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Collect static files for production (adjust if needed)
RUN python manage.py collectstatic --noinput

# Expose the port the app will run on (usually 8000 for Django)
EXPOSE 8000

# Start the application using Gunicorn
#CMD ["gunicorn", "media_manager.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
