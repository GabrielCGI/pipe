@echo off

set UV_PROJECT_ENVIRONMENT=%userprofile%/.cache/uv-envs/layers-dependencies-v2
set SCRIPT_PATH=outdated.py

uv run %SCRIPT_PATH%

pause