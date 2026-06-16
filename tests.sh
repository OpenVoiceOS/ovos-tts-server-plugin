#!/bin/bash

pip install '.[test]'

black --line-length=119 .
bandit -ll -r ovos_tts_plugin_server
flake8 --max-line-length=119 ovos_tts_plugin_server
isort --profile black .
ruff ovos_tts_plugin_server
mypy --ignore-missing-imports --exclude test ovos_tts_plugin_server
safety check --ignore=58755 --continue-on-error

pytest
