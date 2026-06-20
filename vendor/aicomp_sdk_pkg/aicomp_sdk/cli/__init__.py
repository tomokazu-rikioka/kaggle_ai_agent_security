"""
Command Line Interface for aicomp_sdk.

Provides user-friendly commands for common operations:
- init: Create submission templates
- validate: Fast validation of submissions
- test: Run evaluations with progress tracking
- compare: Compare evaluation results
- history: View past evaluation results
- visualize: Generate charts from results
"""

from aicomp_sdk.cli.main import main

__all__ = ["main"]
