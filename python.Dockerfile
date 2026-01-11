FROM ubuntu:noble

ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSIONS="3.9 3.10 3.11 3.12 3.13 3.14"
ARG PYTHON_VERSION="3.14"

ENV PYTHONUNBUFFERED=1

RUN apt update && \
	apt install -y \
		bash \
		curl \
		wget \
		iputils-ping \
		git

RUN apt update && \
	apt install -y software-properties-common && \
	add-apt-repository ppa:deadsnakes/ppa && \
	apt update && \
	for version in ${PYTHON_VERSIONS}; do \
		apt install -y \
			python${version} \
			python${version}-dev \
			python${version}-venv && \
		python${version} -m ensurepip --upgrade \
	; done && \
	ln -s $(which python${PYTHON_VERSION}) /usr/local/bin/python && \
	ln -s $(which python${PYTHON_VERSION}) /usr/local/bin/python3

RUN pip${PYTHON_VERSION} install \
	build \
	twine \
	tox

# playwright
# In order to install the correct playwright dependencies for the playwright
# release we are using, we need the `playwright install-deps` command which
# is part of the playwright package itself. The playwright release version is
# tracked in the `pyproject.toml` file and pip won't let us install
# dependencies from it if the project is not present. Therefore, we need to
# copy the whole project into the image before we can
# run `playwright install-deps`.
COPY . /app

RUN cd /app && \
	python${PYTHON_VERSION} -m venv env && \
	. ./env/bin/activate && \
	pip install .[test] && \
	playwright install-deps && \
	cd / && \
	rm -rf /app
