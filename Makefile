PYTHON=python3.13
PYPIRC=~/.pypirc.fscherf

.PHONY: \
	all \
	python-shell python-test python-build \
	node-shell node-build node-watch node-lint \
	clean build test ci-test lint \
	docs docs-server grip

define DOCKER_COMPOSE_RUN
	docker compose run \
		-it \
		--user=$$(id -u):$$(id -g) \
		--remove-orphans \
		--service-ports \
		$1 $2
endef

all: asgi-test-app

# python
python-shell:
	$(call DOCKER_COMPOSE_RUN,python,bash)

python-test:
	$(call DOCKER_COMPOSE_RUN,python,tox)

python-build:
	rm -rf build dist *.egg-info && \
	$(call DOCKER_COMPOSE_RUN,python,${PYTHON} -m build)

# node
node-shell:
	$(call DOCKER_COMPOSE_RUN,node,bash)

node-build:
	$(call DOCKER_COMPOSE_RUN,node,npm run build)

node-watch:
	$(call DOCKER_COMPOSE_RUN,node,npm run watch)

node-lint:
	$(call DOCKER_COMPOSE_RUN,node,npm run lint)

# meta
clean:
	rm -rf build dist *.egg-info && \
	rm -rf .tox && \
	rm -rf node_modules && \
	rm -rf falk/client

build: node-build python-build

test:
	$(call DOCKER_COMPOSE_RUN,python,tox -e ${PYTHON} ${args})

ci-test:
	$(call DOCKER_COMPOSE_RUN,python,tox ${args})

lint: node-lint

# docs
docs:
	$(call DOCKER_COMPOSE_RUN,python,tox -e docs ${args})

docs-server:
	$(call DOCKER_COMPOSE_RUN,python,tox -e docs-server ${args})

grip:
	$(call DOCKER_COMPOSE_RUN,python,tox -e grip ${args})

# test apps
wsgi-test-app: node-build
	$(call DOCKER_COMPOSE_RUN,python,tox -e wsgi-test-app ${args})

asgi-test-app: node-build
	$(call DOCKER_COMPOSE_RUN,python,tox -e asgi-test-app ${args})

# releases
_pypi-upload:
	$(call DOCKER_COMPOSE_RUN,-v ${PYPIRC}:/.pypirc,python twine upload --config-file /.pypirc dist/*)

_doc-upload:
	rsync -avh --recursive --delete \
		docs/site/* pages.fscherf.de:/var/www/virtual/fscherf/pages.fscherf.de/falk
