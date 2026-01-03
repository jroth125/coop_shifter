VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
# On Windows with venv, you'd use:
# PYTHON := $(VENV)/Scripts/python.exe
# PIP := $(VENV)/Scripts/pip.exe
.PHONY: venv install run build clean
venv:
	python3.11 -m venv $(VENV)
install: venv
	$(PIP) install --upgrade pip
	$(PIP) install bs4 dateparser requests python-dotenv pyinstaller
run: install
	$(PYTHON) src/main.py
build: install
	$(PYTHON) -m PyInstaller src/main.py --onefile -n shifter_ex
clean:
	rm -rf build dist shifter_ex.spec