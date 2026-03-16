#!/usr/bin/env python3
"""
Master overnight script: pulls ALL of Tanach sequentially.
Resume-safe: skips books that are already complete.
Run: python run_overnight.py
"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Just run the full tanach script — it handles everything and skips completed books
from pull_full_tanach import main
main()
