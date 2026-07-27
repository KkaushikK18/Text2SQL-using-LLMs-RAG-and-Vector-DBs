import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger with standard formatting for the enterprise app.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times if get_logger is called repeatedly
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Output to stdout
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # Optionally, you can add a FileHandler here for persistent logging
        
    return logger
