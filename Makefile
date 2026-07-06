.PHONY: test lint clean install

install:
	pip install -r requirements.txt

test:
	python -m pytest kernel/tests/ -v --tb=short

lint:
	ruff check kernel/

fmt:
	ruff format kernel/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
