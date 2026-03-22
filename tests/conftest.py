#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Test Configuration
Pytest configuration and shared fixtures for comprehensive testing
"""

import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytest

# Add project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BASE_DIR, PATTERNS_FILE, MEMORY_FILE
from base_classes import MemoryManager, PatternsManager
from logger import get_logger


@pytest.fixture(scope="function")
def test_temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = Path(tempfile.mkdtemp(prefix="baby_planner_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_base_dir(test_temp_dir, monkeypatch):
    """Mock BASE_DIR to use test directory"""
    mock_dir = test_temp_dir / "daily-plans"
    mock_dir.mkdir()
    monkeypatch.setattr("config.BASE_DIR", mock_dir)
    return mock_dir


@pytest.fixture
def mock_memory_file(mock_base_dir):
    """Create a mock memory file for testing"""
    memory_file = mock_base_dir / "memory_entries.json"
    memory_file.write_text("{}")
    return memory_file


@pytest.fixture
def mock_patterns_file(mock_base_dir):
    """Create a mock patterns file with test data"""
    patterns_file = mock_base_dir / "patterns.json"
    test_patterns = {
        "baby_patterns": {
            "birth_date": "2025-03-17",
            "age_months": 2,
            "developmental_stage": "infant",
            "favorite_activities": ["tummy_time", "reading", "sensory_play"],
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
            }
        },
        "patterns": {
            "energy_levels": {
                "morning_peak": "9:00 AM",
                "afternoon_peak": "2:00 PM",
                "evening_peak": "6:00 PM",
                "overall_pattern": "biphasic"
            },
            "task_preferences": {
                "preferred_task_types": ["sensory", "motor"],
                "avoid_task_types": ["loud_noises"],
                "complex_task_times": ["morning"],
                "quick_task_times": ["evening"]
            },
            "feedback_themes": {
                "what_works": ["gentle_touch", "voice_soothing"],
                "what_doesnt_work": ["sudden_movements"],
                "common_obstacles": ["overstimulation"],
                "success_factors": ["quiet_environment"]
            }
        },
        "history": {
            "plans_generated": 10,
            "feedback_processed": 8,
            "accuracy_score": 0.85,
            "last_updated": "2025-03-22T10:30:00"
        }
    }
    patterns_file.write_text(json.dumps(test_patterns, indent=2))
    return patterns_file


@pytest.fixture
def memory_manager(mock_memory_file, mock_base_dir):
    """Create MemoryManager instance with test configuration"""
    with patch("base_classes.MEMORY_FILE", mock_memory_file):
        manager = MemoryManager()
        # Clear any existing memory
        manager._memory_cache = {}
        manager.save_memory()
        yield manager


@pytest.fixture
def patterns_manager(mock_patterns_file, mock_base_dir):
    """Create PatternsManager instance with test configuration"""
    with patch("base_classes.PATTERNS_FILE", mock_patterns_file):
        manager = PatternsManager()
        yield manager


@pytest.fixture
def sample_memory_entries():
    """Sample memory entries for testing"""
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    return {
        f'baby_feedback_{today}': {
            'timestamp': datetime.now().isoformat(),
            'feedback': {
                'what_enjoyed': ['tummy time', 'reading books'],
                'didnt_like': ['loud noises', 'sudden movements'],
                'sleep_quality': '8',
                'feeding_response': 'good',
                'developmental': ['tracking objects', 'more alert']
            },
            'journal_entries': [
                {
                    'note': 'Great morning with lots of smiles',
                    'time': '10:30 AM'
                }
            ]
        },
        f'baby_feedback_{yesterday}': {
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
            'feedback': {
                'what_enjoyed': ['gentle touch', 'skin to skin'],
                'didnt_like': ['overstimulation'],
                'sleep_quality': '6',
                'feeding_response': 'fussy',
                'developmental': ['better head control']
            },
            'journal_entries': [
                {
                    'note': 'Challenging afternoon with fussiness',
                    'time': '2:00 PM'
                }
            ]
        }
    }


@pytest.fixture
def sample_feedback_emails():
    """Sample feedback emails for testing"""
    return [
        {
            'subject': 'Baby Feedback - 2025-03-22',
            'from': 'parent@example.com',
            'body': 'feedback Baby loved tummy time today and enjoyed reading books',
            'date': '2025-03-22T20:30:00'
        },
        {
            'subject': 'Daily Journal',
            'from': 'parent@example.com', 
            'body': 'journal Had a wonderful morning with lots of smiles and cooing',
            'date': '2025-03-22T18:15:00'
        },
        {
            'subject': 'Memory Request',
            'from': 'parent@example.com',
            'body': 'memory week',
            'date': '2025-03-22T19:00:00'
        },
        {
            'subject': 'Patterns Update',
            'from': 'parent@example.com',
            'body': 'patterns',
            'date': '2025-03-22T17:45:00'
        }
    ]


@pytest.fixture
def mock_imap_server():
    """Mock IMAP server for email testing"""
    mock_server = Mock()
    mock_server.login.return_value = ('OK', ['Login successful'])
    mock_server.select.return_value = ('OK', ['INBOX selected'])
    mock_server.search.return_value = ('OK', [b'1 2 3 4'])
    mock_server.fetch.return_value = ('OK', [(b'1 (RFC822 {500}', b'email_data')])
    mock_server.store.return_value = ('OK', ['Flags set'])
    mock_server.logout.return_value = ('OK', ['Logout successful'])
    return mock_server


@pytest.fixture
def mock_smtp_server():
    """Mock SMTP server for email testing"""
    mock_server = Mock()
    mock_server.starttls.return_value = (220, 'Ready')
    mock_server.login.return_value = (235, 'Authentication successful')
    mock_server.send_message.return_value = {}
    mock_server.quit.return_value = (221, 'Bye')
    return mock_server


@pytest.fixture
def disable_logging(monkeypatch):
    """Disable logging during tests to reduce noise"""
    def mock_get_logger(name, log_file=None):
        logger = Mock()
        logger.info = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        logger.debug = Mock()
        return logger
    
    monkeypatch.setattr("logger.get_logger", mock_get_logger)
    monkeypatch.setattr("base_classes.get_logger", mock_get_logger)


@pytest.fixture
def sample_plan_content():
    """Sample baby plan content for testing"""
    return """# Baby Development Plan - 2025-03-22

