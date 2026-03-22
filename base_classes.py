#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Base Classes
Common functionality and base classes for the baby planning system
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import (
    BASE_DIR, EMAIL_CONFIG_FILE, MEMORY_FILE, PATTERNS_FILE,
    DEFAULT_BABY_PATTERNS, ERROR_MESSAGES, SUCCESS_MESSAGES
)
from logger import get_logger, log_error, log_success, log_warning

class BabyPlannerBase(ABC):
    """Base class for all baby planner components"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = get_logger(component_name)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        BASE_DIR.mkdir(exist_ok=True)
    
    def _load_json_file(self, file_path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load JSON file with error handling"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.debug(f"File {file_path} not found, using default")
                return default or {}
        except (json.JSONDecodeError, IOError) as e:
            log_error(self.component_name, e, f"loading {file_path}")
            return default or {}
    
    def _save_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Save JSON file with error handling"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            log_success(self.component_name, f"Saved {file_path}")
            return True
        except (IOError, TypeError) as e:
            log_error(self.component_name, e, f"saving {file_path}")
            return False

class ConfigurableComponent(BabyPlannerBase):
    """Base class for components that need configuration"""
    
    def __init__(self, component_name: str, config_file: Optional[Path] = None):
        super().__init__(component_name)
        self.config_file = config_file
        self._config = {}
        self._load_config()
    
    @abstractmethod
    def _load_config(self):
        """Load configuration - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration - to be implemented by subclasses"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        self._config[key] = value
        return self._save_config()
    
    def _save_config(self) -> bool:
        """Save configuration to file"""
        if self.config_file:
            return self._save_json_file(self.config_file, self._config)
        return True

