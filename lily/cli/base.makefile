
#
# RENDERED FOR VERSION: {% VERSION %}
#
# WARNING: This file is autogenerated by the `lily` and any manual
# changes you will apply here will be overwritten by next
# `lily init <project>` invocation.
#

help:  ## show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

SHELL := /bin/bash

LILY_SERVICE_PORT := $(shell source env.sh && echo $${LILY_SERVICE_PORT})

#
# UTILS
#
shell:  ## run django shell (ipython)
	source env.sh && \
	python {% SRC_DIR %}/manage.py shell

#
# MIGRATIONS
#
.PHONY: migrations_create
migrations_create:  ## auto-create migrations for all installed apps
	source env.sh && \
	python {% SRC_DIR %}/manage.py makemigrations


.PHONY: migrations_bulk_read
migrations_bulk_read:  ## real all migrations
	source env.sh && \
	python {% SRC_DIR %}/manage.py listmigrations


.PHONY: migrations_apply
migrations_apply:  ## apply all not yet applied migrations
	source env.sh && \
	python {% SRC_DIR %}/manage.py migrate


#
# COMMANDS & DOCS
#
.PHONY: docs_render_markdown
docs_render_markdown: test_all  ## render Markdown representation of commands
	source env.sh && \
	python {% SRC_DIR %}/manage.py render_markdown

.PHONY: docs_render_commands
docs_render_commands: test_all  ## render JSON representation of commands
	source env.sh && \
	python {% SRC_DIR %}/manage.py render_commands


#
# START
#
start_gunicorn: migrations_apply  ## start service locally
	source env.sh && \
	export PYTHONPATH="${PYTHONPATH}:${PWD}/{% SRC_DIR %}" && \
	python {% SRC_DIR %}/manage.py migrate && \
	gunicorn conf.wsgi \
		--worker-class gevent \
		-w 1 \
		--log-level=debug \
		-t 60 \
		-b 127.0.0.1:${LILY_SERVICE_PORT}

start_dev_server: migrations_apply  ## start development server (for quick checks) locally
	source env.sh && \
	python {% SRC_DIR %}/manage.py runserver 127.0.0.1:${LILY_SERVICE_PORT}

#
# OVERWRITE SETUP / TEARDOWN
#
.PHONY: test_teardown
test_teardown: docs_render_commands docs_render_markdown
