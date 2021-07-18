# Makefile

include .lily/lily_assistant.makefile
include .lily/lily.makefile


deploy_to_pypi:
	rm -rf dist && \
	python setup.py bdist_wheel && \
	twine upload dist/*.whl

.PHONY: lint
lint:  ## lint the lily & tests
	printf "\n>> [CHECKER] check if code fulfills quality criteria\n" && \
	source env.sh && \
	flake8 --ignore N818,D100,D101,D102,D103,D104,D105,D106,D107,D202,D204,W504,W606 tests && \
	flake8 --ignore N818,D100,D101,D102,D103,D104,D105,D106,D107,D202,D204,W504,W606 lily