class EmailBasedComponent(ConfigurableComponent):
    """Base class for email-related components"""
    
    def __init__(self, component_name: str):
        super().__init__(component_name, EMAIL_CONFIG_FILE)
    
    def _load_config(self):
        """Load email configuration"""
        self._config = self._load_json_file(self.config_file, {})
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default email configuration"""
        return {
            "sender_email": "",
            "app_password": "",
            "recipient_email": ""
        }
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        required_fields = ["sender_email", "app_password", "recipient_email"]
        return all(self.get_config(field) for field in required_fields)

class MemoryManager(BabyPlannerBase):
    """Manages memory storage and retrieval"""
    
    def __init__(self):
        super().__init__("memory_manager")
        self.memory_file = MEMORY_FILE
        self._memory_cache = {}
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from file"""
        self._memory_cache = self._load_json_file(self.memory_file, {})
    
    def save_memory(self) -> bool:
        """Save memory to file"""
        return self._save_json_file(self.memory_file, self._memory_cache)
    
    def add_entry(self, key: str, entry: Dict[str, Any]) -> bool:
        """Add a memory entry"""
        entry['timestamp'] = datetime.now().isoformat()
        self._memory_cache[key] = entry
        return self.save_memory()
    
    def get_entry(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory entry"""
        return self._memory_cache.get(key)
    
    def get_entries_by_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """Get entries matching a pattern"""
        return [
            (key, entry) for key, entry in self._memory_cache.items()
            if pattern in key
        ]
    
    def get_entries_in_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get entries within a date range"""
        matching_entries = []
        for key, entry in self._memory_cache.items():
            if 'timestamp' in entry:
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if start_date <= entry_date <= end_date:
                    matching_entries.append((key, entry))
        return matching_entries
    
    def search_entries(self, keyword: str) -> List[Dict[str, Any]]:
        """Search entries for keyword"""
        keyword_lower = keyword.lower()
        matching_entries = []
        
        for key, entry in self._memory_cache.items():
            entry_str = json.dumps(entry).lower()
            if keyword_lower in entry_str:
                matching_entries.append((key, entry))
        
        return matching_entries
    
    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get memory summary for specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = self.get_entries_in_date_range(cutoff_date, datetime.now())
        
        summary = {
            'total_entries': len(recent_entries),
            'enjoyed_activities': [],
            'disliked_activities': [],
            'sleep_ratings': [],
            'developmental_notes': [],
            'feeding_patterns': [],
            'journal_entries': []
        }
        
        for key, entry in recent_entries:
            if 'feedback' in entry:
                feedback = entry['feedback']
                
                # Collect data
                summary['enjoyed_activities'].extend(feedback.get('what_enjoyed', []))
                summary['disliked_activities'].extend(feedback.get('didnt_like', []))
                
                if feedback.get('sleep_quality'):
                    try:
                        summary['sleep_ratings'].append(int(feedback['sleep_quality']))
                    except (ValueError, TypeError):
                        pass
                
                summary['feeding_patterns'].extend(feedback.get('feeding_response', []))
                summary['developmental_notes'].extend(feedback.get('developmental', []))
            
            if 'journal_entries' in entry:
                summary['journal_entries'].extend(entry['journal_entries'])
        
        # Process summary
        summary['most_enjoyed'] = list(set(summary['enjoyed_activities']))[:5]
        summary['most_disliked'] = list(set(summary['disliked_activities']))[:3]
        summary['avg_sleep'] = sum(summary['sleep_ratings']) / len(summary['sleep_ratings']) if summary['sleep_ratings'] else 0
        summary['feeding_patterns'] = list(set(summary['feeding_patterns']))[:2]
        summary['new_skills'] = list(set(summary['developmental_notes']))[:2]
        
        return summary
    
    def cleanup_old_entries(self, days_to_keep: int = 90):
        """Clean up old memory entries"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        keys_to_remove = []
        
        for key, entry in self._memory_cache.items():
            if 'timestamp' in entry:
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if entry_date < cutoff_date:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._memory_cache[key]
        
        if keys_to_remove:
            self.save_memory()
            log_success(self.component_name, f"Cleaned up {len(keys_to_remove)} old memory entries")

class PatternsManager(ConfigurableComponent):
    """Manages baby patterns and preferences"""
    
    def __init__(self):
        super().__init__("patterns_manager", PATTERNS_FILE)
    
    def _load_config(self):
        """Load patterns configuration"""
        self._config = self._load_json_file(self.config_file, DEFAULT_BABY_PATTERNS)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default patterns"""
        return DEFAULT_BABY_PATTERNS
    
    def get_baby_patterns(self) -> Dict[str, Any]:
        """Get baby patterns"""
        return self._config.get("baby_patterns", {})
    
    def update_baby_patterns(self, patterns: Dict[str, Any]) -> bool:
        """Update baby patterns"""
        self._config["baby_patterns"] = patterns
        return self._save_config()
    
    def get_activity_preferences(self) -> List[str]:
        """Get favorite activities"""
        return self.get_baby_patterns().get("favorite_activities", [])
    
    def get_favorite_activities(self) -> List[str]:
        """Get favorite activities (alias for get_activity_preferences)"""
        return self.get_activity_preferences()
    
    def get_sleep_schedule(self) -> Dict[str, str]:
        """Get sleep schedule"""
        return self.get_baby_patterns().get("sleep_schedule", {})
    
    def get_feeding_schedule(self) -> Dict[str, str]:
        """Get feeding schedule"""
        return self.get_baby_patterns().get("feeding_schedule", {})
    
    def get_patterns_history(self) -> Dict[str, Any]:
        """Get patterns history and statistics"""
        return self._config.get("history", {
            "plans_generated": 0,
            "feedback_processed": 0,
            "accuracy_score": 0.0,
            "last_updated": datetime.now().isoformat()
        })
    
    def update_patterns_history(self, history: Dict[str, Any]) -> bool:
        """Update patterns history"""
        if "history" not in self._config:
            self._config["history"] = {}
        self._config["history"].update(history)
        self._config["history"]["last_updated"] = datetime.now().isoformat()
        return self._save_config()
    
    def add_favorite_activity(self, activity: str) -> bool:
        """Add activity to favorites list"""
        baby_patterns = self.get_baby_patterns()
        if "favorite_activities" not in baby_patterns:
            baby_patterns["favorite_activities"] = []
        
        if activity not in baby_patterns["favorite_activities"]:
            baby_patterns["favorite_activities"].append(activity)
            return self.update_baby_patterns(baby_patterns)
        return True  # Already exists
    
    def remove_favorite_activity(self, activity: str) -> bool:
        """Remove activity from favorites list"""
        baby_patterns = self.get_baby_patterns()
        if "favorite_activities" in baby_patterns and activity in baby_patterns["favorite_activities"]:
            baby_patterns["favorite_activities"].remove(activity)
            return self.update_baby_patterns(baby_patterns)
        return True  # Activity doesn't exist
    
    def get_developmental_stage(self) -> str:
        """Get current developmental stage"""
        return self.get_baby_patterns().get("developmental_stage", "unknown")
    
    def set_developmental_stage(self, stage: str) -> bool:
        """Set developmental stage"""
        baby_patterns = self.get_baby_patterns()
        baby_patterns["developmental_stage"] = stage
        return self.update_baby_patterns(baby_patterns)
    
    def update_accuracy_score(self, score: float) -> bool:
        """Update pattern prediction accuracy score"""
        history = self.get_patterns_history()
        history["accuracy_score"] = score
        return self.update_patterns_history(history)
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences"""
        return self._config.get("user_preferences", {
            "morning_start_time": "08:00",
            "evening_end_time": "21:00",
            "preferred_task_count": 6,
            "break_frequency": "2_hours",
            "focus_areas": ["motor_skills", "sensory_development", "visual_tracking"],
            "avoid_areas": ["loud_stimuli", "overstimulation"],
            "communication_style": "gentle",
            "adaptation_speed": "moderate"
        })
    
    def update_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        if "user_preferences" not in self._config:
            self._config["user_preferences"] = {}
        self._config["user_preferences"].update(preferences)
        return self._save_config()
    
    def get_patterns(self) -> Dict[str, Any]:
        """Get all patterns (alias for get_baby_patterns)"""
        return self.get_baby_patterns()
    
    def save_patterns(self) -> bool:
        """Save patterns to file (alias for _save_config)"""
        return self._save_config()
    
    def increment_plans_generated(self) -> bool:
        """Increment plans generated counter"""
        history = self.get_patterns_history()
        history["plans_generated"] = history.get("plans_generated", 0) + 1
        return self.update_patterns_history(history)
    
    def increment_feedback_processed(self) -> bool:
        """Increment feedback processed counter"""
        history = self.get_patterns_history()
        history["feedback_processed"] = history.get("feedback_processed", 0) + 1
        return self.update_patterns_history(history)
    
    def update_sleep_schedule(self, schedule: Dict[str, str]) -> bool:
        """Update sleep schedule"""
        baby_patterns = self.get_baby_patterns()
        baby_patterns["sleep_schedule"] = schedule
        return self.update_baby_patterns(baby_patterns)
    
    def update_feeding_schedule(self, schedule: Dict[str, str]) -> bool:
        """Update feeding schedule"""
        baby_patterns = self.get_baby_patterns()
        baby_patterns["feeding_schedule"] = schedule
        return self.update_baby_patterns(baby_patterns)
    
    def calculate_age_months(self) -> int:
        """Calculate baby's age in months from birth date"""
        baby_patterns = self.get_baby_patterns()
        birth_date_str = baby_patterns.get("birth_date")
        if birth_date_str:
            try:
                birth_date = datetime.fromisoformat(birth_date_str)
                today = datetime.now()
                age_months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
                return max(0, age_months)
            except ValueError:
                pass
        return 0

# Singleton instances
memory_manager = MemoryManager()
patterns_manager = PatternsManager()
