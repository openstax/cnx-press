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

# Needed for testing
RUN set -x \
    && apt-get update \
    && apt-get install wamerican curl --no-install-recommends -y


# ###
# Java install,
#   copied from https://github.com/docker-library/openjdk/blob/93316d3b14379d29fe0cd363bd6839eb8dd8cc7b/7-jre/Dockerfile
# ###

# A few problems with compiling Java from source:
#  1. Oracle.  Licensing prevents us from redistributing the official JDK.
#  2. Compiling OpenJDK also requires the JDK to be installed, and it gets
#       really hairy.

RUN apt-get update && apt-get install -y --no-install-recommends \
		bzip2 \
		unzip \
		xz-utils \
	&& rm -rf /var/lib/apt/lists/*

# Default to UTF-8 file.encoding
ENV LANG C.UTF-8

# add a simple script that can auto-detect the appropriate JAVA_HOME value
# based on whether the JDK or only the JRE is installed
RUN { \
		echo '#!/bin/sh'; \
		echo 'set -e'; \
		echo; \
		echo 'dirname "$(dirname "$(readlink -f "$(which javac || which java)")")"'; \
	} > /usr/local/bin/docker-java-home \
	&& chmod +x /usr/local/bin/docker-java-home

# do some fancy footwork to create a JAVA_HOME that's cross-architecture-safe
RUN ln -svT "/usr/lib/jvm/java-7-openjdk-$(dpkg --print-architecture)" /docker-java-home
ENV JAVA_HOME /docker-java-home/jre

RUN set -ex; \
	\
	apt-get update; \
	apt-get install -y openjdk-7-jre-headless; \
	rm -rf /var/lib/apt/lists/*; \
	\
# verify that "docker-java-home" returns what we expect
	[ "$(readlink -f "$JAVA_HOME")" = "$(docker-java-home)" ]; \
	\
# update-alternatives so that future installs of other OpenJDK versions don't change /usr/bin/java
	update-alternatives --get-selections | awk -v home="$(readlink -f "$JAVA_HOME")" 'index($3, home) == 1 { $2 = "manual"; print | "update-alternatives --set-selections" }'; \
# ... and verify that it actually worked for one of the alternatives we care about
	update-alternatives --query java | grep -q 'Status: manual'

# ###
# / End copy for Java Install
# ###


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
