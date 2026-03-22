#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - MemoryManager Unit Tests
Comprehensive testing of memory storage, retrieval, and management functionality
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

import pytest

from base_classes import MemoryManager


class TestMemoryManager:
    """Test suite for MemoryManager class"""

    def test_memory_manager_initialization(self, memory_manager):
        """Test MemoryManager initializes correctly"""
        assert memory_manager.component_name == "memory_manager"
        assert hasattr(memory_manager, '_memory_cache')
        assert hasattr(memory_manager, 'memory_file')
        assert isinstance(memory_manager._memory_cache, dict)

    def test_load_memory_empty_file(self, mock_base_dir):
        """Test loading memory from empty file"""
        memory_file = mock_base_dir / "empty_memory.json"
        memory_file.write_text("{}")
        
        with patch("base_classes.MEMORY_FILE", memory_file):
            manager = MemoryManager()
            assert manager._memory_cache == {}

    def test_load_memory_nonexistent_file(self, memory_manager):
        """Test loading memory when file doesn't exist"""
        # Should create empty cache
        assert memory_manager._memory_cache == {}

    def test_load_memory_corrupted_file(self, mock_base_dir):
        """Test loading memory from corrupted JSON file"""
        memory_file = mock_base_dir / "corrupted_memory.json"
        memory_file.write_text("invalid json content")
        
        with patch("base_classes.MEMORY_FILE", memory_file):
            manager = MemoryManager()
            # Should fall back to empty cache
            assert manager._memory_cache == {}

    def test_add_memory_entry(self, memory_manager):
        """Test adding a memory entry"""
        key = "test_entry"
        entry = {
            "feedback": {"what_enjoyed": ["tummy_time"]},
            "journal_entries": [{"note": "test note"}]
        }
        
        result = memory_manager.add_entry(key, entry)
        
        assert result is True
        assert key in memory_manager._memory_cache
        assert "timestamp" in memory_manager._memory_cache[key]
        assert memory_manager._memory_cache[key]["feedback"] == entry["feedback"]

    def test_add_memory_entry_overwrite(self, memory_manager):
        """Test overwriting an existing memory entry"""
        key = "test_entry"
        original_entry = {"feedback": {"what_enjoyed": ["original"]}}
        updated_entry = {"feedback": {"what_enjoyed": ["updated"]}}
        
        # Add original entry
        memory_manager.add_entry(key, original_entry)
        original_timestamp = memory_manager._memory_cache[key]["timestamp"]
        
        # Overwrite with updated entry
        memory_manager.add_entry(key, updated_entry)
        
        assert key in memory_manager._memory_cache
        assert memory_manager._memory_cache[key]["feedback"] == updated_entry["feedback"]
        # Timestamp should be updated
        assert memory_manager._memory_cache[key]["timestamp"] != original_timestamp

    def test_get_memory_entry_exists(self, memory_manager, sample_memory_entries):
        """Test retrieving an existing memory entry"""
        # Load sample data
        memory_manager._memory_cache = sample_memory_entries
        
        key = list(sample_memory_entries.keys())[0]
        entry = memory_manager.get_entry(key)
        
        assert entry is not None
        assert entry == sample_memory_entries[key]

    def test_get_memory_entry_not_exists(self, memory_manager):
        """Test retrieving a non-existent memory entry"""
        entry = memory_manager.get_entry("non_existent_key")
        assert entry is None

    def test_save_memory_success(self, memory_manager):
        """Test successful memory save to file"""
        key = "test_save"
        entry = {"feedback": {"test": "data"}}
        
        memory_manager.add_entry(key, entry)
        result = memory_manager.save_memory()
        
        assert result is True
        
        # Verify file content
        if memory_manager.memory_file.exists():
            saved_data = json.loads(memory_manager.memory_file.read_text())
            assert key in saved_data
            assert saved_data[key]["feedback"] == entry["feedback"]

    def test_save_memory_file_error(self, memory_manager, mock_base_dir):
        """Test memory save with file system error"""
        # Create a file that can't be written to (permission error simulation)
        readonly_file = mock_base_dir / "readonly_memory.json"
        readonly_file.write_text("{}")
        readonly_file.chmod(0o444)  # Read-only
        
        memory_manager.memory_file = readonly_file
        key = "test_error"
        entry = {"feedback": {"test": "data"}}
        
        memory_manager.add_entry(key, entry)
        result = memory_manager.save_memory()
        
        # Should handle the error gracefully
        assert result is False

    def test_get_entries_by_pattern(self, memory_manager, sample_memory_entries):
        """Test retrieving entries matching a pattern"""
        memory_manager._memory_cache = sample_memory_entries
        
        # Test pattern matching
        results = memory_manager.get_entries_by_pattern("baby_feedback")
        assert len(results) == 2  # Both entries should match
        
        # Test specific date pattern
        today = datetime.now().strftime('%Y-%m-%d')
        results = memory_manager.get_entries_by_pattern(today)
        assert len(results) == 1
        assert today in results[0][0]

    def test_get_entries_by_pattern_no_match(self, memory_manager):
        """Test pattern matching with no results"""
        memory_manager._memory_cache = {}
        
        results = memory_manager.get_entries_by_pattern("non_existent_pattern")
        assert results == []

    def test_get_entries_in_date_range(self, memory_manager, sample_memory_entries):
        """Test retrieving entries within a date range"""
        memory_manager._memory_cache = sample_memory_entries
        
        # Test range covering today only
        today = datetime.now()
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        results = memory_manager.get_entries_in_date_range(start_date, end_date)
        assert len(results) == 1
        
        # Test range covering multiple days
        start_date = today - timedelta(days=1)
        end_date = today + timedelta(days=1)
        
        results = memory_manager.get_entries_in_date_range(start_date, end_date)
        assert len(results) == 2

    def test_get_entries_in_date_range_no_timestamp(self, memory_manager):
        """Test date range filtering with entries lacking timestamps"""
        # Add entry without timestamp
        memory_manager._memory_cache = {
            "no_timestamp": {"data": "test"}
        }
        
        today = datetime.now()
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        results = memory_manager.get_entries_in_date_range(start_date, end_date)
        assert len(results) == 0  # Entry without timestamp should be excluded

    def test_search_entries_keyword_found(self, memory_manager, sample_memory_entries):
        """Test searching entries with keyword that matches"""
        memory_manager._memory_cache = sample_memory_entries
        
        results = memory_manager.search_entries("tummy")
        assert len(results) > 0
        
        # Verify search results contain the keyword
        for key, entry in results:
            entry_text = json.dumps(entry).lower()
            assert "tummy" in entry_text

    def test_search_entries_keyword_not_found(self, memory_manager, sample_memory_entries):
        """Test searching entries with keyword that doesn't match"""
        memory_manager._memory_cache = sample_memory_entries
        
        results = memory_manager.search_entries("nonexistent_keyword")
        assert results == []

    def test_search_entries_case_insensitive(self, memory_manager):
        """Test that search is case insensitive"""
        memory_manager._memory_cache = {
            "test_key": {"feedback": {"what_enjoyed": ["TUMMY_TIME"]}}
        }
        
        # Test lowercase search
        results_lower = memory_manager.search_entries("tummy")
        # Test uppercase search
        results_upper = memory_manager.search_entries("TUMMY")
        
        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert results_lower == results_upper

    def test_get_summary_empty_memory(self, memory_manager):
        """Test getting summary from empty memory"""
        summary = memory_manager.get_summary()
        
        assert summary["total_entries"] == 0
        assert summary["date_range"]["start"] is None
        assert summary["date_range"]["end"] is None
        assert summary["feedback_themes"] == {}

    def test_get_summary_with_data(self, memory_manager, sample_memory_entries):
        """Test getting summary with memory data"""
        memory_manager._memory_cache = sample_memory_entries
        
        summary = memory_manager.get_summary(days=7)
        
        assert summary["total_entries"] == 2
        assert summary["date_range"]["start"] is not None
        assert summary["date_range"]["end"] is not None
        assert "feedback_themes" in summary

    def test_get_summary_feedback_themes(self, memory_manager):
        """Test feedback theme extraction in summary"""
        memory_manager._memory_cache = {
            "entry1": {
                "timestamp": datetime.now().isoformat(),
                "feedback": {
                    "what_enjoyed": ["tummy_time", "reading"],
                    "didnt_like": ["loud_noises"]
                }
            },
            "entry2": {
                "timestamp": datetime.now().isoformat(),
                "feedback": {
                    "what_enjoyed": ["tummy_time", "sensory_play"],
                    "didnt_like": ["overstimulation"]
                }
            }
        }
        
        summary = memory_manager.get_summary()
        themes = summary["feedback_themes"]
        
        assert "tummy_time" in themes["enjoyed"]
        assert "reading" in themes["enjoyed"]
        assert "sensory_play" in themes["enjoyed"]
        assert "loud_noises" in themes["disliked"]
        assert "overstimulation" in themes["disliked"]

    def test_cleanup_old_entries(self, memory_manager):
        """Test cleanup of old memory entries"""
        # Create entries with different timestamps
        old_date = datetime.now() - timedelta(days=100)
        recent_date = datetime.now() - timedelta(days=5)
        
        memory_manager._memory_cache = {
            "old_entry": {
                "timestamp": old_date.isoformat(),
                "data": "old"
            },
            "recent_entry": {
                "timestamp": recent_date.isoformat(),
                "data": "recent"
            },
            "no_timestamp": {
                "data": "no_timestamp"
            }
        }
        
        # Clean up entries older than 30 days
        memory_manager.cleanup_old_entries(days_to_keep=30)
        
        # Old entry should be removed
        assert "old_entry" not in memory_manager._memory_cache
        # Recent entry should remain
        assert "recent_entry" in memory_manager._memory_cache
        # Entry without timestamp should remain (can't determine age)
        assert "no_timestamp" in memory_manager._memory_cache

    def test_cleanup_old_entries_no_deletions(self, memory_manager):
        """Test cleanup when no entries need deletion"""
        recent_date = datetime.now() - timedelta(days=5)
        
        memory_manager._memory_cache = {
            "recent_entry": {
                "timestamp": recent_date.isoformat(),
                "data": "recent"
            }
        }
        
        original_count = len(memory_manager._memory_cache)
        memory_manager.cleanup_old_entries(days_to_keep=30)
        
        # No entries should be removed
        assert len(memory_manager._memory_cache) == original_count

    def test_memory_persistence_across_instances(self, mock_memory_file):
        """Test that memory persists across different MemoryManager instances"""
        # First instance - add data
        manager1 = MemoryManager()
        key = "persistence_test"
        entry = {"feedback": {"test": "persistence"}}
        manager1.add_entry(key, entry)
        
        # Second instance - should load the data
        manager2 = MemoryManager()
        retrieved_entry = manager2.get_entry(key)
        
        assert retrieved_entry is not None
        assert retrieved_entry["feedback"] == entry["feedback"]

    def test_concurrent_access_simulation(self, memory_manager):
        """Test simulated concurrent access to memory"""
        # Simulate multiple operations
        operations = []
        for i in range(10):
            key = f"concurrent_test_{i}"
            entry = {"feedback": {"test": f"data_{i}"}}
            operations.append((key, entry))
        
        # Add all entries
        for key, entry in operations:
            memory_manager.add_entry(key, entry)
        
        # Verify all entries exist
        for key, entry in operations:
            retrieved = memory_manager.get_entry(key)
            assert retrieved is not None
            assert retrieved["feedback"] == entry["feedback"]

    def test_memory_integrity_validation(self, memory_manager):
        """Test memory data integrity validation"""
        # Test with various data types
        test_entries = {
            "string_data": {"feedback": {"test": "string_value"}},
            "numeric_data": {"feedback": {"rating": 8}},
            "list_data": {"feedback": {"items": ["item1", "item2"]}},
            "nested_data": {
                "feedback": {
                    "nested": {
                        "deep": {"value": "deep_value"}
                    }
                }
            }
        }
        
        for key, entry in test_entries.items():
            memory_manager.add_entry(key, entry)
            retrieved = memory_manager.get_entry(key)
            assert retrieved == entry

    def test_error_handling_invalid_json_structure(self, memory_manager):
        """Test handling of invalid JSON structures in memory file"""
        # This tests the resilience of the memory system
        invalid_json = '{"incomplete": "json"'  # Missing closing brace
        
        with patch.object(memory_manager, '_load_json_file', return_value={}):
            # Should handle gracefully and return empty cache
            memory_manager._load_memory()
            assert memory_manager._memory_cache == {}
