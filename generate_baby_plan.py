#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Import Wrapper
Provides import access to generate-baby-plan.py functionality
"""

# Import the main functionality from the hyphenated file
import importlib.util
import sys
from pathlib import Path

# Load the generate-baby-plan.py module
spec = importlib.util.spec_from_file_location("generate_baby_plan_module", Path(__file__).parent / "generate-baby-plan.py")
generate_baby_plan_module = importlib.util.module_from_spec(spec)
sys.modules["generate_baby_plan_module"] = generate_baby_plan_module
spec.loader.exec_module(generate_baby_plan_module)

# Export the main class
BabyPlanGenerator = generate_baby_plan_module.BabyPlanGenerator
