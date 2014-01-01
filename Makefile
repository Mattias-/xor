default: test

test:
		nosetests $(TEST_OPTIONS) --exe -w tests/

coverage:
		nosetests $(TEST_OPTIONS) --exe -w tests/ --with-coverage --cover-package=xonrequest
