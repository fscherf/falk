PYTHON=python3.14
PYPIRC=~/.pypirc.fscherf

.PHONY: \
	all \
	docker-build \
	python-shell python-test python-build \
	node-shell node-build node-watch node-lint \
	clean build test ci-test lint \
	docs docs-server grip \
	test-app django52-test-app

define DOCKER_COMPOSE_RUN
	docker compose run \
		-it \
		--user=$$(id -u):$$(id -g) \
		--remove-orphans \
		--service-ports \
		$1 $2
endef

all: test-app

# docker
docker-build:
	docker compose build --no-cache ${args}

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
	rm -rf falk/static/*
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
	rm -rf playwright && \
	rm -rf falk/static

build: docker-build node-build python-build

test: node-build
	$(call DOCKER_COMPOSE_RUN,python,tox -e ${PYTHON} ${args})

ci-test: clean build
	$(call DOCKER_COMPOSE_RUN,python,tox -r ${args})

lint: node-lint

# docs
docs:
	$(call DOCKER_COMPOSE_RUN,python,tox -e docs ${args})

docs-server:
	$(call DOCKER_COMPOSE_RUN,python,tox -e docs-server ${args})

grip:
	$(call DOCKER_COMPOSE_RUN,python,tox -e grip ${args})

# test apps
test-app: node-build
	$(call DOCKER_COMPOSE_RUN,python,tox -e test-app ${args})

django52-test-app: node-build
	$(call DOCKER_COMPOSE_RUN,python,tox -e django52-test-app ${args})

# releases
_pypi-upload:
	$(call DOCKER_COMPOSE_RUN,-v ${PYPIRC}:/.pypirc,python twine upload --config-file /.pypirc dist/*)

_doc-upload:
	rsync -avh --recursive --delete \
		docs/site/* pages.fscherf.de:/var/www/virtual/fscherf/pages.fscherf.de/falk
