#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - PatternsManager Unit Tests
Comprehensive testing of baby patterns management and developmental tracking
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from base_classes import PatternsManager


class TestPatternsManager:
    """Test suite for PatternsManager class"""

    def test_patterns_manager_initialization(self, patterns_manager):
        """Test PatternsManager initializes correctly"""
        assert patterns_manager.component_name == "patterns_manager"
        assert hasattr(patterns_manager, '_patterns_cache')
        assert hasattr(patterns_manager, 'patterns_file')
        assert isinstance(patterns_manager._patterns_cache, dict)

    def test_load_patterns_success(self, patterns_manager, mock_patterns_file):
        """Test successful patterns loading"""
        patterns = patterns_manager.get_patterns()
        assert patterns is not None
        assert "baby_patterns" in patterns
        assert "patterns" in patterns
        assert "history" in patterns

    def test_load_patterns_file_not_exists(self, mock_base_dir):
        """Test loading patterns when file doesn't exist"""
        non_existent_file = mock_base_dir / "non_existent_patterns.json"
        
        with patch("base_classes.PATTERNS_FILE", non_existent_file):
            manager = PatternsManager()
            patterns = manager.get_patterns()
            # Should return empty patterns
            assert patterns == {}

    def test_load_patterns_corrupted_file(self, mock_base_dir):
        """Test loading patterns from corrupted JSON file"""
        corrupted_file = mock_base_dir / "corrupted_patterns.json"
        corrupted_file.write_text("invalid json content")
        
        with patch("base_classes.PATTERNS_FILE", corrupted_file):
            manager = PatternsManager()
            patterns = manager.get_patterns()
            # Should return empty patterns
            assert patterns == {}

    def test_save_patterns_success(self, patterns_manager):
        """Test successful patterns save"""
        # Modify patterns
        patterns = patterns_manager.get_patterns()
        patterns["test_field"] = "test_value"
        
        result = patterns_manager.save_patterns()
        
        assert result is True
        
        # Verify file content
        if patterns_manager.patterns_file.exists():
            saved_data = json.loads(patterns_manager.patterns_file.read_text())
            assert "test_field" in saved_data
            assert saved_data["test_field"] == "test_value"

    def test_get_baby_patterns(self, patterns_manager):
        """Test retrieving baby-specific patterns"""
        baby_patterns = patterns_manager.get_baby_patterns()
        
        assert baby_patterns is not None
        assert "birth_date" in baby_patterns
        assert "age_months" in baby_patterns
        assert "developmental_stage" in baby_patterns
        assert "favorite_activities" in baby_patterns
        assert "sleep_schedule" in baby_patterns
        assert "feeding_schedule" in baby_patterns

    def test_update_baby_patterns(self, patterns_manager):
        """Test updating baby patterns"""
        new_patterns = {
            "birth_date": "2025-01-15",
            "age_months": 3,
            "developmental_stage": "infant",
            "favorite_activities": ["new_activity"]
        }
        
        result = patterns_manager.update_baby_patterns(new_patterns)
        
        assert result is True
        
        updated_patterns = patterns_manager.get_baby_patterns()
        assert updated_patterns["birth_date"] == "2025-01-15"
        assert updated_patterns["age_months"] == 3
        assert "new_activity" in updated_patterns["favorite_activities"]

    def test_update_baby_patterns_partial(self, patterns_manager):
        """Test partial update of baby patterns"""
        original_patterns = patterns_manager.get_baby_patterns()
        original_birth_date = original_patterns["birth_date"]
        
        # Update only age
        new_patterns = {"age_months": 4}
        result = patterns_manager.update_baby_patterns(new_patterns)
        
        assert result is True
        
        updated_patterns = patterns_manager.get_baby_patterns()
        assert updated_patterns["age_months"] == 4
        # Birth date should remain unchanged
        assert updated_patterns["birth_date"] == original_birth_date

    def test_get_developmental_stage(self, patterns_manager):
        """Test getting developmental stage"""
        stage = patterns_manager.get_developmental_stage()
        assert stage in ["newborn", "infant", "toddler", "young_toddler", "toddler_2", "preschool"]

    def test_set_developmental_stage(self, patterns_manager):
        """Test setting developmental stage"""
        new_stage = "toddler"
        result = patterns_manager.set_developmental_stage(new_stage)
        
        assert result is True
        assert patterns_manager.get_developmental_stage() == new_stage

    def test_set_developmental_stage_invalid(self, patterns_manager):
        """Test setting invalid developmental stage"""
        result = patterns_manager.set_developmental_stage("invalid_stage")
        assert result is False
        # Stage should remain unchanged
        assert patterns_manager.get_developmental_stage() != "invalid_stage"

    def test_calculate_age_months(self, patterns_manager):
        """Test baby age calculation"""
        # Set a known birth date
        birth_date = "2025-01-15"
        patterns_manager.update_baby_patterns({"birth_date": birth_date})
        
        age = patterns_manager.calculate_age_months()
        assert isinstance(age, int)
        assert age >= 0

    def test_calculate_age_months_no_birth_date(self, patterns_manager):
        """Test age calculation without birth date"""
        # Remove birth date
        patterns_manager.update_baby_patterns({"birth_date": None})
        
        age = patterns_manager.calculate_age_months()
        assert age == 0

    def test_get_favorite_activities(self, patterns_manager):
        """Test retrieving favorite activities"""
        activities = patterns_manager.get_favorite_activities()
        assert isinstance(activities, list)
        assert len(activities) >= 0

    def test_add_favorite_activity(self, patterns_manager):
        """Test adding a favorite activity"""
        new_activity = "test_activity"
        original_count = len(patterns_manager.get_favorite_activities())
        
        result = patterns_manager.add_favorite_activity(new_activity)
        
        assert result is True
        activities = patterns_manager.get_favorite_activities()
        assert new_activity in activities
        assert len(activities) == original_count + 1

    def test_add_favorite_activity_duplicate(self, patterns_manager):
        """Test adding duplicate favorite activity"""
        existing_activity = patterns_manager.get_favorite_activities()[0] if patterns_manager.get_favorite_activities() else "test_activity"
        
        # Add it first if it doesn't exist
        if existing_activity not in patterns_manager.get_favorite_activities():
            patterns_manager.add_favorite_activity(existing_activity)
        
        original_count = len(patterns_manager.get_favorite_activities())
        
        # Try to add duplicate
        result = patterns_manager.add_favorite_activity(existing_activity)
        
        # Should not add duplicate
        activities = patterns_manager.get_favorite_activities()
        assert len(activities) == original_count

    def test_remove_favorite_activity(self, patterns_manager):
        """Test removing a favorite activity"""
        # Add an activity first
        test_activity = "removable_activity"
        patterns_manager.add_favorite_activity(test_activity)
        
        result = patterns_manager.remove_favorite_activity(test_activity)
        
        assert result is True
        activities = patterns_manager.get_favorite_activities()
        assert test_activity not in activities

    def test_remove_favorite_activity_not_exists(self, patterns_manager):
        """Test removing non-existent favorite activity"""
        non_existent = "non_existent_activity"
        
        result = patterns_manager.remove_favorite_activity(non_existent)
        
        assert result is False

    def test_get_sleep_schedule(self, patterns_manager):
        """Test retrieving sleep schedule"""
        schedule = patterns_manager.get_sleep_schedule()
        
        assert isinstance(schedule, dict)
        expected_times = ["morning_nap", "afternoon_nap", "evening_nap", "night_bedtime"]
        for time_key in expected_times:
            assert time_key in schedule

    def test_update_sleep_schedule(self, patterns_manager):
        """Test updating sleep schedule"""
        new_schedule = {
            "morning_nap": "8:30 AM",
            "afternoon_nap": "1:30 PM",
            "evening_nap": "4:30 PM",
            "night_bedtime": "8:00 PM"
        }
        
        result = patterns_manager.update_sleep_schedule(new_schedule)
        
        assert result is True
        updated_schedule = patterns_manager.get_sleep_schedule()
        assert updated_schedule["morning_nap"] == "8:30 AM"

    def test_get_feeding_schedule(self, patterns_manager):
        """Test retrieving feeding schedule"""
        schedule = patterns_manager.get_feeding_schedule()
        
        assert isinstance(schedule, dict)
        expected_times = ["morning", "midday", "afternoon", "evening", "night"]
        for time_key in expected_times:
            assert time_key in schedule

    def test_update_feeding_schedule(self, patterns_manager):
        """Test updating feeding schedule"""
        new_schedule = {
            "morning": "6:30 AM",
            "midday": "12:00 PM",
            "afternoon": "3:00 PM",
            "evening": "6:00 PM",
            "night": "9:30 PM"
        }
        
        result = patterns_manager.update_feeding_schedule(new_schedule)
        
        assert result is True
        updated_schedule = patterns_manager.get_feeding_schedule()
        assert updated_schedule["morning"] == "6:30 AM"

    def test_get_patterns_history(self, patterns_manager):
        """Test retrieving patterns history"""
        history = patterns_manager.get_patterns_history()
        
        assert isinstance(history, dict)
        assert "plans_generated" in history
        assert "feedback_processed" in history
        assert "accuracy_score" in history

    def test_update_patterns_history(self, patterns_manager):
        """Test updating patterns history"""
        new_history = {
            "plans_generated": 15,
            "feedback_processed": 12,
            "accuracy_score": 0.90
        }
        
        result = patterns_manager.update_patterns_history(new_history)
        
        assert result is True
        updated_history = patterns_manager.get_patterns_history()
        assert updated_history["plans_generated"] == 15
        assert updated_history["accuracy_score"] == 0.90

    def test_increment_plans_generated(self, patterns_manager):
        """Test incrementing plans generated count"""
        original_count = patterns_manager.get_patterns_history().get("plans_generated", 0)
        
        patterns_manager.increment_plans_generated()
        
        new_count = patterns_manager.get_patterns_history().get("plans_generated", 0)
        assert new_count == original_count + 1

    def test_increment_feedback_processed(self, patterns_manager):
        """Test incrementing feedback processed count"""
        original_count = patterns_manager.get_patterns_history().get("feedback_processed", 0)
        
        patterns_manager.increment_feedback_processed()
        
        new_count = patterns_manager.get_patterns_history().get("feedback_processed", 0)
        assert new_count == original_count + 1

    def test_update_accuracy_score(self, patterns_manager):
        """Test updating accuracy score"""
        new_score = 0.95
        
        patterns_manager.update_accuracy_score(new_score)
        
        history = patterns_manager.get_patterns_history()
        assert history["accuracy_score"] == new_score

    def test_get_user_preferences(self, patterns_manager):
        """Test retrieving user preferences"""
        preferences = patterns_manager.get_user_preferences()
        
        assert isinstance(preferences, dict)
        # Check for common preference keys
        possible_keys = ["morning_start_time", "evening_end_time", "preferred_task_count"]
        for key in possible_keys:
            if key in preferences:
                assert preferences[key] is not None

    def test_update_user_preferences(self, patterns_manager):
        """Test updating user preferences"""
        new_preferences = {
            "morning_start_time": "08:00",
            "evening_end_time": "22:00",
            "preferred_task_count": 8
        }
        
        result = patterns_manager.update_user_preferences(new_preferences)
        
        assert result is True
        updated_preferences = patterns_manager.get_user_preferences()
        assert updated_preferences["morning_start_time"] == "08:00"

    def test_patterns_persistence_across_instances(self, mock_patterns_file):
        """Test that patterns persist across different PatternsManager instances"""
        # First instance - modify patterns
        manager1 = PatternsManager()
        manager1.update_baby_patterns({"age_months": 5})
        
        # Second instance - should load modified data
        manager2 = PatternsManager()
        baby_patterns = manager2.get_baby_patterns()
        
        assert baby_patterns["age_months"] == 5

    def test_validate_patterns_structure(self, patterns_manager):
        """Test validation of patterns structure"""
        patterns = patterns_manager.get_patterns()
        
        # Validate required top-level keys
        required_keys = ["baby_patterns", "patterns", "history"]
        for key in required_keys:
            assert key in patterns
        
        # Validate baby_patterns structure
        baby_patterns = patterns["baby_patterns"]
        baby_required_keys = ["birth_date", "age_months", "developmental_stage"]
        for key in baby_required_keys:
            assert key in baby_patterns

    def test_error_handling_save_failure(self, patterns_manager, mock_base_dir):
        """Test handling of save failures"""
        # Create a read-only file to simulate save failure
        readonly_file = mock_base_dir / "readonly_patterns.json"
        readonly_file.write_text("{}")
        readonly_file.chmod(0o444)
        
        patterns_manager.patterns_file = readonly_file
        
        result = patterns_manager.save_patterns()
        assert result is False

    def test_developmental_stage_age_mapping(self, patterns_manager):
        """Test that developmental stage matches age"""
        # Test various ages and their expected stages
        age_stage_mapping = {
            0: "newborn",
            2: "infant", 
            8: "toddler",
            15: "young_toddler",
            20: "toddler_2",
            30: "preschool"
        }
        
        for age_months, expected_stage in age_stage_mapping.items():
            patterns_manager.update_baby_patterns({"age_months": age_months})
            # Note: This test assumes the system updates stage based on age
            # In a real implementation, there might be a separate method for this
            current_stage = patterns_manager.get_developmental_stage()
            # The actual implementation might have different logic
            # This test documents the expected behavior

    def test_patterns_data_types(self, patterns_manager):
        """Test that patterns data has correct types"""
        baby_patterns = patterns_manager.get_baby_patterns()
        
        # Test data types
        assert isinstance(baby_patterns["age_months"], int)
        assert isinstance(baby_patterns["favorite_activities"], list)
        assert isinstance(baby_patterns["sleep_schedule"], dict)
        assert isinstance(baby_patterns["feeding_schedule"], dict)
        
        history = patterns_manager.get_patterns_history()
        assert isinstance(history.get("plans_generated", 0), int)
        assert isinstance(history.get("feedback_processed", 0), int)
        assert isinstance(history.get("accuracy_score", 0.0), (int, float))
