# Makefile

include .lily/lily_assistant.makefile
include .lily/lily.makefile


deploy_to_pypi:
	rm -rf dist && \
	python setup.py bdist_wheel && \
	twine upload dist/*.whl
