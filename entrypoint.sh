#!/bin/bash

uvicorn src.api:app --host 0.0.0.0 --port 5000 &
echo "API serving /chat endpoint on port 5000"

streamlit run src/app.py --server.port 8000 --server.address 0.0.0.0 &
echo "Web UI for chat available on port 8000"

wait