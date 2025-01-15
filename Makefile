.PHONY: clean build upload install version-control

# Clean up previous builds
clean:
	rm -rf dist

# Build the source distribution
build: clean
	mkdir -p dist
	python setup.py sdist

# Upload the distribution to PyPI
upload: build
	pip install --upgrade twine
	twine upload dist/* --verbose

# Install dependencies
install:
	pip install -r requirements.txt