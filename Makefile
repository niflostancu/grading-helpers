# Makefile for installing env. requirements

VENV=.venv

requirements: $(VENV) $(VENV)/.reqs.installed

$(VENV)/.reqs.installed: requirements.txt $(VENV)
	$(VENV)/bin/python3 -mpip install -r requirements.txt
	touch "$@"

$(VENV):
	python3 -m venv $(VENV)

