.PHONY: dev release publish clean run

top: run

dev:
	pip install -e .

release:
	python -m build

publish:
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

run:
	nits -v
