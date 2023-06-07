FROM python:3.9-slim-buster
LABEL authors="Danila Kuzmiankou"
WORKDIR /main

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD ["python3", "./main.py"]

# Build with: docker build --tag discord-music-bot .
# Run with: docker run discord-music-bot