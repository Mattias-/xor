default: test

test:
		nosetests $(TEST_OPTIONS)

coverage:
		nosetests $(TEST_OPTIONS) --with-coverage --cover-package=xonrequest
