.PHONY: check test lint compile

PYTHON ?= .venv311/bin/python

check: compile lint test

compile:
	$(PYTHON) -m compileall -q d3keyhelper_linux.py d3keyhelper_linux_gui.py gui_profile_page.py gui_widgets.py gui_i18n.py vision.py capture.py config_io.py runner_events.py config_schema.py enums.py tests

lint:
	$(PYTHON) -m ruff check .

test:
	QT_QPA_PLATFORM=offscreen $(PYTHON) -m unittest discover -s tests
