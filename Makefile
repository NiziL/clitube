all: test install clean

test:
	python setup.py test

build:
	python setup.py build

install:
	python setup.py install

clean:
	rm -rf *.egg-info dist build
