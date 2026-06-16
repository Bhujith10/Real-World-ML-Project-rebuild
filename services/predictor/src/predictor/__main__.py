"""Entry point for the predictor service.

Usage:
    python -m predictor          # Run the streaming prediction service (default)
    python -m predictor train    # Run the training pipeline
"""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "train":
    from predictor.train import train

    train()
else:
    from predictor.main import main

    main()
