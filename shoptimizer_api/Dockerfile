FROM python:3.12-slim

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

# Set up virtualenv path so it is used automatically
ENV PATH="/app/.venv/bin:$PATH"
# Tell uv to copy files instead of hardlinking
ENV UV_LINK_MODE=copy


RUN mkdir /app
WORKDIR /app

# Install Mecab for language processing
RUN apt-get update && apt-get -y install mecab libmecab-dev mecab-ipadic-utf8 git make curl xz-utils file sudo

# Set up Mecab
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
RUN echo yes | mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -a
RUN cp /etc/mecabrc /usr/local/etc/

# Copy dependency definition files
COPY pyproject.toml uv.lock /app/

# Install uv and sync dependencies
RUN pip install --upgrade pip uv && \
    uv sync --frozen --no-dev --no-install-project

# Add all files in Dockerfile directory to /app (can ignore files with .dockerignore)
ADD . /app

# Run gunicorn starting main.py/app object, binding IP:port
CMD exec gunicorn --bind :$PORT --workers 1 --threads 6 --timeout 0 main:app
