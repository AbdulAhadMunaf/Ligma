# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for Python buffering and prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install MySQL client development packages
RUN apt-get update && apt-get install -y \
  default-libmysqlclient-dev \
  libpango1.0-dev \
  libffi-dev \
  pkg-config \
  gcc \
  pkg-config \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy the current directory contents into the container at /app
COPY . /app/
RUN python manage.py collectstatic --noinput

# Expose the port that the application runs on
EXPOSE 8000
