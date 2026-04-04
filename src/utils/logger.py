import logging
import sys

def setup_logger(name: str):
    """Setup a standard logger with consistent formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Consistent format: [Timestamp] [Level] [Module]: Message
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Create a root logger for app-wide use
app_logger = setup_logger("ShieldGig")
