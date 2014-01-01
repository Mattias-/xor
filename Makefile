default: test

test:
		nosetests --exe -w tests/
coverage:
		nosetests --exe -w tests/ --with-coverage --cover-package=xonrequest
