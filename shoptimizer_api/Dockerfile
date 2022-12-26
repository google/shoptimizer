FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV FLASK_APP "main.py"
# Force stdin, stdout and stderr to be totally unbuffered.
ENV PYTHONUNBUFFERED 1
# The product's customLabel field that will be set to track optimization.
# Set to "customLabel{0-4}".
# Items can be filtered by this label in Google Ads to track optimization performance.
# Leave empty to turn off tracking.
# Ref: https://developers.google.com/shopping-content/v2/reference/v2/products#resource -> see customLabel
ENV PRODUCT_TRACKING_FIELD "customLabel4"

RUN mkdir /app
WORKDIR /app

# Install Mecab for language processing
RUN apt-get update && apt-get -y install mecab libmecab-dev mecab-ipadic-utf8 git make curl xz-utils file sudo

# Set up Mecab
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
RUN echo yes | mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -a
RUN cp /etc/mecabrc /usr/local/etc/

# Copy requirements.txt to app/
COPY requirements.txt /app/

# Install packages using pip.
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Add all files in Dockerfile directory to /app (can ignore files with .dockerignore)
ADD . /app

# Install production dependencies.
RUN pip install gunicorn tensorflow

# Run gunicorn starting main.py/app object, binding IP:port
CMD exec gunicorn --bind :$PORT --workers 1 --threads 6 --timeout 0 main:app
