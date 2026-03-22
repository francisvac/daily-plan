#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - LLM Integration Analysis & Optimization
Analyzes what works well with LLM integration and optimizes the code accordingly
"""

import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from config import (
    DEVELOPMENT_STAGES, FEEDBACK_KEYWORDS, JOURNAL_KEYWORDS,
    TEMPLATE_PLACEHOLDERS, ConfigManager
)
from base_classes import BabyPlannerBase, memory_manager, patterns_manager
from logger import get_logger, log_error, log_success, log_warning

class LLMPerformanceLevel(Enum):
    """LLM performance levels for optimization"""
    HIGH = "high"           # Full LLM capabilities available
    MEDIUM = "medium"       # LLM available but with limitations
    LOW = "low"            # LLM unreliable, use fallback
    UNAVAILABLE = "unavailable"  # No LLM access

@dataclass
class LLMPerformanceMetrics:
    """Metrics for tracking LLM performance"""
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    error_count: int = 0
    timeout_count: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

class OptimizedLLMTemplateGenerator(BabyPlannerBase):
    """Optimized LLM template generator with performance tracking and adaptive strategies"""
    
    def __init__(self):
        super().__init__("optimized_llm_generator")
        self.template_cache = {}
        self.cache_expiry_hours = 6
        self.performance_metrics = LLMPerformanceMetrics()
        self.performance_level = LLMPerformanceLevel.HIGH
        self.request_history = []
        self.max_history_size = 100
        
        # Performance thresholds
        self.success_rate_threshold = 0.7  # 70% success rate
        self.response_time_threshold = 15.0  # 15 seconds
        self.consecutive_failures_threshold = 3
        
    def generate_daily_template(self, target_date: datetime.date, 
                               age_months: int, 
                               developmental_stage: str) -> Dict[str, Any]:
        """Generate optimized dynamic template with adaptive LLM usage"""
        
        # Check cache first (always fastest)
        cache_key = f"{target_date}_{age_months}_{developmental_stage}"
        if self._is_cache_valid(cache_key):
            self.logger.info(f"Using cached template for {target_date}")
            return self.template_cache[cache_key]['template']
        
        # Determine strategy based on performance level
        if self.performance_level == LLMPerformanceLevel.UNAVAILABLE:
            self.logger.info("LLM unavailable, using fallback generation")
            return self._generate_fallback_template(target_date, age_months, developmental_stage)
        
        # Try LLM with appropriate strategy
        template = self._generate_with_adaptive_strategy(target_date, age_months, developmental_stage)
        
        # Cache the result
        self.template_cache[cache_key] = {
            'template': template,
            'timestamp': datetime.now()
        }
        
        return template
    
    def _generate_with_adaptive_strategy(self, target_date: datetime.date, 
                                       age_months: int, 
                                       developmental_stage: str) -> Dict[str, Any]:
        """Generate template using adaptive strategy based on performance level"""
        
        if self.performance_level == LLMPerformanceLevel.HIGH:
            return self._generate_full_llm_template(target_date, age_months, developmental_stage)
        elif self.performance_level == LLMPerformanceLevel.MEDIUM:
            return self._generate_hybrid_template(target_date, age_months, developmental_stage)
        else:  # LOW
            return self._generate_smart_fallback_template(target_date, age_months, developmental_stage)
    
    def _generate_full_llm_template(self, target_date: datetime.date, 
                                   age_months: int, 
                                   developmental_stage: str) -> Dict[str, Any]:
        """Full LLM generation with comprehensive context"""
        
        start_time = time.time()
        
        try:
            # Build comprehensive context
            context = self._build_enhanced_context(target_date, age_months, developmental_stage)
            
            # Generate with LLM
            template = self._call_llm_with_retry(context, max_retries=2)
            
            # Track success
            response_time = time.time() - start_time
            self._track_llm_success(response_time)
            
            return template
            
        except Exception as e:
            response_time = time.time() - start_time
            self._track_llm_failure(str(e), response_time)
            
            # Fall back to hybrid approach
            return self._generate_hybrid_template(target_date, age_months, developmental_stage)
    
    def _generate_hybrid_template(self, target_date: datetime.date, 
                                  age_months: int, 
                                  developmental_stage: str) -> Dict[str, Any]:
        """Hybrid approach: LLM for key decisions, rules for structure"""
        
        try:
            # Use LLM for activity selection only (faster, more reliable)
            activity_suggestions = self._get_llm_activity_suggestions(age_months, developmental_stage)
            
            # Build template with rule-based structure and LLM activities
            template = self._build_template_from_suggestions(activity_suggestions, target_date, age_months, developmental_stage)
            
            self.logger.info("Generated hybrid template (LLM activities + rule-based structure)")
            return template
            
        except Exception as e:
            log_warning(self.component_name, f"Hybrid generation failed: {e}")
            return self._generate_smart_fallback_template(target_date, age_months, developmental_stage)
    
    def _generate_smart_fallback_template(self, target_date: datetime.date, 
                                         age_months: int, 
                                         developmental_stage: str) -> Dict[str, Any]:
        """Smart fallback with feedback adaptation"""
        
        # Get context for smart adaptation
        context = self._build_basic_context(target_date, age_months, developmental_stage)
        
        # Generate enhanced fallback
        template = self._generate_enhanced_fallback(context)
        
        self.logger.info("Generated smart fallback template with feedback adaptation")
        return template
    
    def _build_enhanced_context(self, target_date: datetime.date, 
                               age_months: int, 
                               developmental_stage: str) -> Dict[str, Any]:
        """Build enhanced context with more relevant data"""
        
        # Get comprehensive feedback data
        recent_memory = memory_manager.get_summary(7)
        yesterday_feedback = self._get_yesterday_feedback(target_date)
        
        # Get patterns
        patterns = patterns_manager.get_baby_patterns()
        
        # Build enhanced context
        context = {
            "baby_info": {
                "age_months": age_months,
                "developmental_stage": developmental_stage,
                "birth_date": patterns.get("birth_date", "2025-03-17"),
                "days_old": self._calculate_days_old(target_date, patterns)
            },
            "performance_context": {
                "recent_success_rate": self.performance_metrics.success_rate,
                "avg_response_time": self.performance_metrics.avg_response_time,
                "current_strategy": self.performance_level.value
            },
            "enhanced_patterns": {
                "favorite_activities": patterns.get("favorite_activities", []),
                "sleep_schedule": patterns.get("sleep_schedule", {}),
                "feeding_schedule": patterns.get("feeding_schedule", {}),
                "comfort_patterns": patterns.get("comfort_patterns", {})
            },
            "detailed_feedback": {
                "most_enjoyed": recent_memory.get("most_enjoyed", []),
                "most_disliked": recent_memory.get("most_disliked", []),
                "avg_sleep": recent_memory.get("avg_sleep", 0),
                "feeding_patterns": recent_memory.get("feeding_patterns", []),
                "developmental_notes": recent_memory.get("developmental_notes", []),
                "success_patterns": self._analyze_success_patterns(recent_memory)
            },
            "yesterday_insights": yesterday_feedback or {},
            "environmental_context": {
                "date": target_date.strftime('%Y-%m-%d'),
                "day_of_week": target_date.strftime('%A'),
                "season": self._get_season(target_date),
                "time_of_generation": datetime.now().strftime('%H:%M')
            },
            "developmental_focus": DEVELOPMENT_STAGES.get(developmental_stage, {}).get("focus", [])
        }
        
        return context
    
    def _analyze_success_patterns(self, memory_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in successful activities"""
        
        return {
            "best_times": self._identify_best_activity_times(memory_summary),
            "optimal_duration": self._estimate_optimal_duration(memory_summary),
            "preferred_focus": self._identify_preferred_focus_areas(memory_summary),
            "avoid_triggers": self._identify_dislike_triggers(memory_summary)
        }
    
    def _identify_best_activity_times(self, memory_summary: Dict[str, Any]) -> List[str]:
        """Identify best times for activities based on feedback"""
        # Simple heuristic - could be enhanced with more sophisticated analysis
        return ["morning", "afternoon"] if memory_summary.get("avg_sleep", 0) >= 7 else ["morning"]
    
    def _estimate_optimal_duration(self, memory_summary: Dict[str, Any]) -> str:
        """Estimate optimal activity duration"""
        sleep_quality = memory_summary.get("avg_sleep", 5)
        if sleep_quality >= 8:
            return "15-20 minutes"
        elif sleep_quality >= 6:
            return "10-15 minutes"
        else:
            return "5-10 minutes"
    
    def _identify_preferred_focus_areas(self, memory_summary: Dict[str, Any]) -> List[str]:
        """Identify preferred focus areas from feedback"""
        enjoyed = memory_summary.get("most_enjoyed", [])
        
        focus_mapping = {
            "touch": ["bonding", "comfort"],
            "skin": ["bonding", "comfort"],
            "music": ["development", "comfort"],
            "reading": ["development", "cognitive"],
            "tummy": ["motor", "development"],
            "sensory": ["development", "sensory"]
        }
        
        preferred_focus = set()
        for activity in enjoyed:
            for keyword, focuses in focus_mapping.items():
                if keyword in activity.lower():
                    preferred_focus.update(focuses)
        
        return list(preferred_focus) if preferred_focus else ["bonding", "comfort"]
    
    def _identify_dislike_triggers(self, memory_summary: Dict[str, Any]) -> List[str]:
        """Identify common triggers for disliked activities"""
        disliked = memory_summary.get("most_disliked", [])
        
        triggers = []
        for activity in disliked:
            if "overstimulated" in activity.lower() or "too much" in activity.lower():
                triggers.append("overstimulation")
            if "fussy" in activity.lower():
                triggers.append("tiredness")
            if "loud" in activity.lower():
                triggers.append("noise_sensitivity")
        
        return list(set(triggers)) if triggers else ["unknown"]
    
    def _call_llm_with_retry(self, context: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """Call LLM with retry logic and better error handling"""
        
        prompt = self._build_optimized_prompt(context)
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                result = subprocess.run([
                    'zeroclaw', 'agent', '-m', prompt,
                    '--output-json'
                ], capture_output=True, text=True, timeout=20)  # Reduced timeout
                
                response_time = time.time() - start_time
                
                if result.returncode == 0:
                    template_data = json.loads(result.stdout)
                    return self._validate_and_format_template(template_data, context)
                else:
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    raise Exception(f"LLM returned non-zero: {error_msg}")
                    
            except subprocess.TimeoutExpired:
                if attempt < max_retries:
                    self.logger.warning(f"LLM timeout, retry {attempt + 1}/{max_retries}")
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    raise Exception("LLM timeout after retries")
                    
            except json.JSONDecodeError as e:
                if attempt < max_retries:
                    self.logger.warning(f"JSON decode error, retry {attempt + 1}/{max_retries}")
                    time.sleep(1)
                    continue
                else:
                    raise Exception(f"Invalid JSON response: {e}")
                    
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"LLM error, retry {attempt + 1}/{max_retries}: {e}")
                    time.sleep(1)
                    continue
                else:
                    raise e
        
        raise Exception("All retry attempts failed")
    
    def _build_optimized_prompt(self, context: Dict[str, Any]) -> str:
        """Build optimized prompt for better LLM performance"""
        
        baby_info = context["baby_info"]
        patterns = context["enhanced_patterns"]
        feedback = context["detailed_feedback"]
        day_info = context["environmental_context"]
        
        # Build focused, structured prompt
        prompt = f"""Generate baby daily plan for {day_info['date']}.

BABY PROFILE:
Age: {baby_info['age_months']} months ({baby_info['days_old']} days)
Stage: {baby_info['developmental_stage']}
Focus: {', '.join(context['developmental_focus'])}

CURRENT PATTERNS:
Favorites: {', '.join(patterns['favorite_activities'])}
Sleep: {patterns['sleep_schedule']}
Feeding: {patterns['feeding_schedule']}

RECENT FEEDBACK (7 days):
Enjoyed: {', '.join(feedback['most_enjoyed'])}
Disliked: {', '.join(feedback['most_disliked'])}
Sleep Quality: {feedback['avg_sleep']:.1f}/10
Preferred Focus: {', '.join(feedback['preferred_focus'])}
Avoid Triggers: {', '.join(feedback['avoid_triggers'])}

Generate JSON template:
{{
  "activities": {{
    "morning": [{{"name": "activity", "focus": "area", "duration": "time", "tips": ["tip1"]}}],
    "afternoon": [...],
    "evening": [...]
  }},
  "schedule": {{"feeding": {...}, "sleep": {...}}},
  "focus_areas": [...],
  "tips": [...]
}}

Keep activities age-appropriate and based on feedback. Be concise."""
        
        return prompt
    
    def _get_llm_activity_suggestions(self, age_months: int, developmental_stage: str) -> List[Dict[str, Any]]:
        """Get activity suggestions from LLM (focused request)"""
        
        try:
            # Simple, focused prompt for activities only
            prompt = f"""Suggest 3 age-appropriate activities for {age_months} month old baby ({developmental_stage} stage).

Return JSON:
{{"activities": [{{"name": "activity", "focus": "area", "tips": ["tip"]}}]}}"""
            
            result = subprocess.run([
                'zeroclaw', 'agent', '-m', prompt,
                '--output-json'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("activities", [])
            
        except Exception as e:
            log_warning(self.component_name, f"Activity suggestions failed: {e}")
        
        return []
    
    def _build_template_from_suggestions(self, suggestions: List[Dict[str, Any]], 
                                         target_date: datetime.date,
                                         age_months: int, 
                                         developmental_stage: str) -> Dict[str, Any]:
        """Build template from LLM suggestions and rule-based structure"""
        
        # Get context for adaptation
        context = self._build_basic_context(target_date, age_months, developmental_stage)
        
        # Build template structure
        template = {
            "template_sections": {
                "morning_routine": {
                    "title": "Morning Routine (6 AM - 12 PM)",
                    "activities": []
                },
                "afternoon_routine": {
                    "title": "Afternoon Routine (12 PM - 6 PM)",
                    "activities": []
                },
                "evening_routine": {
                    "title": "Evening Routine (6 PM - 10 PM)",
                    "activities": []
                }
            },
            "schedule_adjustments": context["current_patterns"].get("feeding_schedule", {}),
            "focus_areas": context["developmental_focus"],
            "developmental_targets": self._get_developmental_targets(developmental_stage),
            "parenting_tips": self._get_parenting_tips(age_months, context["recent_feedback"]),
            "adaptation_notes": f"Generated using hybrid approach (LLM + rules) for {age_months} month old"
        }
        
        # Distribute suggestions across time periods
        if suggestions:
            for i, suggestion in enumerate(suggestions[:3]):  # Max 3 suggestions
                period = ["morning", "afternoon", "evening"][i % 3]
                
                activity = {
                    "name": suggestion.get("name", f"activity_{i}"),
                    "description": f"Age-appropriate {suggestion.get('focus', 'development')} activity",
                    "focus_area": suggestion.get("focus", "development"),
                    "duration": "10-15 minutes",
                    "tips": suggestion.get("tips", ["Follow baby's cues"]),
                    "adaptations": ["Shorter if fussy", "Extend if engaged"]
                }
                
                template["template_sections"][f"{period}_routine"]["activities"].append(activity)
        
        return template
    
    def _track_llm_success(self, response_time: float):
        """Track successful LLM call"""
        self.request_history.append({
            "timestamp": datetime.now(),
            "success": True,
            "response_time": response_time,
            "error": None
        })
        
        # Update metrics
        self._update_performance_metrics()
        
        # Log success
        log_success(self.component_name, f"LLM success in {response_time:.2f}s")
    
    def _track_llm_failure(self, error: str, response_time: float):
        """Track failed LLM call"""
        self.request_history.append({
            "timestamp": datetime.now(),
            "success": False,
            "response_time": response_time,
            "error": error
        })
        
        # Update metrics
        self._update_performance_metrics()
        
        # Log failure
        log_warning(self.component_name, f"LLM failure: {error} (took {response_time:.2f}s)")
    
    def _update_performance_metrics(self):
        """Update performance metrics from request history"""
        
        # Keep only recent history
        if len(self.request_history) > self.max_history_size:
            self.request_history = self.request_history[-self.max_history_size:]
        
        if not self.request_history:
            return
        
        # Calculate metrics
        recent_requests = self.request_history[-20:]  # Last 20 requests
        
        success_count = sum(1 for r in recent_requests if r["success"])
        self.performance_metrics.success_rate = success_count / len(recent_requests)
        
        successful_requests = [r for r in recent_requests if r["success"]]
        if successful_requests:
            self.performance_metrics.avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests)
        
        self.performance_metrics.error_count = sum(1 for r in recent_requests if not r["success"])
        
        # Update performance level
        self._update_performance_level()
    
    def _update_performance_level(self):
        """Update performance level based on metrics"""
        
        success_rate = self.performance_metrics.success_rate
        avg_response_time = self.performance_metrics.avg_response_time
        error_count = self.performance_metrics.error_count
        
        # Check consecutive failures
        consecutive_failures = 0
        for request in reversed(self.request_history[-10:]):
            if not request["success"]:
                consecutive_failures += 1
            else:
                break
        
        # Determine performance level
        if consecutive_failures >= self.consecutive_failures_threshold:
            self.performance_level = LLMPerformanceLevel.UNAVAILABLE
        elif success_rate < 0.5 or avg_response_time > self.response_time_threshold * 2:
            self.performance_level = LLMPerformanceLevel.LOW
        elif success_rate < self.success_rate_threshold or avg_response_time > self.response_time_threshold:
            self.performance_level = LLMPerformanceLevel.MEDIUM
        else:
            self.performance_level = LLMPerformanceLevel.HIGH
        
        self.logger.info(f"Performance level updated to: {self.performance_level.value}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        
        return {
            "current_level": self.performance_level.value,
            "success_rate": f"{self.performance_metrics.success_rate:.1%}",
            "avg_response_time": f"{self.performance_metrics.avg_response_time:.2f}s",
            "error_count": self.performance_metrics.error_count,
            "total_requests": len(self.request_history),
            "cache_size": len(self.template_cache),
            "recommendations": self._get_performance_recommendations()
        }
    
    def _get_performance_recommendations(self) -> List[str]:
        """Get recommendations based on performance"""
        
        recommendations = []
        
        if self.performance_level == LLMPerformanceLevel.UNAVAILABLE:
            recommendations.append("LLM is unavailable - using fallback generation")
            recommendations.append("Check LLM service availability and configuration")
        elif self.performance_level == LLMPerformanceLevel.LOW:
            recommendations.append("LLM performance is poor - using hybrid approach")
            recommendations.append("Consider increasing timeout or reducing prompt complexity")
        elif self.performance_level == LLMPerformanceLevel.MEDIUM:
            recommendations.append("LLM performance is moderate - optimized strategy in use")
            recommendations.append("Monitor response times and success rates")
        else:
            recommendations.append("LLM performance is excellent - full generation active")
        
        return recommendations
    
    # Include existing methods from original class
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached template is still valid"""
        if cache_key not in self.template_cache:
            return False
        
        cached_time = self.template_cache[cache_key]['timestamp']
        expiry_time = cached_time + timedelta(hours=self.cache_expiry_hours)
        
        return datetime.now() < expiry_time
    
    def _build_basic_context(self, target_date: datetime.date, 
                           age_months: int, 
                           developmental_stage: str) -> Dict[str, Any]:
        """Build basic context for fallback generation"""
        patterns = patterns_manager.get_baby_patterns()
        recent_memory = memory_manager.get_summary(7)
        
        return {
            "baby_info": {
                "age_months": age_months,
                "developmental_stage": developmental_stage,
                "days_old": self._calculate_days_old(target_date, patterns)
            },
            "current_patterns": patterns,
            "recent_feedback": recent_memory,
            "developmental_focus": DEVELOPMENT_STAGES.get(developmental_stage, {}).get("focus", [])
        }
    
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
    
    def _validate_and_format_template(self, template_data: Dict[str, Any], 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and format LLM-generated template"""
        # Implementation from original class
        if "template_sections" not in template_data:
            template_data["template_sections"] = {}
        
        for section in ["morning_routine", "afternoon_routine", "evening_routine"]:
            if section not in template_data["template_sections"]:
                template_data["template_sections"][section] = {
                    "title": section.replace("_", " ").title(),
                    "activities": []
                }
        
        if "schedule_adjustments" not in template_data:
            template_data["schedule_adjustments"] = context["current_patterns"]
        
        template_data["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "baby_age": context["baby_info"]["age_months"],
            "developmental_stage": context["baby_info"]["developmental_stage"],
            "performance_level": self.performance_level.value
        }
        
        return template_data
    
    def _generate_enhanced_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced fallback template with feedback adaptation"""
        # Implementation from original class with enhancements
        age_months = context["baby_info"]["age_months"]
        developmental_stage = context["baby_info"]["developmental_stage"]
        
        base_activities = self._get_base_activities_by_age(age_months)
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
            "schedule_adjustments": context["current_patterns"],
            "focus_areas": context["developmental_focus"],
            "developmental_targets": self._get_developmental_targets(developmental_stage),
            "parenting_tips": self._get_parenting_tips(age_months, context["recent_feedback"]),
            "adaptation_notes": f"Enhanced fallback for {age_months} months old with feedback adaptation",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "baby_age": age_months,
                "developmental_stage": developmental_stage,
                "fallback_mode": True,
                "enhanced": True
            }
        }
        
        return template
    
    # Include remaining methods from original class...
    def _get_base_activities_by_age(self, age_months: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get base activities by age"""
        # Implementation from original class
        if age_months < 0:  # Prenatal
            return {
                "morning": [{"name": "belly_rubbing", "description": "Gentle belly rubbing", "focus_area": "bonding"}],
                "afternoon": [{"name": "reading_stories", "description": "Read stories", "focus_area": "development"}],
                "evening": [{"name": "gentle_music", "description": "Play calming music", "focus_area": "comfort"}]
            }
        elif age_months == 0:  # Newborn
            return {
                "morning": [{"name": "skin_to_skin", "description": "Skin-to-skin contact", "focus_area": "bonding"}],
                "afternoon": [{"name": "gentle_touch", "description": "Gentle massage", "focus_area": "development"}],
                "evening": [{"name": "swaddling", "description": "Comfort swaddling", "focus_area": "comfort"}]
            }
        else:  # Older baby
            return {
                "morning": [{"name": "tummy_time", "description": "Tummy time practice", "focus_area": "motor"}],
                "afternoon": [{"name": "sensory_play", "description": "Sensory activities", "focus_area": "sensory"}],
                "evening": [{"name": "reading_time", "description": "Reading books", "focus_area": "cognitive"}]
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
                activity_name = activity["name"]
                if activity_name in disliked:
                    # Replace with alternative
                    alternative = self._find_alternative_activity(activity_name, feedback)
                    adapted_activities.append(alternative if alternative else activity)
                elif activity_name in enjoyed:
                    # Enhance enjoyed activities
                    enhanced = activity.copy()
                    enhanced["tips"] = activity.get("tips", []) + ["Baby enjoyed this recently"]
                    adapted_activities.append(enhanced)
                else:
                    adapted_activities.append(activity)
            adapted[period] = adapted_activities
        
        return adapted
    
    def _find_alternative_activity(self, disliked_activity: str, 
                                 feedback: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find alternative activity for disliked one"""
        alternatives = {
            "tummy_time": {"name": "side_laying", "description": "Side laying practice", "focus_area": "motor"},
            "sensory_play": {"name": "quiet_observation", "description": "Quiet observation", "focus_area": "sensory"}
        }
        return alternatives.get(disliked_activity)
    
    def _get_developmental_targets(self, developmental_stage: str) -> List[str]:
        """Get developmental targets by stage"""
        targets = {
            "prenatal": ["mother-baby bonding", "familiarization with voices"],
            "newborn": ["bonding", "basic sensory development", "feeding routines"],
            "infant": ["motor skills", "sensory exploration", "social interaction"],
            "toddler": ["walking practice", "language development", "independence skills"]
        }
        return targets.get(developmental_stage, ["development", "bonding"])
    
    def _get_parenting_tips(self, age_months: int, feedback: Dict[str, Any]) -> List[str]:
        """Get parenting tips based on age and feedback"""
        base_tips = {
            -1: ["Talk to baby throughout the day", "Play gentle music"],
            0: ["Follow baby's hunger cues", "Ensure proper head support"],
            1: ["Establish consistent routines", "Respond to cries promptly"],
            3: ["Encourage reaching for toys", "Practice rolling over"],
            6: ["Introduce solid foods if ready", "Baby-proof environment"],
            12: ["Encourage first steps", "Practice simple words"]
        }
        
        tips = base_tips.get(age_months, ["Follow baby's cues", "Maintain routines"])
        
        if feedback.get("avg_sleep", 0) < 6:
            tips.append("Focus on improving sleep quality")
        
        return tips[:3]

# Optimized singleton instance
optimized_llm_generator = OptimizedLLMTemplateGenerator()
