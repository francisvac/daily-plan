#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - LLM Template Generator
Uses LLM to generate dynamic daily plan templates based on feedback and patterns
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import (
    DEVELOPMENT_STAGES, FEEDBACK_KEYWORDS, JOURNAL_KEYWORDS,
    TEMPLATE_PLACEHOLDERS, ConfigManager
)
from base_classes import BabyPlannerBase, memory_manager, patterns_manager
from logger import get_logger, log_error, log_success, log_warning

class LLMTemplateGenerator(BabyPlannerBase):
    """Generates dynamic plan templates using LLM based on feedback and patterns"""
    
    def __init__(self):
        super().__init__("llm_template_generator")
        self.template_cache = {}
        self.cache_expiry_hours = 6
    
    def generate_daily_template(self, target_date: datetime.date, 
                               age_months: int, 
                               developmental_stage: str) -> Dict[str, Any]:
        """Generate a dynamic daily template using LLM"""
        
        # Check cache first
        cache_key = f"{target_date}_{age_months}_{developmental_stage}"
        if self._is_cache_valid(cache_key):
            self.logger.info(f"Using cached template for {target_date}")
            return self.template_cache[cache_key]['template']
        
        # Get context data
        context = self._build_template_context(target_date, age_months, developmental_stage)
        
        # Generate template using LLM
        template = self._generate_template_with_llm(context)
        
        # Cache the result
        self.template_cache[cache_key] = {
            'template': template,
            'timestamp': datetime.now()
        }
        
        log_success(self.component_name, f"Generated dynamic template for {target_date}")
        return template
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached template is still valid"""
        if cache_key not in self.template_cache:
            return False
        
        cached_time = self.template_cache[cache_key]['timestamp']
        expiry_time = cached_time + timedelta(hours=self.cache_expiry_hours)
        
        return datetime.now() < expiry_time
    
    def _build_template_context(self, target_date: datetime.date, 
                               age_months: int, 
                               developmental_stage: str) -> Dict[str, Any]:
        """Build comprehensive context for LLM template generation"""
        
        # Get recent feedback and patterns
        recent_memory = memory_manager.get_summary(7)
        yesterday_feedback = self._get_yesterday_feedback(target_date)
        
        # Get current patterns
        patterns = patterns_manager.get_baby_patterns()
        
        # Build context
        context = {
            "baby_info": {
                "age_months": age_months,
                "developmental_stage": developmental_stage,
                "birth_date": patterns.get("birth_date", "2025-03-17"),
                "days_old": self._calculate_days_old(target_date, patterns)
            },
            "current_patterns": {
                "favorite_activities": patterns.get("favorite_activities", []),
                "sleep_schedule": patterns.get("sleep_schedule", {}),
                "feeding_schedule": patterns.get("feeding_schedule", {}),
                "comfort_patterns": patterns.get("comfort_patterns", {})
            },
            "recent_feedback": {
                "most_enjoyed": recent_memory.get("most_enjoyed", []),
                "most_disliked": recent_memory.get("most_disliked", []),
                "avg_sleep": recent_memory.get("avg_sleep", 0),
                "feeding_patterns": recent_memory.get("feeding_patterns", []),
                "developmental_notes": recent_memory.get("developmental_notes", [])
            },
            "yesterday_insights": yesterday_feedback or {},
            "day_info": {
                "date": target_date.strftime('%Y-%m-%d'),
                "day_of_week": target_date.strftime('%A'),
                "season": self._get_season(target_date)
            },
            "developmental_focus": DEVELOPMENT_STAGES.get(developmental_stage, {}).get("focus", [])
        }
        
        return context
    
    def _calculate_days_old(self, target_date: datetime.date, patterns: Dict[str, Any]) -> int:
        """Calculate baby's age in days"""
        birth_date_str = patterns.get("birth_date")
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                return (target_date - birth_date).days
            except ValueError:
                pass
        return 0
    
    def _get_season(self, target_date: datetime.date) -> str:
        """Get season for context"""
        month = target_date.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"
    
    def _get_yesterday_feedback(self, target_date: datetime.date) -> Optional[Dict[str, Any]]:
        """Get yesterday's feedback for context"""
        yesterday = target_date - timedelta(days=1)
        key = f'baby_feedback_{yesterday.strftime("%Y-%m-%d")}'
        
        entry = memory_manager.get_entry(key)
        if entry:
            return {
                "enjoyed": entry.get("feedback", {}).get("what_enjoyed", []),
                "disliked": entry.get("feedback", {}).get("didnt_like", []),
                "sleep_quality": entry.get("feedback", {}).get("sleep_quality", 5),
                "feeding_response": entry.get("feedback", {}).get("feeding_response", ""),
                "journal_entries": entry.get("journal_entries", [])
            }
        return None
    
    def _generate_template_with_llm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate template using LLM"""
        
        prompt = self._build_llm_prompt(context)
        
        try:
            # Try ZeroClaw first
            result = subprocess.run([
                'zeroclaw', 'agent', '-m', prompt,
                '--output-json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                template_data = json.loads(result.stdout)
                return self._validate_and_format_template(template_data, context)
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            log_warning(self.component_name, f"LLM generation failed: {e}")
        
        # Fallback to rule-based generation
        return self._generate_fallback_template(context)
    
    def _build_llm_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for LLM"""
        
        baby_info = context["baby_info"]
        patterns = context["current_patterns"]
        feedback = context["recent_feedback"]
        day_info = context["day_info"]
        
        prompt = f"""Generate a personalized baby daily plan template for {day_info['date']} ({day_info['day_of_week']}).

Baby Information:
- Age: {baby_info['age_months']} months ({baby_info['days_old']} days old)
- Developmental Stage: {baby_info['developmental_stage']}
- Focus Areas: {', '.join(context['developmental_focus'])}

Current Patterns:
- Favorite Activities: {', '.join(patterns['favorite_activities'])}
- Sleep Schedule: {patterns['sleep_schedule']}
- Feeding Schedule: {patterns['feeding_schedule']}

Recent Feedback (Last 7 Days):
- Most Enjoyed: {', '.join(feedback['most_enjoyed'])}
- Disliked Activities: {', '.join(feedback['most_disliked'])}
- Average Sleep Quality: {feedback['avg_sleep']:.1f}/10
- Feeding Patterns: {', '.join(feedback['feeding_patterns'])}

Yesterday's Insights:
{self._format_yesterday_insights(context['yesterday_insights'])}

Generate a dynamic daily plan template with this JSON structure:
{{
  "template_sections": {{
    "morning_routine": {{
      "title": "Morning Routine (6 AM - 12 PM)",
      "activities": [
        {{
          "name": "activity_name",
          "description": "Age-appropriate description",
          "focus_area": "bonding/development/comfort",
          "duration": "estimated_duration",
          "tips": ["tip1", "tip2"],
          "adaptations": ["if baby is fussy", "if baby is alert"]
        }}
      ]
    }},
    "afternoon_routine": {{
      "title": "Afternoon Routine (12 PM - 6 PM)",
      "activities": [...]
    }},
    "evening_routine": {{
      "title": "Evening Routine (6 PM - 10 PM)",
      "activities": [...]
    }}
  }},
  "schedule_adjustments": {{
    "feeding_times": {{
      "morning": "time_and_notes",
      "midday": "time_and_notes",
      "afternoon": "time_and_notes",
      "evening": "time_and_notes",
      "night": "time_and_notes"
    }},
    "sleep_times": {{
      "morning_nap": "time_and_duration",
      "afternoon_nap": "time_and_duration",
      "evening_nap": "time_and_duration",
      "night_sleep": "bedtime_and_routine"
    }}
  }},
  "focus_areas": ["primary_focus", "secondary_focus"],
  "developmental_targets": ["target1", "target2"],
  "parenting_tips": ["tip1", "tip2", "tip3"],
  "adaptation_notes": "How to adapt based on baby's mood and responses"
}}

Important Guidelines:
1. Activities must be age-appropriate for {baby_info['age_months']} months old
2. Incorporate feedback from recent days (continue enjoyed activities, avoid disliked ones)
3. Focus on {', '.join(context['developmental_focus'])}
4. Include practical tips for parents
5. Provide adaptation strategies for different baby moods
6. Consider the day of the week and seasonal factors
7. Make activities specific and actionable, not generic

Generate activities that build on what the baby enjoys while introducing gentle new challenges."""
        
        return prompt
    
    def _format_yesterday_insights(self, yesterday: Optional[Dict[str, Any]]) -> str:
        """Format yesterday's insights for prompt"""
        if not yesterday:
            return "No data from yesterday"
        
        return f"""- Enjoyed: {', '.join(yesterday['enjoyed'])}
- Disliked: {', '.join(yesterday['disliked'])}
- Sleep Quality: {yesterday['sleep_quality']}/10
- Journal Notes: {len(yesterday['journal_entries'])} entries"""
    
    def _validate_and_format_template(self, template_data: Dict[str, Any], 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and format LLM-generated template"""
        
        # Ensure required structure
        if "template_sections" not in template_data:
            template_data["template_sections"] = {}
        
        # Validate each section
        for section in ["morning_routine", "afternoon_routine", "evening_routine"]:
            if section not in template_data["template_sections"]:
                template_data["template_sections"][section] = {
                    "title": section.replace("_", " ").title(),
                    "activities": []
                }
        
        # Ensure schedule adjustments
        if "schedule_adjustments" not in template_data:
            template_data["schedule_adjustments"] = {
                "feeding_times": context["current_patterns"]["feeding_schedule"],
                "sleep_times": context["current_patterns"]["sleep_schedule"]
            }
        
        # Add metadata
        template_data["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "baby_age": context["baby_info"]["age_months"],
            "developmental_stage": context["baby_info"]["developmental_stage"],
            "based_on_feedback": len(context["recent_feedback"]["most_enjoyed"]) > 0
        }
        
        return template_data
    
    def _generate_fallback_template(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback template when LLM is unavailable"""
        
        age_months = context["baby_info"]["age_months"]
        developmental_stage = context["baby_info"]["developmental_stage"]
        
        # Use age-appropriate base activities
        base_activities = self._get_base_activities_by_age(age_months)
        
        # Adapt based on feedback
        adapted_activities = self._adapt_activities_from_feedback(
            base_activities, 
            context["recent_feedback"]
        )
        
        template = {
            "template_sections": {
                "morning_routine": {
                    "title": "Morning Routine (6 AM - 12 PM)",
                    "activities": adapted_activities["morning"]
                },
                "afternoon_routine": {
                    "title": "Afternoon Routine (12 PM - 6 PM)",
                    "activities": adapted_activities["afternoon"]
                },
                "evening_routine": {
                    "title": "Evening Routine (6 PM - 10 PM)",
                    "activities": adapted_activities["evening"]
                }
            },
            "schedule_adjustments": {
                "feeding_times": context["current_patterns"]["feeding_schedule"],
                "sleep_times": context["current_patterns"]["sleep_schedule"]
            },
            "focus_areas": context["developmental_focus"],
            "developmental_targets": self._get_developmental_targets(developmental_stage),
            "parenting_tips": self._get_parenting_tips(age_months, context["recent_feedback"]),
            "adaptation_notes": f"Adapt activities based on {context['baby_info']['days_old']} day old baby's responses",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "baby_age": age_months,
                "developmental_stage": developmental_stage,
                "fallback_mode": True
            }
        }
        
        return template
    
    def _get_base_activities_by_age(self, age_months: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get base activities by age"""
        
        if age_months < 0:  # Prenatal
            return {
                "morning": [
                    {
                        "name": "belly_rubbing",
                        "description": "Gentle belly rubbing and talking to baby",
                        "focus_area": "bonding",
                        "duration": "10-15 minutes",
                        "tips": ["Use gentle circular motions", "Talk softly to baby"],
                        "adaptations": ["Shorter if baby is active", "Longer if baby is calm"]
                    }
                ],
                "afternoon": [
                    {
                        "name": "reading_stories",
                        "description": "Read stories to baby with calm voice",
                        "focus_area": "development",
                        "duration": "15-20 minutes",
                        "tips": ["Choose rhythmic stories", "Use expressive voice"],
                        "adaptations": ["Shorter if baby moves a lot", "Longer if baby is still"]
                    }
                ],
                "evening": [
                    {
                        "name": "gentle_music",
                        "description": "Play calming music for baby",
                        "focus_area": "comfort",
                        "duration": "20-30 minutes",
                        "tips": ["Keep volume low", "Choose soft melodies"],
                        "adaptations": ["Skip if baby is overstimulated", "Extend if baby enjoys"]
                    }
                ]
            }
        
        elif age_months == 0:  # Newborn
            return {
                "morning": [
                    {
                        "name": "skin_to_skin",
                        "description": "Skin-to-skin contact for bonding",
                        "focus_area": "bonding",
                        "duration": "20-30 minutes",
                        "tips": ["Ensure baby is diapered", "Maintain warm temperature"],
                        "adaptations": ["Shorter if baby is fussy", "Longer if baby is calm"]
                    }
                ],
                "afternoon": [
                    {
                        "name": "gentle_touch",
                        "description": "Gentle massage and touching",
                        "focus_area": "development",
                        "duration": "10-15 minutes",
                        "tips": ["Use baby-safe oil", "Follow baby's cues"],
                        "adaptations": ["Skip if baby is hungry", "Extend if baby enjoys"]
                    }
                ],
                "evening": [
                    {
                        "name": "swaddling",
                        "description": "Comfort swaddling routine",
                        "focus_area": "comfort",
                        "duration": "10 minutes",
                        "tips": ["Ensure proper swaddling technique", "Check temperature"],
                        "adaptations": ["Looser if baby resists", "Skip if baby is too warm"]
                    }
                ]
            }
        
        else:  # Older baby
            return {
                "morning": [
                    {
                        "name": "tummy_time",
                        "description": "Tummy time for strength development",
                        "focus_area": "motor",
                        "duration": "5-10 minutes",
                        "tips": ["Place favorite toys nearby", "Get on baby's level"],
                        "adaptations": ["Shorter if baby is fussy", "Longer if baby is strong"]
                    }
                ],
                "afternoon": [
                    {
                        "name": "sensory_play",
                        "description": "Age-appropriate sensory activities",
                        "focus_area": "sensory",
                        "duration": "15-20 minutes",
                        "tips": ["Introduce new textures gradually", "Watch for overstimulation"],
                        "adaptations": ["Simpler if baby is tired", "More complex if baby is alert"]
                    }
                ],
                "evening": [
                    {
                        "name": "reading_time",
                        "description": "Interactive reading and storytelling",
                        "focus_area": "cognitive",
                        "duration": "10-15 minutes",
                        "tips": ["Use colorful books", "Let baby touch pages"],
                        "adaptations": ["Shorter if baby is restless", "Longer if baby is engaged"]
                    }
                ]
            }
    
    def _adapt_activities_from_feedback(self, base_activities: Dict[str, List[Dict[str, Any]]], 
                                      feedback: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Adapt activities based on recent feedback"""
        
        enjoyed = set(feedback.get("most_enjoyed", []))
        disliked = set(feedback.get("most_disliked", []))
        
        adapted = {}
        
        for period, activities in base_activities.items():
            adapted_activities = []
            
            for activity in activities:
                # Check if this activity type was enjoyed or disliked
                activity_name = activity["name"]
                
                if activity_name in disliked:
                    # Replace with alternative
                    alternative = self._find_alternative_activity(activity_name, feedback)
                    if alternative:
                        adapted_activities.append(alternative)
                    else:
                        adapted_activities.append(activity)  # Keep original if no alternative
                elif activity_name in enjoyed:
                    # Enhance with additional tips
                    enhanced_activity = activity.copy()
                    enhanced_activity["tips"].append("Baby enjoyed this recently - extend if engaged")
                    adapted_activities.append(enhanced_activity)
                else:
                    # Keep as is
                    adapted_activities.append(activity)
            
            adapted[period] = adapted_activities
        
        return adapted
    
    def _find_alternative_activity(self, disliked_activity: str, 
                                 feedback: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find alternative activity for disliked one"""
        
        alternatives = {
            "tummy_time": {
                "name": "side_laying",
                "description": "Side laying practice for strength",
                "focus_area": "motor",
                "duration": "5-10 minutes",
                "tips": ["Use rolled towels for support", "Supervise closely"],
                "adaptations": ["Shorter if baby is fussy", "Longer if baby is comfortable"]
            },
            "sensory_play": {
                "name": "quiet_observation",
                "description": "Quiet observation of surroundings",
                "focus_area": "sensory",
                "duration": "10-15 minutes",
                "tips": ["Change baby's position frequently", "Use soft lighting"],
                "adaptations": ["Shorter if baby is restless", "Longer if baby is calm"]
            }
        }
        
        return alternatives.get(disliked_activity)
    
    def _get_developmental_targets(self, developmental_stage: str) -> List[str]:
        """Get developmental targets by stage"""
        
        targets = {
            "prenatal": ["mother-baby bonding", "familiarization with voices"],
            "newborn": ["bonding", "basic sensory development", "feeding routines"],
            "infant": ["motor skills", "sensory exploration", "social interaction"],
            "toddler": ["walking practice", "language development", "independence skills"],
            "young_toddler": ["cognitive development", "social skills", "language acquisition"],
            "toddler_2": ["advanced language", "social skills", "independence"],
            "preschool": ["pre-academic skills", "social development", "self-care"]
        }
        
        return targets.get(developmental_stage, ["development", "bonding"])
    
    def _get_parenting_tips(self, age_months: int, feedback: Dict[str, Any]) -> List[str]:
        """Get parenting tips based on age and feedback"""
        
        base_tips = {
            -1: [  # Prenatal
                "Talk to baby throughout the day",
                "Play gentle music for baby",
                "Take time to rest and bond"
            ],
            0: [   # Newborn
                "Follow baby's hunger cues",
                "Ensure proper head support",
                "Create a calm environment"
            ],
            1: [   # 1 month
                "Establish consistent routines",
                "Respond to baby's cries promptly",
                "Practice tummy time when baby is alert"
            ],
            3: [   # 3 months
                "Encourage reaching for toys",
                "Practice rolling over",
                "Maintain consistent sleep schedule"
            ],
            6: [   # 6 months
                "Introduce solid foods if ready",
                "Baby-proof the environment",
                "Encourage sitting practice"
            ],
            9: [   # 9 months
                "Practice crawling and pulling up",
                "Introduce finger foods",
                "Use simple language"
            ],
            12: [  # 12 months
                "Encourage first steps",
                "Practice simple words",
                "Establish clear boundaries"
            ]
        }
        
        tips = base_tips.get(age_months, ["Follow baby's cues", "Maintain routines"])
        
        # Add feedback-specific tips
        if feedback.get("avg_sleep", 0) < 6:
            tips.append("Focus on improving sleep quality and routines")
        
        if feedback.get("most_disliked"):
            tips.append(f"Be patient with activities - baby is learning preferences")
        
        return tips[:3]  # Return top 3 tips

# Singleton instance
llm_template_generator = LLMTemplateGenerator()
