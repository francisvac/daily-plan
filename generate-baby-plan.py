#!/usr/bin/env python3
"""
ZeroClaw Baby Daily Plan Generator - Refactored
Generates personalized daily plans for baby activities based on age and feedback
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import (
    AGE_ACTIVITIES, DEVELOPMENT_STAGES, TEMPLATE_PLACEHOLDERS,
    ERROR_MESSAGES, SUCCESS_MESSAGES, ConfigManager
)
from base_classes import BabyPlannerBase, memory_manager, patterns_manager
from logger import get_logger, log_error, log_success, log_warning

class BabyPlanGenerator(BabyPlannerBase):
    """Refactored baby plan generator with improved architecture"""
    
    def __init__(self):
        super().__init__("plan_generator")
        self.template_file = Path.home() / "daily-plans" / "template.md"
        self.plan_dir = Path.home() / "daily-plans"
    
    def generate(self, date_str: Optional[str] = None, baby_age_months: Optional[int] = None) -> bool:
        """Main generation method with improved error handling"""
        try:
            target_date = self._parse_date(date_str)
            self.logger.info(f"Generating baby plan for: {target_date}")
            
            # Load patterns and calculate age
            patterns = patterns_manager.get_baby_patterns()
            baby_age = self._calculate_baby_age(target_date, baby_age_months, patterns)
            
            if baby_age is None:
                log_error(self.component_name, ValueError("Could not determine baby age"))
                return False
            
            # Update patterns with calculated age
            patterns["age_months"] = baby_age
            patterns["developmental_stage"] = ConfigManager.get_developmental_stage(baby_age)
            patterns_manager.update_baby_patterns(patterns)
            
            # Get historical feedback
            yesterday_feedback = self._get_yesterday_feedback(target_date)
            
            # Generate plan content
            self.logger.info(f"Generating age-appropriate activities for {baby_age} months ({patterns['developmental_stage']} stage)")
            plan_data = self._generate_plan_content(target_date, patterns, yesterday_feedback)
            
            # Create and save plan file
            plan_file = self._create_plan_file(target_date, plan_data)
            
            # Send email
            self._send_plan_email(target_date, plan_file)
            
            # Display summary
            self._display_summary(plan_data, target_date)
            
            log_success(self.component_name, f"Baby plan generated: {plan_file}")
            return True
            
        except Exception as e:
            log_error(self.component_name, e, "generating baby plan")
            return False
    
    def _parse_date(self, date_str: Optional[str]) -> datetime.date:
        """Parse date string or use today"""
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(ERROR_MESSAGES["invalid_date"])
        return datetime.now().date()
    
    def _calculate_baby_age(self, target_date: datetime.date, 
                           provided_age: Optional[int], 
                           patterns: Dict[str, Any]) -> Optional[int]:
        """Calculate baby's age in months"""
        if provided_age is not None:
            return provided_age
        
        birth_date_str = patterns.get("birth_date")
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                days_diff = (target_date - birth_date).days
                
                if days_diff < 30:
                    return 0  # Newborn stage
                else:
                    return days_diff // 30
            except ValueError:
                log_warning(self.component_name, f"Invalid birth date format: {birth_date_str}")
        
        return patterns.get("age_months", 0)
    
    def _calculate_baby_age_days(self, target_date: datetime.date, patterns: Dict[str, Any]) -> int:
        """Calculate baby's exact age in days"""
        birth_date_str = patterns.get("birth_date")
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                return (target_date - birth_date).days
            except ValueError:
                log_warning(self.component_name, f"Invalid birth date format: {birth_date_str}")
        return 0
    
    def _get_yesterday_feedback(self, target_date: datetime.date) -> Optional[Dict[str, Any]]:
        """Get feedback from yesterday's plan"""
        yesterday = target_date - timedelta(days=1)
        yesterday_plan = self.plan_dir / f"{yesterday.strftime('%Y-%m-%d')}-plan.md"
        
        if yesterday_plan.exists():
            try:
                with open(yesterday_plan, 'r') as f:
                    content = f.read()
                return self._extract_feedback_from_plan(content)
            except IOError as e:
                log_error(self.component_name, e, f"reading yesterday's plan: {yesterday_plan}")
        
        return None
    
    def _extract_feedback_from_plan(self, content: str) -> Dict[str, Any]:
        """Extract feedback from plan content"""
        feedback = {
            'activity_success': self._calculate_activity_success(content),
            'enjoyed_activities': self._extract_feedback_section(content, ['enjoyed', 'liked']),
            'disliked_activities': self._extract_feedback_section(content, ['disliked', 'fussy']),
            'sleep_quality': self._extract_sleep_quality(content),
            'feeding_response': self._extract_feeding_response(content)
        }
        return feedback
    
    def _calculate_activity_success(self, content: str) -> float:
        """Calculate activity success rate"""
        try:
            if '## 🍼 Daily Baby Activities' in content:
                todo_section = content.split('## 🍼 Daily Baby Activities')[1].split('## 😴 Sleep & Feeding Schedule')[0]
                completed_section = content.split('## ✅ Completed Activities')[1].split('## 📝 Baby Feedback Section')[0]
            else:
                return 50.0  # Default if parsing fails
            
            todo_count = todo_section.count('- [ ]')
            completed_count = completed_section.count('- [x]') + completed_section.count('- [X]')
            
            if todo_count == 0:
                return 0
            return (completed_count / todo_count) * 100
        except (IndexError, KeyError):
            return 50.0
    
    def _extract_feedback_section(self, content: str, keywords: List[str]) -> List[str]:
        """Extract feedback section by keywords"""
        lines = content.split('\n')
        relevant_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                clean_line = re.sub(r'^[-*•]\s*', '', line.strip())
                if clean_line and len(clean_line) > 3 and 'TBD' not in clean_line:
                    relevant_lines.append(clean_line)
        
        return relevant_lines[:3]
    
    def _extract_sleep_quality(self, content: str) -> int:
        """Extract sleep quality rating"""
        sleep_pattern = r'\*\*Sleep Quality \(1-10\):\*\* (\d+)'
        match = re.search(sleep_pattern, content)
        return int(match.group(1)) if match else 5
    
    def _extract_feeding_response(self, content: str) -> str:
        """Extract feeding response"""
        feeding_pattern = r'\*\*Feeding Response:\*\* (.+)'
        match = re.search(feeding_pattern, content)
        return match.group(1).strip() if match else "Normal"
    
    def _get_age_appropriate_activities(self, age_months: int, patterns: Dict[str, Any]) -> Dict[str, List[str]]:
        """Get age-appropriate activities"""
        if age_months < 0:
            return AGE_ACTIVITIES[-1]
        elif age_months == 0:
            return AGE_ACTIVITIES[0]
        else:
            # Find the highest age key that's <= age_months
            valid_ages = [k for k in AGE_ACTIVITIES.keys() if k <= age_months and k >= 0]
            if valid_ages:
                age_range = max(valid_ages)
                return AGE_ACTIVITIES[age_range]
            else:
                return AGE_ACTIVITIES[0]
    
    def _generate_plan_content(self, target_date: datetime.date, 
                             patterns: Dict[str, Any], 
                             yesterday_feedback: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate plan content using ZeroClaw AI or fallback"""
        try:
            # Try ZeroClaw AI first
            plan_data = self._generate_with_zeroclaw(target_date, patterns, yesterday_feedback)
            if plan_data:
                return plan_data
        except Exception as e:
            log_warning(self.component_name, f"ZeroClaw generation failed: {e}")
        
        # Fallback to template-based generation
        return self._generate_fallback_plan(target_date, patterns, yesterday_feedback)
    
    def _generate_with_zeroclaw(self, target_date: datetime.date, 
                               patterns: Dict[str, Any], 
                               yesterday_feedback: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate plan using ZeroClaw AI"""
        day_name = target_date.strftime('%A')
        age_months = patterns["age_months"]
        developmental_stage = patterns.get("developmental_stage", "unknown")
        
        # Build context for ZeroClaw
        context = self._build_zeroclaw_context(day_name, target_date, age_months, developmental_stage, yesterday_feedback)
        
        try:
            result = subprocess.run([
                'zeroclaw', 'agent', '-m', context + self._get_zeroclaw_prompt(age_months, developmental_stage),
                '--output-json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            log_warning(self.component_name, f"ZeroClaw error: {e}")
        
        return None
    
    def _build_zeroclaw_context(self, day_name: str, target_date: datetime.date, 
                              age_months: int, developmental_stage: str, 
                              yesterday_feedback: Optional[Dict[str, Any]]) -> str:
        """Build context for ZeroClaw AI"""
        context = f"Generate a personalized baby daily plan for {day_name}, {target_date.strftime('%Y-%m-%d')}."
        
        if age_months < 0:
            context += f"\n\nBaby is currently in the womb (prenatal stage), due on {patterns.get('birth_date', '2025-03-17')}."
            context += f"\nFocus on activities that bond with the baby and prepare for birth."
        elif age_months == 0:
            context += f"\n\nBaby is a newborn (0 months old)."
            context += f"\nFocus on gentle activities, bonding, and basic care routines."
        else:
            context += f"\n\nBaby is {age_months} months old."
            context += f"\nDevelopmental stage: {developmental_stage}"
        
        if yesterday_feedback:
            context += f"\n\nBased on yesterday's feedback:\n"
            context += f"- Enjoyed: {', '.join(yesterday_feedback.get('enjoyed_activities', []))}\n"
            context += f"- Disliked: {', '.join(yesterday_feedback.get('disliked_activities', []))}\n"
            context += f"- Sleep quality: {yesterday_feedback.get('sleep_quality', 5)}/10\n"
        
        return context
    
    def _get_zeroclaw_prompt(self, age_months: int, developmental_stage: str) -> str:
        """Get ZeroClaw prompt based on age"""
        base_prompt = f"""
                
Generate age-appropriate baby activities with this JSON structure:
{{
  "baby_age": {age_months},
  "developmental_stage": "{developmental_stage}",
  "focus_areas": ["bonding", "development", "comfort"],
  "morning_activities": {{
    "bonding": "Specific age-appropriate bonding activity",
    "development": "Age-appropriate developmental activity", 
    "comfort": "Comfort and soothing activity"
  }},
  "afternoon_activities": {{
    "bonding": "Different bonding activity",
    "development": "Different developmental activity",
    "comfort": "Different comfort activity"
  }},
  "evening_activities": {{
    "bonding": "Gentle evening bonding activity",
    "development": "Calming developmental activity",
    "comfort": "Bedtime comfort routine"
  }},
  "feeding_schedule": {{
    "morning": "Time and notes",
    "midday": "Time and notes",
    "afternoon": "Time and notes", 
    "evening": "Time and notes",
    "night": "Time and notes"
  }},
  "sleep_schedule": {{
    "morning_nap": "Time and duration",
    "afternoon_nap": "Time and duration",
    "evening_nap": "Time and duration",
    "night_sleep": "Bedtime and routine"
  }},
  "reasoning": "Why these activities are perfect for this age and stage"
}}
 
"""
        
        if age_months < 0:
            base_prompt += "Make activities specific, age-appropriate, and developmentally beneficial.\nFor prenatal stage: focus on mother-baby bonding, reading to baby, gentle movement, music.\n"
        elif age_months == 0:
            base_prompt += "Make activities specific, age-appropriate, and developmentally beneficial.\nFor newborn stage: focus on gentle touch, bonding, basic care routines.\n"
        else:
            base_prompt += "Make activities specific, age-appropriate, and developmentally beneficial.\nFor older babies: focus on sensory development, motor skills, cognitive activities.\n"
        
        return base_prompt
    
    def _generate_fallback_plan(self, target_date: datetime.date, 
                                patterns: Dict[str, Any], 
                                yesterday_feedback: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback plan using templates"""
        age_months = patterns["age_months"]
        day_name = target_date.strftime('%A')
        
        activities = self._get_age_appropriate_activities(age_months, patterns)
        
        # Determine activity keys based on developmental stage
        if age_months < 0:
            activity_keys = ["belly_rubbing", "reading_stories", "gentle_music"]
        else:
            activity_keys = ["tummy_time", "reading", "sensory_play"]
        
        plan_data = {
            "baby_age": age_months,
            "developmental_stage": patterns.get("developmental_stage", "unknown"),
            "focus_areas": ["bonding", "development", "comfort"],
            "morning_activities": {},
            "afternoon_activities": {},
            "evening_activities": {},
            "feeding_schedule": patterns.get("feeding_schedule", {}),
            "sleep_schedule": patterns.get("sleep_schedule", {}),
            "reasoning": f"Age-appropriate activities for {age_months} months old baby"
        }
        
        # Fill activities based on available keys
        for period in ["morning", "afternoon", "evening"]:
            for i, activity in enumerate(activity_keys):
                if i < len(activities[period]):
                    plan_data[f"{period}_activities"][activity] = activities[period][i]
        
        return plan_data
    
    def _create_plan_file(self, target_date: datetime.date, plan_data: Dict[str, Any]) -> Path:
        """Create plan markdown file"""
        # Read template
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # Get memory summary
        memory_summary = memory_manager.get_summary(7)
        
        # Prepare replacements
        replacements = self._prepare_template_replacements(target_date, plan_data, memory_summary)
        
        # Apply replacements
        content = template
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
        
        # Write plan file
        plan_file = self.plan_dir / f"{target_date.strftime('%Y-%m-%d')}-plan.md"
        with open(plan_file, 'w') as f:
            f.write(content)
        
        return plan_file
    
    def _prepare_template_replacements(self, target_date: datetime.date, 
                                     plan_data: Dict[str, Any], 
                                     memory_summary: Dict[str, Any]) -> Dict[str, str]:
        """Prepare template replacements"""
        is_prenatal = plan_data.get("baby_age", -1) < 0
        
        replacements = {
            '{{DATE}}': target_date.strftime('%Y-%m-%d'),
            '{{DAY_OF_WEEK}}': target_date.strftime('%A'),
            '{{BABY_AGE}}': self._format_age_display(plan_data, target_date),
            '{{FOCUS_AREAS}}': ', '.join(plan_data['focus_areas']),
            '{{TIMESTAMP}}': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Add memory summary replacements
        replacements.update({
            '{{TOP_ENJOYED}}': ', '.join(memory_summary.get('most_enjoyed', [])[:3]),
            '{{TOP_DISLIKED}}': ', '.join(memory_summary.get('most_disliked', [])[:2]),
            '{{AVG_SLEEP}}': f"{memory_summary.get('avg_sleep', 0):.1f}",
            '{{FEEDING_TRENDS}}': ', '.join(memory_summary.get('feeding_patterns', [])[:2]),
            '{{NEW_SKILLS}}': ', '.join(memory_summary.get('new_skills', [])[:2]),
            '{{PROGRESSING_SKILLS}}': ', '.join(memory_summary.get('progressing_skills', [])[:2]),
            '{{MILESTONES}}': ', '.join(memory_summary.get('milestones', [])[:2]),
        })
        
        # Add activity replacements based on developmental stage
        if is_prenatal:
            replacements.update(self._get_prenatal_activity_replacements(plan_data))
        else:
            replacements.update(self._get_postnatal_activity_replacements(plan_data))
        
        # Add schedule replacements
        replacements.update(self._get_schedule_replacements(plan_data))
        
        return replacements
    
    def _format_age_display(self, plan_data: Dict[str, Any], target_date: datetime.date) -> str:
        """Format age display string"""
        if plan_data['baby_age'] > 0:
            return f"{plan_data['baby_age']} months ({plan_data.get('developmental_stage', 'unknown')} stage)"
        else:
            days_old = self._calculate_baby_age_days(target_date, patterns_manager.get_baby_patterns())
            return f"{days_old} days ({plan_data.get('developmental_stage', 'unknown')} stage)"
    
    def _get_prenatal_activity_replacements(self, plan_data: Dict[str, Any]) -> Dict[str, str]:
        """Get prenatal activity replacements"""
        return {
            '{{MORNING_TUMMY}}': plan_data['morning_activities'].get('belly_rubbing', 'Gentle belly rubbing'),
            '{{MORNING_READING}}': plan_data['morning_activities'].get('reading_stories', 'Read stories to baby'),
            '{{MORNING_PLAY}}': plan_data['morning_activities'].get('gentle_music', 'Play gentle music'),
            '{{AFTERNOON_TUMMY}}': plan_data['afternoon_activities'].get('mother_voice', 'Talk to baby with mother voice'),
            '{{AFTERNOON_READING}}': plan_data['afternoon_activities'].get('gentle_movement', 'Gentle movement exercises'),
            '{{AFTERNOON_SENSORY}}': plan_data['afternoon_activities'].get('relaxation', 'Relaxation time'),
            '{{EVENING_PLAY}}': plan_data['evening_activities'].get('calming_music', 'Calming music'),
            '{{EVENING_READING}}': plan_data['evening_activities'].get('bedtime_stories', 'Bedtime stories'),
            '{{EVENING_BEDTIME}}': plan_data['evening_activities'].get('mother_bonding', 'Mother-baby bonding'),
        }
    
    def _get_postnatal_activity_replacements(self, plan_data: Dict[str, Any]) -> Dict[str, str]:
        """Get postnatal activity replacements"""
        return {
            '{{MORNING_TUMMY}}': plan_data['morning_activities'].get('tummy_time', 'Tummy time'),
            '{{MORNING_READING}}': plan_data['morning_activities'].get('reading', 'Reading time'),
            '{{MORNING_PLAY}}': plan_data['morning_activities'].get('play', 'Play time'),
            '{{AFTERNOON_TUMMY}}': plan_data['afternoon_activities'].get('tummy_time', 'Tummy time'),
            '{{AFTERNOON_READING}}': plan_data['afternoon_activities'].get('reading', 'Reading time'),
            '{{AFTERNOON_SENSORY}}': plan_data['afternoon_activities'].get('sensory', 'Sensory play'),
            '{{EVENING_PLAY}}': plan_data['evening_activities'].get('play', 'Play time'),
            '{{EVENING_READING}}': plan_data['evening_activities'].get('reading', 'Reading time'),
            '{{EVENING_BEDTIME}}': plan_data['evening_activities'].get('bedtime', 'Bedtime routine'),
        }
    
    def _get_schedule_replacements(self, plan_data: Dict[str, Any]) -> Dict[str, str]:
        """Get schedule replacements"""
        schedule_keys = ['morning', 'midday', 'afternoon', 'evening', 'night']
        replacements = {}
        
        for key in schedule_keys:
            replacements[f'{{FEEDING_{key.upper()}}}'] = plan_data['feeding_schedule'].get(key, 'Regular feeding')
        
        sleep_keys = ['morning_nap', 'afternoon_nap', 'evening_nap', 'night_sleep']
        for key in sleep_keys:
            replacements[f'{{SLEEP_{key.upper()}}}'] = plan_data['sleep_schedule'].get(key, 'Regular sleep')
        
        return replacements
    
    def _send_plan_email(self, target_date: datetime.date, plan_file: Path):
        """Send plan via email"""
        try:
            from email_integration import BabyPlanEmailer
            emailer = BabyPlanEmailer()
            
            with open(plan_file, 'r') as f:
                plan_content = f.read()
            
            emailer.send_plan_email(target_date.strftime('%Y-%m-%d'), plan_content)
        except ImportError:
            log_warning(self.component_name, "Email integration not available")
        except Exception as e:
            log_error(self.component_name, e, "sending plan email")
    
    def _display_summary(self, plan_data: Dict[str, Any], target_date: datetime.date):
        """Display plan summary"""
        print("\nBaby Plan Summary:")
        
        if plan_data['baby_age'] == 0:
            days_old = self._calculate_baby_age_days(target_date, patterns_manager.get_baby_patterns())
            print(f"  Baby Age: {days_old} days ({plan_data.get('developmental_stage', 'unknown')} stage)")
        else:
            print(f"  Baby Age: {plan_data['baby_age']} months ({plan_data.get('developmental_stage', 'unknown')} stage)")
        
        print(f"  Focus: {', '.join(plan_data['focus_areas'])}")
        print(f"  Tummy Time: {len([k for k in plan_data.keys() if 'tummy' in k])} sessions")
        print(f"  Reading Time: {len([k for k in plan_data.keys() if 'reading' in k])} sessions")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "baby":
        date_arg = sys.argv[2] if len(sys.argv) > 2 else None
        age_arg = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else None
        
        generator = BabyPlanGenerator()
        success = generator.generate(date_arg, age_arg)
        
        if not success:
            sys.exit(1)
    else:
        print("Usage: python3 generate-baby-plan.py baby [YYYY-MM-DD] [age_months]")
        sys.exit(1)

if __name__ == "__main__":
    main()
