"""Entry point for the Streamlit application.

This file exists at the repository root for two reasons. It keeps `src` on the
import path when Streamlit runs, and it is the filename Streamlit Community
Cloud looks for by default when deploying.

Run with:  streamlit run streamlit_app.py
"""

from src.app import main

if __name__ == "__main__":
    main()
