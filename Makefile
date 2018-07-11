# Makefile

SHELL := /bin/bash

help:  ## show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

#
# DEVELOPMENT
#
shell:  ## run django shell (ipython)
	source env.sh && python lily/manage.py shell

#
# TESTS
#
test:  ## run selected tests
	source env.sh && py.test --cov=./lily --cov-config .coveragerc -r w -s -vv $(tests)

test_all:  ## run all available tests
	source env.sh && py.test --cov=./lily --cov-config .coveragerc -r w -s -vv tests

coverage:  # render html coverage report
	coverage html -d coverage_html && google-chrome coverage_html/index.html

#
# UPGRADE_VERSION
#
upgrade_version_patch:  ## upgrade version by patch 0.0.X
	source env.sh && python lily/manage.py upgrade_version PATCH

upgrade_version_minor:  ## upgrade version by minor 0.X.0
	source env.sh && python lily/manage.py upgrade_version MINOR

upgrade_version_major:  ## upgrade version by major X.0.0
	source env.sh && python lily/manage.py upgrade_version MAJOR
