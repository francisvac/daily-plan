#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Core Configuration and Constants
Centralized configuration and constants for the baby planning system
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Paths
BASE_DIR = Path.home() / "daily-plans"
PLAN_DIR = BASE_DIR
PATTERNS_FILE = BASE_DIR / "patterns.json"
TEMPLATE_FILE = BASE_DIR / "template.md"
MEMORY_FILE = BASE_DIR / "memory_entries.json"
EMAIL_CONFIG_FILE = BASE_DIR / "email_config.json"
PROCESSED_EMAILS_FILE = BASE_DIR / "processed_emails.json"

# Baby Development Stages
DEVELOPMENT_STAGES = {
    "prenatal": {"age_range": (-1, -1), "focus": ["bonding", "development", "comfort"]},
    "newborn": {"age_range": (0, 1), "focus": ["bonding", "development", "comfort"]},
    "infant": {"age_range": (1, 6), "focus": ["development", "sensory", "motor"]},
    "toddler": {"age_range": (6, 12), "focus": ["motor", "cognitive", "social"]},
    "young_toddler": {"age_range": (12, 18), "focus": ["cognitive", "language", "social"]},
    "toddler_2": {"age_range": (18, 24), "focus": ["language", "social", "independence"]},
    "preschool": {"age_range": (24, 36), "focus": ["cognitive", "social", "pre-academic"]}
}

# Default Baby Patterns
DEFAULT_BABY_PATTERNS = {
    "baby_patterns": {
        "birth_date": "2025-03-17",
        "age_months": 0,
        "developmental_stage": "newborn",
        "favorite_activities": ["gentle_touch", "skin_to_skin", "voice_soothing", "swaddling"],
        "sleep_schedule": {
            "morning_nap": "9:00 AM",
            "afternoon_nap": "1:00 PM", 
            "evening_nap": "4:00 PM",
            "night_bedtime": "7:30 PM"
        },
        "feeding_schedule": {
            "morning": "7:00 AM",
            "midday": "11:30 AM",
            "afternoon": "3:30 PM",
            "evening": "6:30 PM",
            "night": "10:00 PM"
        },
        "preferred_activity_times": ["morning", "afternoon", "evening"],
        "favorite_reading_times": ["morning", "before_mother_rest", "bedtime"],
        "comfort_patterns": {
            "soothing_techniques": ["gentle_touch", "skin_to_skin", "voice_soothing", "swaddling"],
            "optimal_environment": ["quiet", "warm", "dim_lighting"]
        }
    },
    "patterns": {
        "energy_levels": {
            "morning_peak": None,
            "afternoon_peak": None,
            "evening_peak": None,
            "overall_pattern": "unknown"
        },
        "task_preferences": {
            "preferred_task_types": [],
            "avoid_task_types": [],
            "complex_task_times": [],
            "quick_task_times": []
        },
        "completion_patterns": {
            "high_completion_days": [],
            "low_completion_days": [],
            "seasonal_patterns": {},
            "weekly_patterns": {}
        },
        "feedback_themes": {
            "what_works": [],
            "what_doesnt_work": [],
            "common_obstacles": [],
            "success_factors": []
        },
        "productivity_insights": {
            "optimal_task_count": None,
            "best_task_duration": None,
            "break_frequency": None,
            "focus_session_length": None
        }
    },
    "history": {
        "plans_generated": 0,
        "feedback_processed": 0,
        "accuracy_score": 0.0,
        "last_updated": None
    },
    "user_preferences": {
        "morning_start_time": "09:00",
        "evening_end_time": "21:00",
        "preferred_task_count": 6,
        "break_frequency": "2_hours",
        "focus_areas": [],
        "avoid_areas": []
    }
}

# Email Configuration
EMAIL_SERVER_CONFIG = {
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com", 
    "smtp_port": 465
}

# Memory and Feedback Patterns
FEEDBACK_KEYWORDS = {
    "enjoyed": ["enjoyed", "liked", "loved", "happy", "smiled", "giggled"],
    "disliked": ["didn't like", "disliked", "fussy", "unhappy", "cried", "upset"],
    "sleep": ["sleep quality", "sleep", "slept", "napped", "rested"],
    "feeding": ["feeding", "ate", "nursing", "bottle", "fed"],
    "developmental": ["developmental", "milestone", "new skill", "learned", "first", "progress"]
}

JOURNAL_KEYWORDS = ["journal", "note", "thought", "feeling", "observation", "moment"]

