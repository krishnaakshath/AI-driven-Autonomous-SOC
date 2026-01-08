#!/bin/bash
source soc-env/bin/activate
streamlit run dashboard.py --server.port 8501 --server.headless true
