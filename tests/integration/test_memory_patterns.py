#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Memory & Patterns Integration Tests
Integration testing of memory storage with pattern learning and adaptation
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from base_classes import MemoryManager, PatternsManager


class TestMemoryPatternsIntegration:
    """Integration tests for memory and patterns system interaction"""

    def test_memory_feedback_influences_patterns(self, memory_manager, patterns_manager):
        """Test that memory feedback influences pattern learning"""
        
        # Add multiple feedback entries about tummy time
        feedback_entries = [
            ('baby_feedback_2025-03-20', {
                'timestamp': '2025-03-20T10:00:00',
                'feedback': {
                    'what_enjoyed': ['tummy time', 'sensory play'],
                    'didnt_like': [],
                    'sleep_quality': '8',
                    'feeding_response': 'good'
                }
            }),
            ('baby_feedback_2025-03-21', {
                'timestamp': '2025-03-21T10:00:00',
                'feedback': {
                    'what_enjoyed': ['tummy time', 'reading'],
                    'didnt_like': ['loud noises'],
                    'sleep_quality': '7',
                    'feeding_response': 'good'
                }
            }),
            ('baby_feedback_2025-03-22', {
                'timestamp': '2025-03-22T10:00:00',
                'feedback': {
                    'what_enjoyed': ['tummy time'],
                    'didnt_like': ['overstimulation'],
                    'sleep_quality': '9',
                    'feeding_response': 'excellent'
                }
            })
        ]
        
        # Add feedback to memory
        for key, entry in feedback_entries:
            memory_manager.add_entry(key, entry)
        
        # Simulate pattern learning from memory
        learned_patterns = self._extract_patterns_from_memory(memory_manager)
        
        # Verify tummy time is identified as preferred activity
        assert 'tummy time' in learned_patterns['enjoyed_activities']
        assert learned_patterns['enjoyed_activities']['tummy time'] >= 3
        
        # Verify disliked activities are tracked
        assert 'loud noises' in learned_patterns['disliked_activities']
        assert 'overstimulation' in learned_patterns['disliked_activities']
        
        # Update patterns manager with learned preferences
        for activity in learned_patterns['enjoyed_activities']:
            if learned_patterns['enjoyed_activities'][activity] >= 2:
                patterns_manager.add_favorite_activity(activity.replace(' ', '_'))
        
        # Verify patterns were updated
        updated_patterns = patterns_manager.get_baby_patterns()
        assert 'tummy_time' in updated_patterns['favorite_activities']

    def test_sleep_pattern_learning_from_memory(self, memory_manager, patterns_manager):
        """Test learning sleep patterns from memory data"""
        
        # Add feedback with varying sleep quality
        sleep_feedback = [
            ('baby_feedback_2025-03-20_night', {
                'timestamp': '2025-03-20T22:00:00',
                'feedback': {
                    'sleep_quality': '3',  # Poor sleep
                    'didnt_like': ['restless night']
                }
            }),
            ('baby_feedback_2025-03-21_night', {
                'timestamp': '2025-03-21T22:00:00',
                'feedback': {
                    'sleep_quality': '8',  # Good sleep
                    'what_enjoyed': ['peaceful night']
                }
            }),
            ('baby_feedback_2025-03-22_night', {
                'timestamp': '2025-03-22T22:00:00',
                'feedback': {
                    'sleep_quality': '9',  # Excellent sleep
                    'what_enjoyed': ['deep sleep', 'calm evening']
                }
            })
        ]
        
        for key, entry in sleep_feedback:
            memory_manager.add_entry(key, entry)
        
        # Analyze sleep patterns
        sleep_analysis = self._analyze_sleep_patterns(memory_manager)
        
        # Verify sleep quality tracking
        assert sleep_analysis['average_sleep_quality'] >= 6.5
        assert sleep_analysis['sleep_trend'] == 'improving'
        
        # Update patterns with sleep insights
        if sleep_analysis['sleep_trend'] == 'improving':
            current_schedule = patterns_manager.get_sleep_schedule()
            # Could adjust schedule based on patterns
            patterns_manager.update_sleep_schedule(current_schedule)

    def test_developmental_milestone_tracking(self, memory_manager, patterns_manager):
        """Test tracking developmental milestones from memory"""
        
        # Add developmental observations over time
        developmental_entries = [
            ('baby_feedback_2025-03-15', {
                'timestamp': '2025-03-15T10:00:00',
                'feedback': {
                    'developmental': ['better head control', 'tracking objects']
                }
            }),
            ('baby_feedback_2025-03-20', {
                'timestamp': '2025-03-20T10:00:00',
                'feedback': {
                    'developmental': ['reaching for toys', 'more alert']
                }
            }),
            ('baby_feedback_2025-03-25', {
                'timestamp': '2025-03-25T10:00:00',
                'feedback': {
                    'developmental': ['rolling over attempt', 'stronger grip']
                }
            })
        ]
        
        for key, entry in developmental_entries:
            memory_manager.add_entry(key, entry)
        
        # Extract developmental progression
        developmental_progression = self._track_developmental_progress(memory_manager)
        
        # Verify milestone tracking
        assert 'head control' in developmental_progression['achieved_skills']
        assert 'tracking objects' in developmental_progression['achieved_skills']
        assert 'reaching for toys' in developmental_progression['achieved_skills']
        assert 'rolling over' in developmental_progression['emerging_skills']
        
        # Update developmental stage if needed
        if len(developmental_progression['achieved_skills']) >= 5:
            patterns_manager.set_developmental_stage('infant')

    def test_feeding_pattern_integration(self, memory_manager, patterns_manager):
        """Test feeding pattern integration between memory and patterns"""
        
        # Add feeding-related feedback
        feeding_feedback = [
            ('baby_feedback_2025-03-20_morning', {
                'timestamp': '2025-03-20T07:00:00',
                'feedback': {
                    'feeding_response': 'good',
                    'what_enjoyed': ['morning feeding']
                }
            }),
            ('baby_feedback_2025-03-20_afternoon', {
                'timestamp': '2025-03-20T15:00:00',
                'feedback': {
                    'feeding_response': 'fussy',
                    'didnt_like': ['afternoon feeding']
                }
            }),
            ('baby_feedback_2025-03-21_morning', {
                'timestamp': '2025-03-21T07:00:00',
                'feedback': {
                    'feeding_response': 'excellent',
                    'what_enjoyed': ['morning feeding']
                }
            })
        ]
        
        for key, entry in feeding_feedback:
            memory_manager.add_entry(key, entry)
        
        # Analyze feeding patterns
        feeding_analysis = self._analyze_feeding_patterns(memory_manager)
        
        # Verify feeding preference detection
        assert feeding_analysis['preferred_feeding_times'] == ['morning']
        assert feeding_analysis['challenging_feeding_times'] == ['afternoon']
        
        # Update feeding schedule based on patterns
        current_schedule = patterns_manager.get_feeding_schedule()
        if 'afternoon' in feeding_analysis['challenging_feeding_times']:
            # Could adjust afternoon feeding time
            adjusted_schedule = current_schedule.copy()
            adjusted_schedule['afternoon'] = '3:30 PM'  # Example adjustment
            patterns_manager.update_feeding_schedule(adjusted_schedule)

    def test_memory_summary_informs_pattern_updates(self, memory_manager, patterns_manager):
        """Test that memory summaries inform pattern updates"""
        
        # Create comprehensive memory data
        today = datetime.now()
        for i in range(7):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            memory_manager.add_entry(f'baby_feedback_{date}', {
                'timestamp': (today - timedelta(days=i)).isoformat(),
                'feedback': {
                    'what_enjoyed': [f'activity_{i}'],
                    'didnt_like': [f'challenge_{i}'],
                    'sleep_quality': str(5 + i % 5),
                    'feeding_response': ['poor', 'fair', 'good', 'excellent'][i % 4]
                }
            })
        
        # Get memory summary
        summary = memory_manager.get_summary(days=7)
        
        # Verify summary contains pattern-relevant data
        assert summary['total_entries'] == 7
        assert 'feedback_themes' in summary
        
        # Use summary to update patterns
        themes = summary['feedback_themes']
        
        # Update favorite activities based on frequently enjoyed items
        if themes['enjoyed']:
            most_enjoyed = max(themes['enjoyed'], key=themes['enjoyed'].get)
            patterns_manager.add_favorite_activity(most_enjoyed)
        
        # Update disliked activities
        if themes['disliked']:
            most_disliked = max(themes['disliked'], key=themes['disliked'].get)
            # Could add to avoid list in patterns
        
        # Verify patterns were updated
        updated_patterns = patterns_manager.get_baby_patterns()
        assert len(updated_patterns['favorite_activities']) > 0

    def test_cross_reference_memory_with_patterns(self, memory_manager, patterns_manager):
        """Test cross-referencing memory data with existing patterns"""
        
        # Set up existing patterns
        existing_patterns = {
            'favorite_activities': ['tummy_time', 'reading'],
            'avoid_activities': ['loud_noises']
        }
        patterns_manager.update_baby_patterns(existing_patterns)
        
        # Add memory data that confirms and contradicts patterns
        memory_data = {
            'confirmation_feedback': {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': ['tummy time', 'reading'],  # Confirms patterns
                    'didnt_like': ['loud noises']  # Confirms patterns
                }
            },
            'contradiction_feedback': {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': ['loud noises'],  # Contradicts patterns
                    'didnt_like': ['tummy time']  # Contradicts patterns
                }
            }
        }
        
        for key, entry in memory_data.items():
            memory_manager.add_entry(key, entry)
        
        # Cross-reference and validate patterns
        validation_results = self._validate_patterns_against_memory(memory_manager, patterns_manager)
        
        # Verify validation results
        assert validation_results['confirmed_patterns'] > 0
        assert validation_results['contradicted_patterns'] > 0
        
        # Update patterns based on contradictions
        if validation_results['contradicted_patterns'] > 0:
            # Could adjust patterns or flag for review
            current_patterns = patterns_manager.get_baby_patterns()
            # Example: Add contradictory activities for monitoring
            patterns_manager.update_baby_patterns({
                'contradictory_activities': validation_results['contradictions']
            })

    def test_memory_cleanup_preserves_patterns(self, memory_manager, patterns_manager):
        """Test that memory cleanup doesn't lose important pattern data"""
        
        # Add old and recent memory data
        old_date = datetime.now() - timedelta(days=100)
        recent_date = datetime.now() - timedelta(days=5)
        
        memory_manager.add_entry('old_entry', {
            'timestamp': old_date.isoformat(),
            'feedback': {'what_enjoyed': ['old_activity']},
            'patterns_data': {'important_insight': 'should_be_preserved'}
        })
        
        memory_manager.add_entry('recent_entry', {
            'timestamp': recent_date.isoformat(),
            'feedback': {'what_enjoyed': ['recent_activity']},
            'patterns_data': {'current_insight': 'active'}
        })
        
        # Extract patterns before cleanup
        patterns_before = self._extract_patterns_from_memory(memory_manager)
        
        # Perform cleanup
        memory_manager.cleanup_old_entries(days_to_keep=30)
        
        # Verify old entries are removed but patterns are preserved
        assert 'old_entry' not in memory_manager._memory_cache
        assert 'recent_entry' in memory_manager._memory_cache
        
        # Extract patterns after cleanup
        patterns_after = self._extract_patterns_from_memory(memory_manager)
        
        # Important pattern insights should be preserved in patterns manager
        current_patterns = patterns_manager.get_patterns()
        assert 'patterns' in current_patterns

    def test_pattern_accuracy_tracking(self, memory_manager, patterns_manager):
        """Test tracking pattern accuracy over time"""
        
        # Simulate pattern predictions and actual outcomes
        prediction_outcomes = [
            {
                'date': '2025-03-20',
                'predicted_favorite': 'tummy time',
                'actual_feedback': {'what_enjoyed': ['tummy time']},
                'accurate': True
            },
            {
                'date': '2025-03-21',
                'predicted_favorite': 'reading',
                'actual_feedback': {'what_enjoyed': ['sensory play']},
                'accurate': False
            },
            {
                'date': '2025-03-22',
                'predicted_favorite': 'sensory play',
                'actual_feedback': {'what_enjoyed': ['sensory play']},
                'accurate': True
            }
        ]
        
        for outcome in prediction_outcomes:
            memory_manager.add_entry(f'prediction_{outcome["date"]}', {
                'timestamp': f'{outcome["date"]}T10:00:00',
                'prediction': outcome['predicted_favorite'],
                'actual_feedback': outcome['actual_feedback'],
                'accurate': outcome['accurate']
            })
        
        # Calculate accuracy
        accuracy_data = self._calculate_pattern_accuracy(memory_manager)
        
        # Verify accuracy calculation
        assert accuracy_data['total_predictions'] == 3
        assert accuracy_data['accurate_predictions'] == 2
        assert accuracy_data['accuracy_score'] == 2/3
        
        # Update patterns history with accuracy
        patterns_manager.update_accuracy_score(accuracy_data['accuracy_score'])
        
        # Verify accuracy was recorded
        history = patterns_manager.get_patterns_history()
        assert history['accuracy_score'] == 2/3

    def test_memory_patterns_synchronization(self, memory_manager, patterns_manager):
        """Test synchronization between memory and patterns systems"""
        
        # Add comprehensive memory data
        memory_data = {
            'activities': ['tummy time', 'reading', 'sensory play'],
            'schedule': {'optimal_times': ['morning', 'afternoon']},
            'development': ['head control', 'tracking'],
            'preferences': {'quiet_environment': True, 'gentle_touch': True}
        }
        
        memory_manager.add_entry('comprehensive_data', {
            'timestamp': datetime.now().isoformat(),
            'extracted_patterns': memory_data
        })
        
        # Synchronize memory patterns with patterns manager
        sync_result = self._synchronize_memory_to_patterns(memory_manager, patterns_manager)
        
        # Verify synchronization
        assert sync_result['activities_synced'] > 0
        assert sync_result['preferences_synced'] > 0
        
        # Verify patterns manager was updated
        updated_patterns = patterns_manager.get_baby_patterns()
        assert len(updated_patterns['favorite_activities']) > 0
        
        # Verify memory references patterns
        memory_summary = memory_manager.get_summary()
        assert memory_summary['total_entries'] > 0

    # Helper methods for integration testing
    
    def _extract_patterns_from_memory(self, memory_manager):
        """Extract patterns from memory data"""
        patterns = {
            'enjoyed_activities': {},
            'disliked_activities': {},
            'sleep_trends': [],
            'feeding_patterns': {}
        }
        
        for key, entry in memory_manager._memory_cache.items():
            if 'feedback' in entry:
                feedback = entry['feedback']
                
                # Count enjoyed activities
                for activity in feedback.get('what_enjoyed', []):
                    patterns['enjoyed_activities'][activity] = patterns['enjoyed_activities'].get(activity, 0) + 1
                
                # Count disliked activities
                for activity in feedback.get('didnt_like', []):
                    patterns['disliked_activities'][activity] = patterns['disliked_activities'].get(activity, 0) + 1
                
                # Track sleep quality
                if 'sleep_quality' in feedback:
                    patterns['sleep_trends'].append(int(feedback['sleep_quality']))
        
        return patterns
    
    def _analyze_sleep_patterns(self, memory_manager):
        """Analyze sleep patterns from memory"""
        sleep_qualities = []
        
        for key, entry in memory_manager._memory_cache.items():
            if 'feedback' in entry and 'sleep_quality' in entry['feedback']:
                sleep_qualities.append(int(entry['feedback']['sleep_quality']))
        
        if not sleep_qualities:
            return {'average_sleep_quality': 0, 'sleep_trend': 'unknown'}
        
        avg_quality = sum(sleep_qualities) / len(sleep_qualities)
        
        # Simple trend analysis
        if len(sleep_qualities) >= 2:
            recent_avg = sum(sleep_qualities[-3:]) / min(3, len(sleep_qualities))
            earlier_avg = sum(sleep_qualities[:-3]) / max(1, len(sleep_qualities) - 3)
            trend = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'average_sleep_quality': avg_quality,
            'sleep_trend': trend,
            'data_points': len(sleep_qualities)
        }
    
    def _track_developmental_progress(self, memory_manager):
        """Track developmental progress from memory"""
        achieved_skills = set()
        emerging_skills = set()
        
        for key, entry in memory_manager._memory_cache.items():
            if 'feedback' in entry and 'developmental' in entry['feedback']:
                for skill in entry['feedback']['developmental']:
                    # Simple classification based on skill description
                    if any(word in skill.lower() for word in ['better', 'stronger', 'improved']):
                        achieved_skills.add(skill)
                    else:
                        emerging_skills.add(skill)
        
        return {
            'achieved_skills': list(achieved_skills),
            'emerging_skills': list(emerging_skills),
            'total_observations': len(achieved_skills) + len(emerging_skills)
        }
    
    def _analyze_feeding_patterns(self, memory_manager):
        """Analyze feeding patterns from memory"""
        feeding_responses = {}
        
        for key, entry in memory_manager._memory_cache.items():
            if 'feedback' in entry and 'feeding_response' in entry['feedback']:
                # Extract time of day from key or timestamp
                time_of_day = self._extract_time_of_day(key, entry.get('timestamp'))
                response = entry['feedback']['feeding_response']
                
                if time_of_day not in feeding_responses:
                    feeding_responses[time_of_day] = []
                feeding_responses[time_of_day].append(response)
        
        # Analyze preferences
        preferred_times = []
        challenging_times = []
        
        for time, responses in feeding_responses.items():
            positive_responses = sum(1 for r in responses if r in ['good', 'excellent'])
            negative_responses = sum(1 for r in responses if r in ['poor', 'fussy'])
            
            if positive_responses > negative_responses:
                preferred_times.append(time)
            elif negative_responses > positive_responses:
                challenging_times.append(time)
        
        return {
            'preferred_feeding_times': preferred_times,
            'challenging_feeding_times': challenging_times,
            'feeding_data_points': len(feeding_responses)
        }
    
    def _extract_time_of_day(self, key, timestamp):
        """Extract time of day from key or timestamp"""
        # Simple extraction based on key patterns
        if 'morning' in key.lower():
            return 'morning'
        elif 'afternoon' in key.lower():
            return 'afternoon'
        elif 'evening' in key.lower():
            return 'evening'
        elif 'night' in key.lower():
            return 'night'
        else:
            # Extract from timestamp
            if timestamp:
                hour = datetime.fromisoformat(timestamp).hour
                if 6 <= hour < 12:
                    return 'morning'
                elif 12 <= hour < 18:
                    return 'afternoon'
                elif 18 <= hour < 22:
                    return 'evening'
                else:
                    return 'night'
        return 'unknown'
    
    def _validate_patterns_against_memory(self, memory_manager, patterns_manager):
        """Validate existing patterns against memory data"""
        current_patterns = patterns_manager.get_baby_patterns()
        memory_patterns = self._extract_patterns_from_memory(memory_manager)
        
        confirmed = 0
        contradicted = 0
        contradictions = []
        
        # Check favorite activities
        for activity in current_patterns.get('favorite_activities', []):
            activity_clean = activity.replace('_', ' ')
            if activity_clean in memory_patterns['enjoyed_activities']:
                confirmed += 1
            elif activity_clean in memory_patterns['disliked_activities']:
                contradicted += 1
                contradictions.append(activity)
        
        return {
            'confirmed_patterns': confirmed,
            'contradicted_patterns': contradicted,
            'contradictions': contradictions,
            'total_checked': len(current_patterns.get('favorite_activities', []))
        }
    
    def _calculate_pattern_accuracy(self, memory_manager):
        """Calculate pattern prediction accuracy"""
        predictions = []
        accurate = 0
        
        for key, entry in memory_manager._memory_cache.items():
            if 'prediction' in entry and 'actual_feedback' in entry:
                predictions.append(entry)
                if entry.get('accurate', False):
                    accurate += 1
        
        return {
            'total_predictions': len(predictions),
            'accurate_predictions': accurate,
            'accuracy_score': accurate / len(predictions) if predictions else 0
        }
    
    def _synchronize_memory_to_patterns(self, memory_manager, patterns_manager):
        """Synchronize memory data with patterns manager"""
        memory_patterns = self._extract_patterns_from_memory(memory_manager)
        sync_count = {'activities_synced': 0, 'preferences_synced': 0}
        
        # Sync enjoyed activities
        for activity, count in memory_patterns['enjoyed_activities'].items():
            if count >= 2:  # Only sync frequently mentioned activities
                activity_clean = activity.replace(' ', '_')
                if patterns_manager.add_favorite_activity(activity_clean):
                    sync_count['activities_synced'] += 1
        
        # Sync other preferences based on memory analysis
        if memory_patterns['sleep_trends']:
            avg_sleep = sum(memory_patterns['sleep_trends']) / len(memory_patterns['sleep_trends'])
            # Could update sleep patterns based on this
            sync_count['preferences_synced'] += 1
        
        return sync_count