# Activity Templates by Age
AGE_ACTIVITIES = {
    -1: {  # Prenatal
        "morning": ["belly_rubbing", "reading_stories", "gentle_music"],
        "afternoon": ["mother_voice", "gentle_movement", "relaxation"],
        "evening": ["calming_music", "bedtime_stories", "mother_bonding"]
    },
    0: {   # Newborn
        "morning": ["gentle_touch", "skin_to_skin", "voice_soothing"],
        "afternoon": ["swaddling", "white_noise", "gentle_rocking"],
        "evening": ["bath_time", "massage", "bedtime_routine"]
    },
    1: {   # 1 month
        "morning": ["tummy_time", "face_tracking", "gentle_play"],
        "afternoon": ["sensory_stimulation", "baby_massage", "outdoor_time"],
        "evening": ["quiet_time", "bedtime_routine", "gentle_soothing"]
    },
    3: {   # 3 months
        "morning": ["tummy_time", "reaching_toys", "sensory_play"],
        "afternoon": ["baby_gym", "mirror_play", "music_time"],
        "evening": ["reading_time", "quiet_play", "bedtime_routine"]
    },
    6: {   # 6 months
        "morning": ["tummy_time", "sitting_practice", "sensory_bins"],
        "afternoon": ["baby_gym", "reading_books", "music_classes"],
        "evening": ["quiet_play", "bedtime_stories", "gentle_soothing"]
    },
    9: {   # 9 months
        "morning": ["crawling_practice", "stacking_toys", "sensory_play"],
        "afternoon": ["pulling_up", "peek_a_boo", "music_time"],
        "evening": ["quiet_time", "reading_books", "bedtime_routine"]
    },
    12: {  # 12 months
        "morning": ["walking_practice", "stacking_blocks", "shape_sorters"],
        "afternoon": ["simple_puzzles", "music_toys", "outdoor_play"],
        "evening": ["quiet_time", "reading_books", "bedtime_routine"]
    }
}

# Email Commands
EMAIL_COMMANDS = {
    "memory": ["today", "week", "month", "search"],
    "feedback": ["add", "quick"],
    "journal": ["add", "note"],
    "patterns": ["summary", "current"],
    "help": ["commands", "usage"]
}

# Template Placeholders
TEMPLATE_PLACEHOLDERS = {
    "basic": ["DATE", "DAY_OF_WEEK", "BABY_AGE", "FOCUS_AREAS", "TIMESTAMP"],
    "activities": ["MORNING_TUMMY", "MORNING_READING", "MORNING_PLAY", 
                   "AFTERNOON_TUMMY", "AFTERNOON_READING", "AFTERNOON_SENSORY",
                   "EVENING_PLAY", "EVENING_READING", "BEDTIME_ROUTINE"],
    "schedule": ["MORNING_FEEDING", "MIDDAY_FEEDING", "AFTERNOON_FEEDING", 
                "EVENING_FEEDING", "NIGHT_FEEDING"],
    "sleep": ["MORNING_NAP", "AFTERNOON_NAP", "EVENING_NAP", "NIGHT_SLEEP"],
    "feedback": ["BABY_ENJOYED", "BABY_DISLIKED", "SLEEP_QUALITY", "FEEDING_RESPONSE",
                "FUSSY_PERIODS", "HAPPY_PERIODS", "DEVELOPMENT"],
    "journal": ["JOURNAL_NOTE", "PARENT_JOURNAL"],
    "memory": ["TOP_ENJOYED", "TOP_DISLIKED", "AVG_SLEEP", "FEEDING_TRENDS",
              "NEW_SKILLS", "PROGRESSING_SKILLS", "MILESTONES"],
    "patterns": ["ACTIVITY_SUCCESS", "BEST_TUMMY_TIME", "FAVORITE_READING_TIMES", "SLEEP_PATTERNS"]
}

# Cron Job Schedules
CRON_SCHEDULES = {
    "plan_generation": "0 6 * * *",
    "email_processing": "0 */2 * * *",
    "feedback_reminder": "0 20 * * *"
}

# Logging Configuration
LOG_LEVEL = os.environ.get("BABY_PLANNER_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Validation Rules
VALIDATION_RULES = {
    "baby_age": {"min": -1, "max": 36},  # Prenatal to 3 years
    "sleep_quality": {"min": 1, "max": 10},
    "feeding_times": ["morning", "midday", "afternoon", "evening", "night"],
    "activity_periods": ["morning", "afternoon", "evening"]
}

# Error Messages
ERROR_MESSAGES = {
    "config_not_found": "Configuration file not found. Please run setup first.",
    "invalid_date": "Invalid date format. Please use YYYY-MM-DD.",
    "email_failed": "Failed to send email. Please check your configuration.",
    "memory_error": "Error accessing memory file.",
    "pattern_error": "Error loading patterns file."
}

# Success Messages
SUCCESS_MESSAGES = {
    "plan_generated": "Baby plan generated successfully!",
    "email_sent": "Email sent successfully!",
    "feedback_saved": "Feedback saved successfully!",
    "memory_updated": "Memory updated successfully!"
}

class ConfigManager:
    """Centralized configuration management"""
    
    @staticmethod
    def ensure_directories():
        """Create necessary directories"""
        BASE_DIR.mkdir(exist_ok=True)
        PLAN_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def load_json_config(file_path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load JSON configuration with fallback to default"""
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {file_path}: {e}")
                return default or {}
        return default or {}
    
    @staticmethod
    def save_json_config(file_path: Path, data: Dict[str, Any]) -> bool:
        """Save JSON configuration"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except (IOError, TypeError) as e:
            print(f"Error saving {file_path}: {e}")
            return False
    
    @staticmethod
    def get_developmental_stage(age_months: int) -> str:
        """Get developmental stage based on age"""
        for stage, config in DEVELOPMENT_STAGES.items():
            min_age, max_age = config["age_range"]
            if min_age <= age_months <= max_age:
                return stage
        return "unknown"
    
    @staticmethod
    def validate_age(age_months: int) -> bool:
        """Validate baby age"""
        return VALIDATION_RULES["baby_age"]["min"] <= age_months <= VALIDATION_RULES["baby_age"]["max"]
