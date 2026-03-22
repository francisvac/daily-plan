#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Logging Module
Centralized logging configuration and utilities
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from config import LOG_LEVEL, LOG_FORMAT, BASE_DIR

class BabyPlannerLogger:
    """Centralized logger for the baby planning system"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """Get or create a logger with consistent configuration"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
            
            # Create formatter
            formatter = logging.Formatter(LOG_FORMAT)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler (if specified)
            if log_file:
                log_path = BASE_DIR / "logs" / log_file
                log_path.parent.mkdir(exist_ok=True)
                file_handler = logging.FileHandler(log_path)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def setup_system_logging(cls):
        """Setup logging for the entire system"""
        # Create logs directory
        (BASE_DIR / "logs").mkdir(exist_ok=True)
        
        # Setup main logger
        main_logger = cls.get_logger("baby_planner", "baby_planner.log")
        
        # Setup component loggers
        cls.get_logger("plan_generator", "plan_generator.log")
        cls.get_logger("email_integration", "email.log")
        cls.get_logger("feedback_processor", "feedback.log")
        cls.get_logger("command_processor", "commands.log")
        
        return main_logger

# Convenience functions
def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Get a logger instance"""
    return BabyPlannerLogger.get_logger(name, log_file)

def log_system_info():
    """Log system information"""
    logger = get_logger("system")
    logger.info("ZeroClaw Baby Planner System Starting")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info(f"Base Directory: {BASE_DIR}")

def log_error(component: str, error: Exception, context: str = ""):
    """Log an error with context"""
    logger = get_logger(component)
    error_msg = f"Error in {component}"
    if context:
        error_msg += f" - {context}"
    error_msg += f": {str(error)}"
    logger.error(error_msg, exc_info=True)

def log_success(component: str, message: str):
    """Log a success message"""
    logger = get_logger(component)
    logger.info(f"✅ {message}")

def log_warning(component: str, message: str):
    """Log a warning message"""
    logger = get_logger(component)
    logger.warning(f"⚠️ {message}")
