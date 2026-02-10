.DEFAULT_GOAL := list
.PHONY: test test-all test-cov lint fmt cov-report list

#: run tests
test:
	uv run pytest tests

#: run tests on all compatible python versions
test-all:
	@for v in 3.10 3.11 3.12 3.13; do \
		echo "=== Python $$v ==="; \
		uv run --python $$v pytest tests || exit 1; \
	done

#: run tests with coverage
test-cov:
	uv run coverage run -m pytest tests

#: generate coverage report
cov-report:
	uv run coverage combine
	uv run coverage html

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
