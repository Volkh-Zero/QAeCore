#!/usr/bin/env python3
"""
SAFLA Startup Script
"""

import sys
from pathlib import Path

# Add SAFLA to path
safla_path = Path(__file__).parent
sys.path.insert(0, str(safla_path))

from safla.cli import main

if __name__ == "__main__":
    main()
