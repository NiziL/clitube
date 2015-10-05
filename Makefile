all: test build

test:
	python setup.py test

build:
	python setup.py build

install:
	python setup.py install

uninstall:
	python setup.py uninstall

clean:
	rm -rf *.egg-info dist build
