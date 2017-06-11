FROM python:3.6-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app/

# Install System Dependencies
RUN set -x \
    && apt-get update \
    && apt-get install httpie -y \
    && apt-get install git --no-install-recommends -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN set -x \
    && apt-get update \
    && apt-get install inotify-tools build-essential --no-install-recommends -y

COPY requirements /tmp/requirements

# Install Python Dependencies
RUN set -x \
    && pip install -U pip setuptools wheel \
    && pip install -r /tmp/requirements/test.txt \
    && pip install -r /tmp/requirements/deploy.txt \
                   -r /tmp/requirements/main.txt \
    && find /usr/local -type f -name '*.pyc' -name '*.pyo' -delete \
    && rm -rf ~/.cache/

# Copy the project into the container
COPY . /app/

# Set the working directory for our app
WORKDIR /app/
