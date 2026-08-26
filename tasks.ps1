# Windows task runner. The Makefile is the equivalent for macOS and Linux.
#
# Usage:  .\tasks.ps1 ingest
#         .\tasks.ps1 test
#         .\tasks.ps1 run

param(
    [Parameter(Position = 0)]
    [ValidateSet('install', 'ingest', 'test', 'run', 'clean')]
    [string]$Task = 'run'
)

$ErrorActionPreference = 'Stop'

switch ($Task) {
    'install' { python -m pip install -r requirements.txt }
    'ingest'  { python -m src.ingest }
    'test'    { python -m pytest tests -q }
    'run'     { streamlit run streamlit_app.py }
    'clean'   { Remove-Item -Path 'extracts\*.parquet' -ErrorAction SilentlyContinue }
}
