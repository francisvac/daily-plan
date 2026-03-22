#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Feedback Pipeline Integration Tests
Integration testing of the complete feedback processing workflow
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest

from email_command_processor import EmailCommandProcessor
from base_classes import MemoryManager, PatternsManager


class TestFeedbackPipelineIntegration:
    """Integration tests for the complete feedback processing pipeline"""

    def test_complete_feedback_to_memory_pipeline(self, processor_with_mocks, memory_manager):
        """Test complete pipeline: email feedback -> memory storage"""
        processor = processor_with_mocks
        
        # Simulate incoming feedback email
        email_data = {
            'from': 'parent@example.com',
            'subject': 'Baby Feedback - 2025-03-22',
            'body': 'feedback Baby loved tummy time today and enjoyed reading books'
        }
        
        with patch.object(processor, '_parse_email_message') as mock_parse, \
             patch.object(processor, '_extract_commands_from_email_body') as mock_extract, \
             patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            # Setup mocks
            mock_parse.return_value = email_data
            mock_extract.return_value = [{'command': 'feedback', 'args': 'Baby loved tummy time today and enjoyed reading books'}]
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'normal',
                    'developmental': []
                },
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            
            # Process the email
            result = processor._process_single_email("email_123")
            
            # Verify the pipeline worked
            assert result is not None
            mock_parse.assert_called_once()
            mock_extract.assert_called_once()
            mock_get_entry.assert_called_once()
            mock_add_entry.assert_called_once()
            
            # Verify feedback was processed correctly
            call_args = mock_add_entry.call_args
            key, entry = call_args[0]
            assert 'baby_feedback_' in key
            assert 'tummy time' in entry['feedback']['what_enjoyed'][0]
            assert 'reading books' in entry['feedback']['what_enjoyed'][1]

    def test_feedback_to_patterns_learning(self, processor_with_mocks, memory_manager, patterns_manager):
        """Test feedback influencing pattern learning"""
        processor = processor_with_mocks
        
        # Simulate multiple feedback entries
        feedback_entries = [
            'feedback Baby loved tummy time',
            'feedback Baby enjoyed tummy time again',
            'feedback Baby really likes tummy time sessions'
        ]
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry, \
             patch.object(memory_manager, 'search_entries') as mock_search, \
             patch.object(patterns_manager, 'add_favorite_activity') as mock_add_activity:
            
            # Setup existing entry
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'normal',
                    'developmental': []
                },
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            mock_search.return_value = [
                ('key1', {'feedback': {'what_enjoyed': ['tummy time']}}),
                ('key2', {'feedback': {'what_enjoyed': ['tummy time']}}),
                ('key3', {'feedback': {'what_enjoyed': ['tummy time']}})
            ]
            mock_add_activity.return_value = True
            
            # Process multiple feedback entries
            for feedback in feedback_entries:
                command = {'command': 'feedback', 'args': feedback.replace('feedback ', '')}
                processor._execute_command(command)
            
            # Simulate pattern learning from accumulated feedback
            processor._learn_patterns_from_feedback()
            
            # Verify pattern learning was triggered
            mock_search.assert_called()
            mock_add_activity.assert_called_with('tummy_time')

    def test_journal_entry_to_memory_integration(self, processor_with_mocks, memory_manager):
        """Test journal entries being stored in memory"""
        processor = processor_with_mocks
        
        journal_entries = [
            'journal Had a wonderful morning with lots of smiles',
            'journal Afternoon was challenging with some fussiness',
            'journal Evening routine went smoothly'
        ]
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            # Setup existing entry
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'normal',
                    'developmental': []
                },
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            
            # Process journal entries
            for entry in journal_entries:
                command = {'command': 'journal', 'args': entry.replace('journal ', '')}
                result = processor._execute_command(command)
                
                assert "✅ Journal entry added" in result
            
            # Verify all entries were added
            assert mock_add_entry.call_count == len(journal_entries)
            
            # Check journal entries structure
            for call in mock_add_entry.call_args_list:
                key, memory_entry = call[0]
                assert len(memory_entry['journal_entries']) > 0
                assert 'note' in memory_entry['journal_entries'][0]
                assert 'time' in memory_entry['journal_entries'][0]

    def test_memory_retrieval_to_email_response(self, processor_with_mocks, memory_manager):
        """Test memory retrieval generating appropriate email responses"""
        processor = processor_with_mocks
        
        # Setup test memory data
        today = datetime.now().strftime('%Y-%m-%d')
        test_memory = {
            f'baby_feedback_{today}': {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': ['tummy time', 'reading'],
                    'didnt_like': ['loud noises'],
                    'sleep_quality': '8',
                    'feeding_response': 'good',
                    'developmental': ['tracking objects']
                },
                'journal_entries': [
                    {'note': 'Great morning', 'time': '10:00 AM'},
                    {'note': 'Challenging afternoon', 'time': '2:00 PM'}
                ]
            }
        }
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry:
            mock_get_entry.return_value = test_memory[f'baby_feedback_{today}']
            
            # Test memory retrieval command
            result = processor._handle_memory_command("today")
            
            # Verify response contains memory data
            assert "Today's Memory" in result
            assert "tummy time" in result
            assert "reading" in result
            assert "loud noises" in result
            assert "Great morning" in result
            assert "Challenging afternoon" in result

    def test_patterns_summary_generation(self, processor_with_mocks, patterns_manager):
        """Test patterns summary generation from accumulated data"""
        processor = processor_with_mocks
        
        # Setup test patterns
        test_patterns = {
            "baby_patterns": {
                "age_months": 2,
                "developmental_stage": "infant",
                "favorite_activities": ["tummy_time", "reading", "sensory_play"],
                "sleep_schedule": {
                    "morning_nap": "9:00 AM",
                    "afternoon_nap": "1:00 PM",
                    "evening_nap": "4:00 PM",
                    "night_bedtime": "7:30 PM"
                }
            },
            "patterns": {
                "feedback_themes": {
                    "what_works": ["gentle_touch", "voice_soothing"],
                    "what_doesnt_work": ["loud_noises"],
                    "success_factors": ["quiet_environment"]
                }
            },
            "history": {
                "plans_generated": 15,
                "feedback_processed": 12,
                "accuracy_score": 0.85
            }
        }
        
        with patch.object(patterns_manager, 'get_patterns') as mock_get_patterns, \
             patch.object(patterns_manager, 'get_baby_patterns') as mock_get_baby:
            
            mock_get_patterns.return_value = test_patterns
            mock_get_baby.return_value = test_patterns["baby_patterns"]
            
            # Test patterns command
            result = processor._handle_patterns_command("")
            
            # Verify patterns summary
            assert "Current Baby Patterns" in result
            assert "2 months" in result
            assert "infant" in result
            assert "tummy_time" in result
            assert "reading" in result
            assert "gentle_touch" in result
            assert "loud_noises" in result
            assert "15 plans" in result
            assert "85%" in result

    def test_multi_command_email_processing(self, processor_with_mocks, memory_manager):
        """Test processing email with multiple commands"""
        processor = processor_with_mocks
        
        email_body = """
        Today's feedback:
        feedback Baby loved tummy time and enjoyed reading
        
        Journal entry:
        journal Had a great morning with lots of smiles
        
        Show me this week's memory:
        memory week
        
        Current patterns:
        patterns
        """
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry, \
             patch.object(memory_manager, 'get_entries_in_date_range') as mock_get_range, \
             patch.object(processor, '_handle_patterns_command') as mock_patterns:
            
            # Setup mocks
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            mock_get_range.return_value = []
            mock_patterns.return_value = "Patterns summary"
            
            # Extract commands
            commands = processor._extract_commands_from_email_body(email_body)
            
            # Verify all commands were extracted
            assert len(commands) == 4
            assert commands[0]['command'] == 'feedback'
            assert commands[1]['command'] == 'journal'
            assert commands[2]['command'] == 'memory'
            assert commands[3]['command'] == 'patterns'
            
            # Execute all commands
            results = []
            for command in commands:
                result = processor._execute_command(command)
                results.append(result)
            
            # Verify all commands were processed
            assert len(results) == 4
            assert any("✅ Feedback added" in result for result in results)
            assert any("✅ Journal entry added" in result for result in results)
            assert any("This Week's Memory" in result for result in results)
            assert any("Current Baby Patterns" in result for result in results)

    def test_feedback_categorization_accuracy(self, processor_with_mocks, memory_manager):
        """Test accurate categorization of feedback content"""
        processor = processor_with_mocks
        
        feedback_samples = [
            ('Baby loved tummy time', 'enjoyed'),
            ('Baby enjoyed reading books', 'enjoyed'),
            ('Baby really likes sensory play', 'enjoyed'),
            ('Baby was fussy during loud noises', 'disliked'),
            ('Baby disliked sudden movements', 'disliked'),
            ('Baby got upset with overstimulation', 'disliked'),
            ('Baby had good feeding', 'feeding'),
            ('Baby slept well last night', 'sleep')
        ]
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'normal',
                    'developmental': []
                },
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            
            # Process each feedback sample
            for feedback_text, expected_category in feedback_samples:
                command = {'command': 'feedback', 'args': feedback_text}
                processor._execute_command(command)
                
                # Verify the feedback was processed
                mock_add_entry.assert_called()
                
                # Check categorization logic (simplified for this test)
                call_args = mock_add_entry.call_args
                key, entry = call_args[0]
                feedback_data = entry['feedback']
                
                if expected_category == 'enjoyed':
                    assert len(feedback_data['what_enjoyed']) > 0
                elif expected_category == 'disliked':
                    assert len(feedback_data['didnt_like']) > 0

    def test_memory_search_integration(self, processor_with_mocks, memory_manager):
        """Test memory search functionality integration"""
        processor = processor_with_mocks
        
        # Setup test memory data with various entries
        test_entries = {
            'baby_feedback_2025-03-20': {
                'feedback': {'what_enjoyed': ['tummy time', 'reading']},
                'timestamp': '2025-03-20T10:00:00'
            },
            'baby_feedback_2025-03-21': {
                'feedback': {'what_enjoyed': ['sensory play'], 'didnt_like': ['loud noises']},
                'timestamp': '2025-03-21T10:00:00'
            },
            'baby_feedback_2025-03-22': {
                'feedback': {'what_enjoyed': ['tummy time'], 'developmental': ['better head control']},
                'timestamp': '2025-03-22T10:00:00'
            }
        }
        
        with patch.object(memory_manager, 'search_entries') as mock_search:
            mock_search.return_value = [
                ('baby_feedback_2025-03-20', test_entries['baby_feedback_2025-03-20']),
                ('baby_feedback_2025-03-22', test_entries['baby_feedback_2025-03-22'])
            ]
            
            # Test search command
            result = processor._handle_memory_command("search tummy")
            
            # Verify search results
            assert "Search Results" in result
            assert "tummy" in result
            assert "2025-03-20" in result
            assert "2025-03-22" in result
            mock_search.assert_called_once_with("tummy")

    def test_error_recovery_in_pipeline(self, processor_with_mocks, memory_manager):
        """Test error recovery in the feedback processing pipeline"""
        processor = processor_with_mocks
        
        # Test scenario where memory save fails
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            # Setup memory save failure
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                'journal_entries': []
            }
            mock_add_entry.return_value = False  # Simulate save failure
            
            # Process feedback
            command = {'command': 'feedback', 'args': 'Baby loved tummy time'}
            result = processor._execute_command(command)
            
            # Verify error handling
            # The system should handle the failure gracefully
            assert result is not None

    def test_concurrent_feedback_processing(self, processor_with_mocks, memory_manager):
        """Test handling of multiple feedback entries in sequence"""
        processor = processor_with_mocks
        
        feedback_batch = [
            'feedback Baby loved morning tummy time',
            'journal Great morning session',
            'feedback Baby enjoyed afternoon reading',
            'journal Afternoon was calm and peaceful',
            'feedback Baby liked evening sensory play'
        ]
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            
            # Process all feedback in sequence
            results = []
            for feedback in feedback_batch:
                if 'feedback' in feedback:
                    command = {'command': 'feedback', 'args': feedback.replace('feedback ', '')}
                else:
                    command = {'command': 'journal', 'args': feedback.replace('journal ', '')}
                
                result = processor._execute_command(command)
                results.append(result)
            
            # Verify all were processed
            assert len(results) == len(feedback_batch)
            assert all(result is not None for result in results)
            assert mock_add_entry.call_count == len(feedback_batch)

    def test_data_consistency_across_pipeline(self, processor_with_mocks, memory_manager):
        """Test data consistency throughout the feedback pipeline"""
        processor = processor_with_mocks
        
        # Test that data remains consistent through processing
        original_feedback = "Baby loved tummy time and enjoyed reading books this morning"
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            
            # Process feedback
            command = {'command': 'feedback', 'args': original_feedback}
            processor._execute_command(command)
            
            # Verify data consistency
            call_args = mock_add_entry.call_args
            key, entry = call_args[0]
            
            # Check that original feedback content is preserved
            feedback_data = entry['feedback']
            assert 'tummy time' in str(feedback_data)
            assert 'reading books' in str(feedback_data)
            
            # Check that timestamp is added
            assert 'timestamp' in entry
            assert entry['timestamp'] is not None

    def test_pipeline_performance_with_large_dataset(self, processor_with_mocks, memory_manager):
        """Test pipeline performance with larger datasets"""
        processor = processor_with_mocks
        
        # Generate large number of feedback entries
        large_feedback_set = []
        for i in range(50):
            large_feedback_set.append(f'feedback Baby enjoyed activity_{i}')
        
        with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            
            # Process all feedback
            for feedback in large_feedback_set:
                command = {'command': 'feedback', 'args': feedback.replace('feedback ', '')}
                processor._execute_command(command)
            
            # Verify all were processed
            assert mock_add_entry.call_count == len(large_feedback_set)
            
            # Performance should remain reasonable
            # (This is a basic check - in real implementation, you'd measure actual timing)
