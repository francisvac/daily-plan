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
    
    def get_sleep_schedule(self) -> Dict[str, str]:
        """Get sleep schedule"""
        return self.get_baby_patterns().get("sleep_schedule", {})
    
    def get_feeding_schedule(self) -> Dict[str, str]:
        """Get feeding schedule"""
        return self.get_baby_patterns().get("feeding_schedule", {})

# Singleton instances
memory_manager = MemoryManager()
patterns_manager = PatternsManager()
