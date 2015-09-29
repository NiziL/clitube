all:
	python3 setup.py build

install:
	python3 setup.py install

uninstall:
	python3 setup.py uninstall

clean:
	rm -rf *.egg-info dist build
