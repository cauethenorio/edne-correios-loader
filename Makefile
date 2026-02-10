.DEFAULT_GOAL := list
.PHONY: test test-all test-cov lint fmt cov-report cov-xml list

#: run tests (e.g. make test PY=3.14)
test:
	uv run $(if $(PY),--python $(PY)) pytest tests

#: run tests on all compatible python versions
test-all:
	@for v in 3.10 3.11 3.12 3.13 3.14; do \
		echo "=== Python $$v ==="; \
		uv run --python $$v pytest tests || exit 1; \
	done

#: run tests with coverage (e.g. make test-cov PY=3.11)
test-cov:
	uv run $(if $(PY),--python $(PY)) coverage run -m pytest tests

#: generate coverage report
cov-report:
	uv run $(if $(PY),--python $(PY)) coverage combine
	uv run $(if $(PY),--python $(PY)) coverage html

#: generate coverage xml report (for CI)
cov-xml:
	uv run $(if $(PY),--python $(PY)) coverage combine
	uv run $(if $(PY),--python $(PY)) coverage xml

#: run tests with coverage and generate report
cov: test-cov cov-report

#: run linter checks
lint:
	uv run ruff check .
	uv run ruff format --diff .

#: format code
fmt:
	uv run ruff format .
	uv run ruff check --fix .

#: list all available commands
list:
	@grep -B1 -E "^[a-zA-Z0-9_-]+\:([^\=]|$$)" Makefile \
	 | grep -v -- -- \
	 | sed 'N;s/\n/###/' \
	 | sed -n 's/^#: \(.*\)###\(.*\):.*/make \2###\1/p' \
	 | column -t  -s '###'
