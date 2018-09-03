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

#
# ANGULAR CLIENT
# TO BE MOVED TO SOME SERVICE WHICH IS CLOSELY RELATED TO COSPHERE
# --> the best is probably the GATEWAY which could also serve as
# --> a centralized storage of all across cluster info!!!
# --> in the future gateway would be capable of "seeing" the dependencies
# --> between services!!!
#
render_angular_for_web_ui:  ## render angular client to WEB UI
	python lily/manage.py render_angular \
		--exclude_domain BRICKS \
		--exclude_domain GOSSIP \
		--exclude_domain QUIZZER

render_angular_for_bricks_ui:  ## render angular client to BRICKS UI
	python lily/manage.py render_angular \
		--include_domain BRICKS \
		--include_domain GOSSIP