## Baby Context
- Date: 2025-03-22 (Saturday)
- Baby's Age: 2 months old
- Developmental Focus: sensory development, motor skills

## Daily Baby Activities

### Morning Routine (6 AM - 12 PM)
- **Tummy Time** (6:30 AM - 7:00 AM): 15 minutes of supervised tummy time
- **Reading Time** (9:00 AM - 9:30 AM): Read soft cloth books
- **Sensory Play** (10:30 AM - 11:00 AM): Gentle textures and sounds

### Afternoon Routine (12 PM - 6 PM)
- **Tummy Time** (1:30 PM - 2:00 PM): Practice head control
- **Reading Time** (3:00 PM - 3:30 PM): High-contrast book reading
- **Gentle Movement** (4:30 PM - 5:00 PM): Slow rocking and cuddling

### Evening Routine (6 PM - 10 PM)
- **Quiet Time** (6:30 PM - 7:00 PM): Calm environment preparation
- **Reading Time** (8:00 PM - 8:30 PM): Bedtime stories
- **Bedtime Routine** (9:30 PM - 10:00 PM): Sleep preparation

## Sleep & Feeding Schedule

### Feeding Times
- Morning: 7:00 AM
- Midday: 11:30 AM  
- Afternoon: 3:30 PM
- Evening: 6:30 PM
- Night: 10:00 PM

### Sleep Schedule
- Morning Nap: 9:00 AM
- Afternoon Nap: 1:00 PM
- Evening Nap: 4:00 PM
- Night Sleep: 7:30 PM

## Completed Activities
*Track completed activities here*

## Baby Feedback Section

### What Baby Enjoyed Most
*Activities that made baby happy*

### What Baby Didn't Like  
*Activities that caused fussiness*

### Sleep & Feeding Patterns
*Quality, response, fussy/happy times*

### Developmental Observations
*New skills, milestones, changes*

## Tomorrow's Plan

### Activities to Continue
*Successful activities to repeat*

### New Activities to Try
*Age-appropriate challenges*

### Schedule Adjustments
*Timing and routine improvements*
"""


# Test data factories
@pytest.fixture
def memory_entry_factory():
    """Factory for creating memory entries"""
    def create_entry(date=None, feedback=None, journal=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'feedback': feedback or {
                'what_enjoyed': [],
                'didnt_like': [],
                'sleep_quality': '5',
                'feeding_response': 'normal',
                'developmental': []
            },
            'journal_entries': journal or []
        }
        
        return f'baby_feedback_{date}', entry
    
    return create_entry


@pytest.fixture
def email_factory():
    """Factory for creating test emails"""
    def create_email(subject, body, from_addr='parent@example.com'):
        return {
            'subject': subject,
            'from': from_addr,
            'body': body,
            'date': datetime.now().isoformat()
        }
    
    return create_email
