PYTHON=python3.13

.PHONY: all python-shell python-test build test ci-test

define DOCKER_COMPOSE_RUN
	docker compose run \
		-it \
		--user=$$(id -u):$$(id -g) \
		--remove-orphans \
		--service-ports \
		$1 $2
endef

all: test

python-shell:
	$(call DOCKER_COMPOSE_RUN,python,bash)

python-test:
	$(call DOCKER_COMPOSE_RUN,python,tox)

build:
	rm -rf build dist *.egg-info && \
	$(call DOCKER_COMPOSE_RUN,python,${PYTHON} -m build)

test:
	$(call DOCKER_COMPOSE_RUN,python,tox -e ${PYTHON} ${args})

ci-test:
	$(call DOCKER_COMPOSE_RUN,python,tox ${args})
