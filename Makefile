executable: shifter_ex

shifter_ex: src/main.py
	python3.11 -m PyInstaller src/main.py --onefile -n shifter_ex

install:
	pip3 install bs4 dateparser requests python-dotenv

run:
	python3.11 src/main.py

