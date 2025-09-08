FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSIONS="3.9 3.10 3.11 3.12 3.13"
ARG PYTHON_VERSION="3.13"

ENV PYTHONUNBUFFERED=1

RUN groupadd -g 1000 user && \
	useradd -u 1000 -g 1000 -m user

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
# TODO: add explanation why this is necessary
COPY . /app

RUN cd /app && \
	python${PYTHON_VERSION} -m venv env && \
	. ./env/bin/activate && \
	pip install .[test] && \
	playwright install-deps && \
	cd / && \
	rm -rf /app
