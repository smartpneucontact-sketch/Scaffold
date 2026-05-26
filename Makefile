.PHONY: install test serve ingest brief resume

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e .

serve:
	PYTHONPATH=src uvicorn case_pilot.api.main:app --reload --port 8000

ingest:
	PYTHONPATH=src $(PYTHON) -m case_pilot.rag.ingest --query "BlackArmor pedicle screw oncology"

brief:
	$(PYTHON) scripts/build_brief_pdf.py

resume:
	$(PYTHON) scripts/build_resume_pdf.py

clean:
	rm -rf .venv .pytest_cache traces
	find . -name __pycache__ -type d -exec rm -rf {} +
