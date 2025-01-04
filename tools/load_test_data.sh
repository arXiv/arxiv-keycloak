#!/bin/bash
cd /
python -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install poetry

cd /arxiv-keycloak/tools
poetry install 

python ./load_test_data.py
