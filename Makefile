# Makefile
.PHONY: install dev build clean test

install:
	pip install -r requirements/base.txt

dev:
	python -m bb_detector

build:
	python build.py

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +

test:
	python -m pytest tests/ -v
