#!/bin/bash
# Start the Song SRT Generator. Run install.command once first.
cd "$(dirname "$0")"
export GRADIO_ANALYTICS_ENABLED=False
source .venv/bin/activate
python app.py
