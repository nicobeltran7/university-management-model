.PHONY: install ingest test run clean

install:
	python -m pip install -r requirements.txt

ingest:
	python -m src.ingest

test:
	python -m pytest tests -q

run:
	streamlit run src/app.py

clean:
	rm -rf extracts/*.parquet
