#!/bin/bash

# Navigate to your project directory
cd backend

# Perform a git pull to update the code
git pull

# install packages
sudo docker compose run --rm backend pip install -r requirements.txt

sudo docker compose up -d --build backend
sudo docker compose up -d --build celery-worker
sudo docker compose up -d --build celery-beat

#sudo docker compose run --rm backend python manage.py migrate --fake
sudo docker compose run --rm backend python manage.py migrate
# Restart Docker Compose services
# docker-compose up -d backend nginx

# remove danging images
echo "Running Docker image prune..."
yes | sudo docker image prune
