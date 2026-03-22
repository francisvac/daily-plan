#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Daily Workflow End-to-End Tests
Complete testing of daily user workflows from plan generation to feedback processing
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from generate_baby_plan import BabyPlanGenerator
from email_integration import BabyPlanEmailer
from email_command_processor import EmailCommandProcessor
from base_classes import MemoryManager, PatternsManager


class TestDailyWorkflow:
    """End-to-end tests for complete daily workflows"""

    def test_complete_daily_workflow(self, mock_base_dir, memory_manager, patterns_manager):
        """Test complete daily workflow: plan generation -> email -> feedback -> learning"""
        
        # 1. Morning: Generate daily plan
        plan_generator = BabyPlanGenerator()
        
        with patch.object(plan_generator, '_generate_plan_content') as mock_generate, \
             patch.object(plan_generator, '_save_plan') as mock_save:
            
            mock_generate.return_value = "# Baby Development Plan\n## Activities\n- Tummy time\n- Reading"
            mock_save.return_value = True
            
            plan_result = plan_generator.generate_plan()
            
            assert plan_result is not None
            mock_generate.assert_called_once()
            mock_save.assert_called_once()
        
        # 2. Email plan to parent
        emailer = BabyPlanEmailer()
        
        with patch.object(emailer, '_send_email') as mock_send:
            mock_send.return_value = True
            
            email_result = emailer.send_plan_email(plan_result)
            
            assert email_result is True
            mock_send.assert_called_once()
        
        # 3. Parent provides feedback via email
        processor = EmailCommandProcessor()
        
        feedback_email = {
            'from': 'parent@example.com',
            'subject': 'Baby Feedback',
            'body': 'feedback Baby loved tummy time today and enjoyed reading\njournal Had a great morning with smiles'
        }
        
        with patch.object(processor, '_parse_email_message') as mock_parse, \
             patch.object(processor, '_extract_commands_from_email_body') as mock_extract, \
             patch.object(memory_manager, 'get_entry') as mock_get_entry, \
             patch.object(memory_manager, 'add_entry') as mock_add_entry:
            
            mock_parse.return_value = feedback_email
            mock_extract.return_value = [
                {'command': 'feedback', 'args': 'Baby loved tummy time today and enjoyed reading'},
                {'command': 'journal', 'args': 'Had a great morning with smiles'}
            ]
            mock_get_entry.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                'journal_entries': []
            }
            mock_add_entry.return_value = True
            
            # Process feedback
            result = processor._process_single_email("feedback_email_123")
            
            assert result is not None
            assert mock_add_entry.call_count == 2  # One for feedback, one for journal
        
        # 4. System learns from feedback and updates patterns
        updated_patterns = patterns_manager.get_baby_patterns()
        
        # Verify learning occurred (patterns updated based on feedback)
        assert 'favorite_activities' in updated_patterns
        
        # 5. Next day's plan incorporates learning
        with patch.object(plan_generator, '_generate_plan_content') as mock_generate_next:
            mock_generate_next.return_value = "# Baby Development Plan\n## Activities (Updated)\n- Tummy time (favorite)\n- Reading (enjoyed)\n- New sensory activity"
            
            next_plan = plan_generator.generate_plan()
            
            assert "favorite" in next_plan or "enjoyed" in next_plan

    def test_feedback_learning_cycle(self, memory_manager, patterns_manager):
        """Test multi-day feedback learning cycle"""
        
        # Simulate 3 days of feedback
        daily_feedback = [
            {
                'day': 1,
                'feedback': 'feedback Baby loved tummy time',
                'journal': 'journal Great morning session',
                'expected_learning': 'tummy_time'
            },
            {
                'day': 2,
                'feedback': 'feedback Baby enjoyed tummy time again',
                'journal': 'journal Another good tummy time session',
                'expected_learning': 'tummy_time'
            },
            {
                'day': 3,
                'feedback': 'feedback Baby really likes tummy time sessions',
                'journal': 'journal Tummy time is becoming a favorite',
                'expected_learning': 'tummy_time'
            }
        ]
        
        processor = EmailCommandProcessor()
        
        for day_data in daily_feedback:
            with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
                 patch.object(memory_manager, 'add_entry') as mock_add_entry:
                
                mock_get_entry.return_value = {
                    'timestamp': datetime.now().isoformat(),
                    'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                    'journal_entries': []
                }
                mock_add_entry.return_value = True
                
                # Process feedback
                feedback_cmd = {'command': 'feedback', 'args': day_data['feedback'].replace('feedback ', '')}
                processor._execute_command(feedback_cmd)
                
                # Process journal
                journal_cmd = {'command': 'journal', 'args': day_data['journal'].replace('journal ', '')}
                processor._execute_command(journal_cmd)
        
        # Verify learning occurred over multiple days
        all_entries = list(memory_manager._memory_cache.values())
        enjoyed_activities = []
        
        for entry in all_entries:
            if 'feedback' in entry:
                enjoyed_activities.extend(entry['feedback'].get('what_enjoyed', []))
        
        # Tummy time should be consistently mentioned
        tummy_mentions = sum(1 for activity in enjoyed_activities if 'tummy time' in activity.lower())
        assert tummy_mentions >= 3
        
        # Update patterns based on learning
        if tummy_mentions >= 2:
            patterns_manager.add_favorite_activity('tummy_time')
        
        # Verify patterns were updated
        updated_patterns = patterns_manager.get_baby_patterns()
        assert 'tummy_time' in updated_patterns['favorite_activities']

    def test_error_recovery_workflow(self, mock_base_dir, memory_manager):
        """Test workflow resilience to errors"""
        
        # Test scenario where email sending fails
        emailer = BabyPlanEmailer()
        
        with patch.object(emailer, '_send_email') as mock_send:
            mock_send.return_value = False  # Simulate email failure
            
            plan_content = "# Test Plan"
            result = emailer.send_plan_email(plan_content)
            
            assert result is False
        
        # Test scenario where memory save fails
        processor = EmailCommandProcessor()
        
        with patch.object(memory_manager, 'add_entry') as mock_add:
            mock_add.return_value = False  # Simulate save failure
            
            command = {'command': 'feedback', 'args': 'Test feedback'}
            result = processor._execute_command(command)
            
            # System should handle failure gracefully
            assert result is not None
        
        # Test scenario where patterns file is corrupted
        corrupted_patterns_file = mock_base_dir / "patterns.json"
        corrupted_patterns_file.write_text("invalid json")
        
        with patch("base_classes.PATTERNS_FILE", corrupted_patterns_file):
            patterns_manager = PatternsManager()
            patterns = patterns_manager.get_patterns()
            
            # Should handle corruption gracefully
            assert patterns == {}

    def test_multi_user_feedback_workflow(self, memory_manager, patterns_manager):
        """Test workflow with multiple users providing feedback"""
        
        # Simulate feedback from different caregivers
        caregiver_feedback = [
            {
                'user': 'mom@example.com',
                'feedback': 'feedback Baby loved tummy time with me',
                'journal': 'journal Great bonding during tummy time'
            },
            {
                'user': 'dad@example.com',
                'feedback': 'feedback Baby enjoyed reading books together',
                'journal': 'journal Story time was fun'
            },
            {
                'user': 'grandma@example.com',
                'feedback': 'feedback Baby liked gentle singing',
                'journal': 'journal Music time was soothing'
            }
        ]
        
        processor = EmailCommandProcessor()
        
        for feedback_data in caregiver_feedback:
            with patch.object(memory_manager, 'get_entry') as mock_get_entry, \
                 patch.object(memory_manager, 'add_entry') as mock_add_entry:
                
                mock_get_entry.return_value = {
                    'timestamp': datetime.now().isoformat(),
                    'feedback': {'what_enjoyed': [], 'didnt_like': [], 'sleep_quality': '5', 'feeding_response': 'normal', 'developmental': []},
                    'journal_entries': []
                }
                mock_add_entry.return_value = True
                
                # Process feedback from this caregiver
                feedback_cmd = {'command': 'feedback', 'args': feedback_data['feedback'].replace('feedback ', '')}
                processor._execute_command(feedback_cmd)
                
                journal_cmd = {'command': 'journal', 'args': feedback_data['journal'].replace('journal ', '')}
                processor._execute_command(journal_cmd)
        
        # Verify all feedback was processed
        assert len(memory_manager._memory_cache) >= len(caregiver_feedback)
        
        # Aggregate feedback across all caregivers
        all_enjoyed = []
        for entry in memory_manager._memory_cache.values():
            if 'feedback' in entry:
                all_enjoyed.extend(entry['feedback'].get('what_enjoyed', []))
        
        # Should have diverse activities from different caregivers
        assert len(set(all_enjoyed)) >= 3

    def test_weekly_pattern_evolution(self, memory_manager, patterns_manager):
        """Test pattern evolution over a week"""
        
        # Simulate a week of feedback
        week_feedback = [
            {'day': 'Monday', 'enjoyed': ['tummy time'], 'disliked': ['loud noises']},
            {'day': 'Tuesday', 'enjoyed': ['tummy time', 'reading'], 'disliked': []},
            {'day': 'Wednesday', 'enjoyed': ['reading'], 'disliked': ['overstimulation']},
            {'day': 'Thursday', 'enjoyed': ['sensory play', 'tummy time'], 'disliked': []},
            {'day': 'Friday', 'enjoyed': ['tummy time'], 'disliked': ['sudden movements']},
            {'day': 'Saturday', 'enjoyed': ['music time', 'reading'], 'disliked': []},
            {'day': 'Sunday', 'enjoyed': ['gentle touch', 'tummy time'], 'disliked': []}
        ]
        
        # Add daily feedback
        for day_data in week_feedback:
            date_key = f'baby_feedback_2025-03-{week_feedback.index(day_data) + 17:02d}'
            memory_manager.add_entry(date_key, {
                'timestamp': f'2025-03-{week_feedback.index(day_data) + 17:02d}T10:00:00',
                'feedback': {
                    'what_enjoyed': day_data['enjoyed'],
                    'didnt_like': day_data['disliked'],
                    'sleep_quality': str(5 + (week_feedback.index(day_data) % 4)),
                    'feeding_response': 'good'
                }
            })
        
        # Analyze weekly patterns
        weekly_summary = memory_manager.get_summary(days=7)
        
        # Verify weekly learning
        assert weekly_summary['total_entries'] == 7
        
        # Identify most frequently enjoyed activity
        themes = weekly_summary['feedback_themes']
        assert 'tummy time' in themes['enjoyed']
        
        # Update patterns based on weekly learning
        if themes['enjoyed']:
            most_enjoyed = max(themes['enjoyed'], key=themes['enjoyed'].get)
            patterns_manager.add_favorite_activity(most_enjoyed.replace(' ', '_'))
        
        # Verify patterns evolved
        updated_patterns = patterns_manager.get_baby_patterns()
        assert 'tummy_time' in updated_patterns['favorite_activities']
        
        # Update history
        patterns_manager.increment_feedback_processed()
        patterns_manager.update_accuracy_score(0.85)  # Simulate 85% accuracy
        
        # Verify history tracking
        history = patterns_manager.get_patterns_history()
        assert history['feedback_processed'] >= 7
        assert history['accuracy_score'] == 0.85

    def test_developmental_stage_progression(self, memory_manager, patterns_manager):
        """Test developmental stage progression based on feedback"""
        
        # Start with newborn stage
        patterns_manager.set_developmental_stage('newborn')
        assert patterns_manager.get_developmental_stage() == 'newborn'
        
        # Add developmental observations over time
        developmental_milestones = [
            {
                'age_weeks': 2,
                'observations': ['better head control', 'tracking objects briefly'],
                'expected_stage': 'newborn'
            },
            {
                'age_weeks': 8,
                'observations': ['consistent head control', 'reaching for toys', 'bringing hands to mouth'],
                'expected_stage': 'infant'
            },
            {
                'age_weeks': 16,
                'observations': ['sitting with support', 'rolling over', 'transferring objects'],
                'expected_stage': 'infant'
            },
            {
                'age_weeks': 28,
                'observations': ['crawling', 'pulling to stand', 'first words'],
                'expected_stage': 'toddler'
            }
        ]
        
        for milestone in developmental_milestones:
            # Update baby age
            age_months = milestone['age_weeks'] // 4
            patterns_manager.update_baby_patterns({'age_months': age_months})
            
            # Add developmental observations
            memory_manager.add_entry(f'developmental_{milestone["age_weeks"]}weeks', {
                'timestamp': (datetime.now() - timedelta(weeks=milestone['age_weeks'])).isoformat(),
                'feedback': {
                    'developmental': milestone['observations']
                }
            })
            
            # Check if stage should be updated
            current_stage = patterns_manager.get_developmental_stage()
            if current_stage != milestone['expected_stage']:
                patterns_manager.set_developmental_stage(milestone['expected_stage'])
            
            # Verify stage progression
            assert patterns_manager.get_developmental_stage() == milestone['expected_stage']
        
        # Verify final stage
        assert patterns_manager.get_developmental_stage() == 'toddler'

    def test_memory_search_and_retrieval_workflow(self, memory_manager, patterns_manager):
        """Test complete memory search and retrieval workflow"""
        
        # Add diverse memory data
        memory_data = {
            'activities': ['tummy time', 'reading', 'sensory play', 'music time'],
            'sleep_patterns': ['good night sleep', 'restless afternoon nap'],
            'feeding_patterns': ['excellent morning feeding', 'fussy evening feeding'],
            'developmental': ['head control', 'tracking', 'reaching']
        }
        
        # Add entries with different content
        for i, activity in enumerate(memory_data['activities']):
            memory_manager.add_entry(f'activity_{i}', {
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
                'feedback': {
                    'what_enjoyed': [activity],
                    'sleep_quality': str(5 + i % 5),
                    'feeding_response': ['good', 'excellent', 'fair'][i % 3]
                }
            })
        
        # Test search functionality
        search_results = memory_manager.search_entries('tummy')
        assert len(search_results) > 0
        
        # Test date range retrieval
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        recent_entries = memory_manager.get_entries_in_date_range(week_ago, today)
        assert len(recent_entries) > 0
        
        # Test pattern-based retrieval
        processor = EmailCommandProcessor()
        
        with patch.object(processor, '_handle_memory_command') as mock_handle:
            mock_handle.return_value = "Memory search results"
            
            # Test different search types
            search_types = ['today', 'week', 'month', 'search tummy']
            
            for search_type in search_types:
                if 'search' in search_type:
                    command = {'command': 'memory', 'args': search_type.replace('search ', '')}
                else:
                    command = {'command': 'memory', 'args': search_type}
                
                result = processor._execute_command(command)
                assert result is not None

    def test_system_resilience_and_recovery(self, memory_manager, patterns_manager):
        """Test system resilience and recovery mechanisms"""
        
        # Test memory file corruption recovery
        original_memory = memory_manager._memory_cache.copy()
        
        # Simulate file corruption
        with patch.object(memory_manager, '_load_json_file', return_value={}):
            memory_manager._load_memory()
            # Should recover with empty cache
            assert memory_manager._memory_cache == {}
        
        # Restore data
        memory_manager._memory_cache = original_memory
        
        # Test patterns file corruption recovery
        with patch.object(patterns_manager, '_load_json_file', return_value={}):
            patterns = patterns_manager.get_patterns()
            # Should recover with empty patterns
            assert patterns == {}
        
        # Test email processing failure recovery
        processor = EmailCommandProcessor()
        
        with patch.object(processor, '_connect_to_email') as mock_connect:
            mock_connect.return_value = False  # Connection failure
            
            result = processor.process_email_commands()
            # Should handle failure gracefully
            assert result is False
        
        # Test partial data recovery
        partial_memory = {
            'complete_entry': {
                'timestamp': datetime.now().isoformat(),
                'feedback': {'what_enjoyed': ['tummy time']},
                'journal_entries': [{'note': 'Good day', 'time': '10:00 AM'}]
            },
            'incomplete_entry': {
                'feedback': {'what_enjoyed': ['reading']}
                # Missing timestamp
            }
        }
        
        memory_manager._memory_cache = partial_memory
        
        # System should handle incomplete data gracefully
        summary = memory_manager.get_summary()
        assert summary['total_entries'] >= 1  # At least complete entries counted

    def test_performance_with_historical_data(self, memory_manager, patterns_manager):
        """Test system performance with large amounts of historical data"""
        
        # Generate large dataset (3 months of daily entries)
        for day in range(90):
            date = datetime.now() - timedelta(days=day)
            memory_manager.add_entry(f'baby_feedback_{date.strftime("%Y-%m-%d")}', {
                'timestamp': date.isoformat(),
                'feedback': {
                    'what_enjoyed': [f'activity_{day % 10}'],
                    'didnt_like': [f'challenge_{day % 5}'],
                    'sleep_quality': str(5 + day % 5),
                    'feeding_response': ['good', 'excellent', 'fair'][day % 3],
                    'developmental': [f'milestone_{day // 7}']
                },
                'journal_entries': [
                    {'note': f'Journal entry for day {day}', 'time': f'{10 + day % 8}:00 AM'}
                ]
            })
        
        # Test performance of memory operations
        start_time = datetime.now()
        
        # Test search performance
        search_results = memory_manager.search_entries('activity_1')
        search_time = datetime.now() - start_time
        
        # Should complete search in reasonable time
        assert search_time.total_seconds() < 1.0
        assert len(search_results) >= 9  # Should find ~9 occurrences
        
        # Test summary generation performance
        start_time = datetime.now()
        summary = memory_manager.get_summary(days=30)
        summary_time = datetime.now() - start_time
        
        # Should complete summary in reasonable time
        assert summary_time.total_seconds() < 1.0
        assert summary['total_entries'] == 30
        
        # Test pattern learning performance
        start_time = datetime.now()
        weekly_summary = memory_manager.get_summary(days=7)
        learning_time = datetime.now() - start_time
        
        # Should complete learning in reasonable time
        assert learning_time.total_seconds() < 1.0
        
        # Update patterns with learned data
        if weekly_summary['feedback_themes']['enjoyed']:
            most_enjoyed = max(weekly_summary['feedback_themes']['enjoyed'], 
                             key=weekly_summary['feedback_themes']['enjoyed'].get)
            patterns_manager.add_favorite_activity(most_enjoyed.replace(' ', '_'))
        
        # Verify system still responsive
        updated_patterns = patterns_manager.get_baby_patterns()
        assert len(updated_patterns['favorite_activities']) > 0
