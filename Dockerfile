FROM registry.gitlab.com/sandlabs/prospector-3.7-slim:latest

WORKDIR /opt/app
COPY pyproject.toml poetry.lock ./

RUN export BUILD_DEPS='git build-essential cmake' && \
    apt-get -qq update && \
    apt-get -y install --no-install-recommends $BUILD_DEPS && \
    poetry install --no-interaction --no-root --no-dev && \
    apt-get -y purge --auto-remove $BUILD_DEPS && \
    rm -rf /var/lib/apt/lists/*

COPY ./ ./

ENV IS_DOCKER=1 PRODUCTION=1 DEVELOP=0 PYTHONPATH=/opt/app
CMD /bin/bash -c "python main.py"
