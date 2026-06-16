"""Entry point for the predictor service.

Usage:
    python -m predictor          # Run the streaming prediction service (default)
    python -m predictor.train    # Run the training pipeline
"""

from predictor.main import main

main()
