default: test

test:
		nosetests $(TEST_OPTIONS) -e slow

coverage:
		nosetests $(TEST_OPTIONS) --with-coverage --cover-package=xor

build:
	        virtualenv xor_env && . xor_env/bin/activate && \
				                pip install -r requirements.txt

build-dev:
	        virtualenv xor_env && . xor_env/bin/activate && \
				                pip install -r dev-requirements.txt
