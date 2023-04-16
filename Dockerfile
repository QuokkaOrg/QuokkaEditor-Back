FROM python:3.11

RUN useradd -ms /bin/bash docker-user

RUN apt-get -y update \
    && apt-get install -y gettext git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSl https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=1.4.2 python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /app
COPY poetry.lock pyproject.toml README.md /app/

ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

COPY src/quokka_editor_back ./src/quokka_editor_back
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install ; else poetry install --no-dev ; fi"

EXPOSE 8080

CMD gunicorn --config src/quokka_editor_back/gunicorn.conf.py quokka_editor_back.api.app:app