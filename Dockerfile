# run like following to build the image
# docker build -t notipy .

FROM python:3.12
RUN apt-get update && apt-get upgrade -y
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt