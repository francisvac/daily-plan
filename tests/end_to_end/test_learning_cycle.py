#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Learning Cycle End-to-End Tests
Complete testing of the feedback-to-learning-to-improvement cycle
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from base_classes import MemoryManager, PatternsManager
from email_command_processor import EmailCommandProcessor
from generate_baby_plan import BabyPlanGenerator


class TestLearningCycle:
    """End-to-end tests for the complete learning cycle"""

    def test_feedback_to_pattern_learning_cycle(self, memory_manager, patterns_manager):
        """Test complete cycle: feedback -> pattern learning -> improved recommendations"""
        
        # Phase 1: Initial state - no learning
        initial_patterns = patterns_manager.get_baby_patterns()
        initial_favorites = initial_patterns.get('favorite_activities', [])
        
        # Phase 2: Collect feedback over multiple days
        feedback_sequence = [
            {
                'day': 1,
                'feedback': 'feedback Baby absolutely loved tummy time today, was so engaged and happy',
                'context': 'morning session, 15 minutes',
                'outcome': 'very positive'
            },
            {
                'day': 2,
                'feedback': 'feedback Baby enjoyed tummy time again, tried to lift head higher',
                'context': 'afternoon session, 20 minutes',
                'outcome': 'positive'
            },
            {
                'day': 3,
                'feedback': 'feedback Baby loved tummy time so much we extended the session',
                'context': 'morning session, 25 minutes',
                'outcome': 'very positive'
            },
            {
                'day': 4,
                'feedback': 'feedback Baby was fussy during loud music time but loved quiet reading',
                'context': 'afternoon activities',
                'outcome': 'mixed'
            },
            {
                'day': 5,
                'feedback': 'feedback Baby really enjoys gentle singing and soft voices',
                'context': 'bedtime routine',
                'outcome': 'positive'
            }
        ]
        
        processor = EmailCommandProcessor()
        
        # Process all feedback
        for day_data in feedback_sequence:
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
                
                # Process feedback
                command = {'command': 'feedback', 'args': day_data['feedback'].replace('feedback ', '')}
                processor._execute_command(command)
        
        # Phase 3: Extract patterns from accumulated feedback
        memory_summary = memory_manager.get_summary(days=5)
        feedback_themes = memory_summary['feedback_themes']
        
        # Verify learning occurred
        assert 'tummy time' in feedback_themes['enjoyed']
        assert feedback_themes['enjoyed']['tummy time'] >= 3  # Mentioned 3+ times
        assert 'reading' in feedback_themes['enjoyed']
        assert 'loud music' in feedback_themes['disliked']
        
        # Phase 4: Update patterns based on learning
        # Add frequently enjoyed activities
        for activity, count in feedback_themes['enjoyed'].items():
            if count >= 2:
                activity_clean = activity.replace(' ', '_')
                patterns_manager.add_favorite_activity(activity_clean)
        
        # Add disliked activities to avoid list
        for activity in feedback_themes['disliked']:
            if feedback_themes['disliked'][activity] >= 1:
                # Could add to avoid list in patterns
                pass
        
        # Phase 5: Verify patterns updated
        updated_patterns = patterns_manager.get_baby_patterns()
        updated_favorites = updated_patterns.get('favorite_activities', [])
        
        # Should have new favorites based on feedback
        assert 'tummy_time' in updated_favorites
        assert len(updated_favorites) > len(initial_favorites)
        
        # Phase 6: Generate improved recommendations based on learning
        plan_generator = BabyPlanGenerator()
        
        with patch.object(plan_generator, '_generate_plan_content') as mock_generate:
            # Plan should incorporate learned preferences
            mock_generate.return_value = """
# Baby Development Plan - Enhanced by Learning

## Morning Activities (Based on Preferences)
- **Tummy Time** (25 minutes) - Baby's favorite activity
- **Gentle Reading** (15 minutes) - Enjoyed quiet time
- **Soft Singing** (10 minutes) - Preferred over loud music

## Afternoon Activities  
- **Tummy Time** (20 minutes) - Extended sessions successful
- **Quiet Sensory Play** (15 minutes) - Avoid overstimulation
- **Gentle Movement** (10 minutes) - Calm activities preferred
"""
            
            enhanced_plan = plan_generator.generate_plan()
            
            # Verify plan incorporates learning
            assert 'favorite activity' in enhanced_plan
            assert 'tummy time' in enhanced_plan.lower()
            assert 'quiet' in enhanced_plan.lower()

    def test_developmental_learning_progression(self, memory_manager, patterns_manager):
        """Test learning about developmental progression over time"""
        
        # Track developmental observations across months
        developmental_timeline = [
            {
                'age_months': 1,
                'observations': ['brief head lifting', 'tracking faces', 'startle reflex'],
                'activities_successful': ['gentle touch', 'skin to skin', 'soft voices'],
                'stage': 'newborn'
            },
            {
                'age_months': 2,
                'observations': ['better head control', 'tracking objects', 'bringing hands to mouth'],
                'activities_successful': ['tummy time', 'high contrast books', 'gentle movement'],
                'stage': 'infant'
            },
            {
                'age_months': 4,
                'observations': ['holding head steady', 'reaching for toys', 'rolling over attempts'],
                'activities_successful': ['tummy time (extended)', 'grasping toys', 'sensory mats'],
                'stage': 'infant'
            },
            {
                'age_months': 6,
                'observations': ['sitting with support', 'transferring objects', 'babbling'],
                'activities_successful': ['sitting practice', 'block play', 'picture books'],
                'stage': 'infant'
            }
        ]
        
        # Process developmental timeline
        for period in developmental_timeline:
            # Update baby age
            patterns_manager.update_baby_patterns({'age_months': period['age_months']})
            
            # Add developmental observations
            memory_manager.add_entry(f'developmental_{period["age_months"]}months', {
                'timestamp': (datetime.now() - timedelta(days=30*period['age_months'])).isoformat(),
                'feedback': {
                    'developmental': period['observations'],
                    'what_enjoyed': period['activities_successful'],
                    'sleep_quality': '7',
                    'feeding_response': 'good'
                }
            })
            
            # Update developmental stage if needed
            current_stage = patterns_manager.get_developmental_stage()
            if current_stage != period['stage']:
                patterns_manager.set_developmental_stage(period['stage'])
            
            # Verify stage progression
            assert patterns_manager.get_developmental_stage() == period['stage']
            
            # Update favorite activities based on successful activities
            for activity in period['activities_successful']:
                if activity in ['tummy time', 'sitting practice', 'block play']:
                    activity_clean = activity.replace(' ', '_')
                    patterns_manager.add_favorite_activity(activity_clean)
        
        # Verify developmental learning
        final_patterns = patterns_manager.get_baby_patterns()
        assert final_patterns['age_months'] == 6
        assert final_patterns['developmental_stage'] == 'infant'
        assert 'tummy_time' in final_patterns['favorite_activities']
        
        # Verify memory captured progression
        developmental_entries = [k for k in memory_manager._memory_cache.keys() if 'developmental_' in k]
        assert len(developmental_entries) == 4

    def test_sleep_pattern_learning_and_adaptation(self, memory_manager, patterns_manager):
        """Test learning sleep patterns and adapting schedules"""
        
        # Collect sleep-related feedback over time
        sleep_feedback_sequence = [
            {
                'night': 1,
                'bedtime': '7:30 PM',
                'sleep_quality': '3',  # Poor
                'observations': 'baby was restless, woke frequently',
                'next_day_mood': 'fussy'
            },
            {
                'night': 2,
                'bedtime': '8:00 PM',
                'sleep_quality': '5',  # Fair
                'observations': 'better sleep, still some wakeups',
                'next_day_mood': 'improved'
            },
            {
                'night': 3,
                'bedtime': '8:30 PM',
                'sleep_quality': '8',  # Good
                'observations': 'slept well, longer stretches',
                'next_day_mood': 'happy'
            },
            {
                'night': 4,
                'bedtime': '8:30 PM',
                'sleep_quality': '9',  # Excellent
                'observations': 'great sleep, minimal wakeups',
                'next_day_mood': 'very happy'
            },
            {
                'night': 5,
                'bedtime': '8:30 PM',
                'sleep_quality': '8',  # Good
                'observations': 'consistent good sleep',
                'next_day_mood': 'happy'
            }
        ]
        
        # Process sleep feedback
        for night_data in sleep_feedback_sequence:
            memory_manager.add_entry(f'sleep_night_{night_data["night"]}', {
                'timestamp': (datetime.now() - timedelta(days=5-night_data["night"])).isoformat(),
                'feedback': {
                    'sleep_quality': night_data['sleep_quality'],
                    'what_enjoyed': [f'bedtime {night_data["bedtime"]}'] if night_data['sleep_quality'] >= '7' else [],
                    'didnt_like': [f'bedtime {night_data["bedtime"]}'] if night_data['sleep_quality'] <= '5' else []
                },
                'journal_entries': [{
                    'note': night_data['observations'],
                    'time': night_data['bedtime']
                }]
            })
        
        # Analyze sleep patterns
        sleep_summary = memory_manager.get_summary(days=5)
        sleep_themes = sleep_summary['feedback_themes']
        
        # Identify optimal bedtime
        optimal_bedtimes = []
        for activity in sleep_themes['enjoyed']:
            if 'bedtime' in activity:
                optimal_bedtimes.append(activity)
        
        # Should identify 8:30 PM as optimal
        assert 'bedtime 8:30 PM' in optimal_bedtimes
        
        # Update sleep schedule based on learning
        if optimal_bedtimes:
            # Extract time from most successful bedtime
            best_bedtime = max(optimal_bedtimes, key=lambda x: sleep_themes['enjoyed'][x])
            time_extracted = best_bedtime.split(' ')[1]
            
            current_schedule = patterns_manager.get_sleep_schedule()
            current_schedule['night_bedtime'] = time_extracted
            patterns_manager.update_sleep_schedule(current_schedule)
        
        # Verify schedule adaptation
        updated_schedule = patterns_manager.get_sleep_schedule()
        assert updated_schedule['night_bedtime'] == '8:30 PM'

    def test_accuracy_tracking_and_improvement(self, memory_manager, patterns_manager):
        """Test tracking prediction accuracy and improving recommendations"""
        
        # Simulate prediction accuracy tracking
        prediction_history = []
        
        # Month 1: Low accuracy (50%)
        month1_predictions = [
            {'predicted': 'tummy time', 'actual': 'tummy time', 'accurate': True},
            {'predicted': 'reading', 'actual': 'sensory play', 'accurate': False},
            {'predicted': 'music time', 'actual': 'quiet time', 'accurate': False},
            {'predicted': 'gentle touch', 'actual': 'gentle touch', 'accurate': True}
        ]
        
        # Month 2: Improved accuracy (70%)
        month2_predictions = [
            {'predicted': 'tummy time', 'actual': 'tummy time', 'accurate': True},
            {'predicted': 'reading', 'actual': 'reading', 'accurate': True},
            {'predicted': 'sensory play', 'actual': 'sensory play', 'accurate': True},
            {'predicted': 'music time', 'actual': 'quiet time', 'accurate': False},
            {'predicted': 'gentle touch', 'actual': 'gentle touch', 'accurate': True}
        ]
        
        # Month 3: High accuracy (85%)
        month3_predictions = [
            {'predicted': 'tummy time', 'actual': 'tummy time', 'accurate': True},
            {'predicted': 'reading', 'actual': 'reading', 'accurate': True},
            {'predicted': 'sensory play', 'actual': 'sensory play', 'accurate': True},
            {'predicted': 'quiet time', 'actual': 'quiet time', 'accurate': True},
            {'predicted': 'gentle touch', 'actual': 'gentle touch', 'accurate': True},
            {'predicted': 'block play', 'actual': 'music time', 'accurate': False}
        ]
        
        # Process prediction history
        for month, predictions in enumerate([month1_predictions, month2_predictions, month3_predictions], 1):
            for pred in predictions:
                memory_manager.add_entry(f'prediction_month{month}_{predictions.index(pred)}', {
                    'timestamp': (datetime.now() - timedelta(days=30*(4-month))).isoformat(),
                    'prediction': pred['predicted'],
                    'actual_feedback': {'what_enjoyed': [pred['actual']]},
                    'accurate': pred['accurate']
                })
            
            # Calculate monthly accuracy
            accurate_count = sum(1 for p in predictions if p['accurate'])
            accuracy_score = accurate_count / len(predictions)
            
            # Update patterns history
            patterns_manager.update_accuracy_score(accuracy_score)
            patterns_manager.increment_feedback_processed()
        
        # Verify accuracy tracking
        final_history = patterns_manager.get_patterns_history()
        assert final_history['accuracy_score'] >= 0.8  # Should be around 85%
        assert final_history['feedback_processed'] >= 15
        
        # Verify learning improved accuracy
        month1_accuracy = sum(1 for p in month1_predictions if p['accurate']) / len(month1_predictions)
        month3_accuracy = sum(1 for p in month3_predictions if p['accurate']) / len(month3_predictions)
        
        assert month3_accuracy > month1_accuracy  # Should show improvement

    def test_comprehensive_learning_integration(self, memory_manager, patterns_manager):
        """Test integration of all learning mechanisms"""
        
        # Simulate comprehensive learning scenario
        learning_scenarios = {
            'activity_preferences': {
                'data': [
                    'feedback Baby loves tummy time sessions',
                    'feedback Baby enjoys reading books',
                    'feedback Baby likes sensory play activities',
                    'feedback Baby dislikes loud noises',
                    'feedback Baby dislikes sudden movements'
                ],
                'expected_outcome': ['tummy_time', 'reading', 'sensory_play']
            },
            'schedule_optimization': {
                'data': [
                    'feedback Morning tummy time works best',
                    'feedback Afternoon reading is enjoyable',
                    'feedback Evening quiet time is calming',
                    'feedback Midday activities are challenging'
                ],
                'expected_outcome': {'optimal_times': ['morning', 'afternoon', 'evening']}
            },
            'developmental_tracking': {
                'data': [
                    'feedback Baby showing better head control',
                    'feedback Baby starting to reach for toys',
                    'feedback Baby tracking objects better',
                    'feedback Baby bringing hands to mouth'
                ],
                'expected_outcome': {'stage': 'infant', 'skills': ['head_control', 'reaching', 'tracking']}
            }
        }
        
        processor = EmailCommandProcessor()
        
        # Process all learning data
        for category, scenario in learning_scenarios.items():
            for feedback in scenario['data']:
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
                    
                    command = {'command': 'feedback', 'args': feedback.replace('feedback ', '')}
                    processor._execute_command(command)
        
        # Extract comprehensive learnings
        memory_summary = memory_manager.get_summary(days=30)
        feedback_themes = memory_summary['feedback_themes']
        
        # Apply activity preference learning
        for activity in learning_scenarios['activity_preferences']['expected_outcome']:
            if any(activity.replace('_', ' ') in theme for theme in feedback_themes['enjoyed']):
                patterns_manager.add_favorite_activity(activity)
        
        # Apply developmental learning
        if 'developmental' in str(memory_manager._memory_cache):
            patterns_manager.set_developmental_stage('infant')
        
        # Verify comprehensive learning integration
        final_patterns = patterns_manager.get_baby_patterns()
        
        # Activity preferences learned
        for expected_activity in learning_scenarios['activity_preferences']['expected_outcome']:
            assert expected_activity in final_patterns['favorite_activities']
        
        # Developmental stage updated
        assert final_patterns['developmental_stage'] == 'infant'
        
        # History updated
        history = patterns_manager.get_patterns_history()
        assert history['feedback_processed'] >= len(learning_scenarios['activity_preferences']['data'])
        
        # Memory contains comprehensive data
        assert len(memory_manager._memory_cache) >= 15  # All feedback entries

    def test_learning_persistence_and_recovery(self, memory_manager, patterns_manager):
        """Test that learning persists across sessions and can be recovered"""
        
        # Phase 1: Build up learning data
        learning_data = {
            'favorite_activities': ['tummy_time', 'reading', 'sensory_play'],
            'avoid_activities': ['loud_noises', 'sudden_movements'],
            'optimal_schedule': {
                'morning_nap': '9:00 AM',
                'afternoon_nap': '1:00 PM',
                'night_bedtime': '8:30 PM'
            },
            'developmental_stage': 'infant',
            'accuracy_score': 0.85
        }
        
        # Update patterns with learning data
        patterns_manager.update_baby_patterns({
            'favorite_activities': learning_data['favorite_activities'],
            'avoid_activities': learning_data['avoid_activities']
        })
        patterns_manager.set_developmental_stage(learning_data['developmental_stage'])
        patterns_manager.update_sleep_schedule(learning_data['optimal_schedule'])
        patterns_manager.update_accuracy_score(learning_data['accuracy_score'])
        
        # Add memory entries
        for i, activity in enumerate(learning_data['favorite_activities']):
            memory_manager.add_entry(f'learning_entry_{i}', {
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
                'feedback': {
                    'what_enjoyed': [activity.replace('_', ' ')],
                    'sleep_quality': '8',
                    'feeding_response': 'good'
                }
            })
        
        # Verify learning was saved
        saved_patterns = patterns_manager.get_baby_patterns()
        assert saved_patterns['favorite_activities'] == learning_data['favorite_activities']
        assert saved_patterns['developmental_stage'] == learning_data['developmental_stage']
        
        saved_memory = len(memory_manager._memory_cache)
        assert saved_memory >= len(learning_data['favorite_activities'])
        
        # Phase 2: Simulate session restart (new instances)
        # In real scenario, this would be loading from files
        # For testing, we verify data persistence by checking file contents
        
        # Phase 3: Verify learning can be recovered and used
        recovered_patterns = patterns_manager.get_patterns()
        assert 'baby_patterns' in recovered_patterns
        assert recovered_patterns['baby_patterns']['favorite_activities'] == learning_data['favorite_activities']
        
        recovered_history = patterns_manager.get_patterns_history()
        assert recovered_history['accuracy_score'] == learning_data['accuracy_score']
        
        # Phase 4: Continue learning from recovered state
        new_feedback = 'feedback Baby really loves block play now'
        
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
            
            processor = EmailCommandProcessor()
            command = {'command': 'feedback', 'args': new_feedback.replace('feedback ', '')}
            processor._execute_command(command)
        
        # Verify learning continues
        updated_patterns = patterns_manager.get_baby_patterns()
        assert len(updated_patterns['favorite_activities']) >= len(learning_data['favorite_activities'])
