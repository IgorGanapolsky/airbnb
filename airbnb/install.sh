#!/bin/bash
# This script sets up the Python environment and installs dependencies.

echo "--- Setting up Python virtual environment in ./venv ---"
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

echo "--- Installing required packages from requirements.txt ---"
pip install --upgrade pip
pip install -r requirements.txt

echo "
--- Setup Complete! ---
To activate the virtual environment in your shell, run:
source venv/bin/activate

Next, copy config.yaml.template to config.yaml and fill in your API keys.
"