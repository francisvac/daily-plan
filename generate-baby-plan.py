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
    DEVELOPMENT_STAGES, TEMPLATE_PLACEHOLDERS,
    ERROR_MESSAGES, SUCCESS_MESSAGES, ConfigManager
)
from base_classes import BabyPlannerBase, memory_manager, patterns_manager
from logger import get_logger, log_error, log_success, log_warning
from optimized_llm_generator import optimized_llm_generator

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
        """Get age-appropriate activities (fallback method)"""
        from config import AGE_ACTIVITIES_LEGACY
        
        if age_months < 0:
            return AGE_ACTIVITIES_LEGACY[-1]
        elif age_months == 0:
            return AGE_ACTIVITIES_LEGACY[0]
        else:
            # Find the highest age key that's <= age_months
            valid_ages = [k for k in AGE_ACTIVITIES_LEGACY.keys() if k <= age_months and k >= 0]
            if valid_ages:
                age_range = max(valid_ages)
                return AGE_ACTIVITIES_LEGACY[age_range]
            else:
                return AGE_ACTIVITIES_LEGACY[0]
    
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
        """Create plan markdown file using optimized LLM-generated template"""
        
        # Get optimized LLM-generated template
        age_months = plan_data.get("baby_age", 0)
        developmental_stage = plan_data.get("developmental_stage", "newborn")
        
        dynamic_template = optimized_llm_generator.generate_daily_template(
            target_date, age_months, developmental_stage
        )
        
        # Generate plan content from template
        plan_content = self._generate_content_from_template(dynamic_template, target_date, plan_data)
        
        # Write plan file
        plan_file = self.plan_dir / f"{target_date.strftime('%Y-%m-%d')}-plan.md"
        with open(plan_file, 'w') as f:
            f.write(plan_content)
        
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
    
    def _generate_content_from_template(self, template: Dict[str, Any], 
                                    target_date: datetime.date, 
                                    plan_data: Dict[str, Any]) -> str:
        """Generate markdown content from LLM template"""
        
        # Build header
        content = f"""# Baby Daily Plan - {target_date.strftime('%Y-%m-%d')}

## 👶 Baby Context
**Date:** {target_date.strftime('%Y-%m-%d')}  
**Day:** {target_date.strftime('%A')}  
**Baby Age:** {self._format_age_display(plan_data, target_date)}  
**Focus:** {', '.join(plan_data.get('focus_areas', ['bonding', 'development', 'comfort']))}

---

"""
        
        # Add template sections
        template_sections = template.get("template_sections", {})
        
        for section_key, section_data in template_sections.items():
            content += f"## {section_data.get('title', section_key.replace('_', ' ').title())}\n\n"
            
            activities = section_data.get("activities", [])
            for activity in activities:
                content += f"- [ ] **{activity.get('name', 'Activity').title().replace('_', ' ')}**: {activity.get('description', 'Age-appropriate activity')}\n"
                
                # Add duration if available
                if activity.get('duration'):
                    content += f"  - **Duration:** {activity['duration']}\n"
                
                # Add focus area
                if activity.get('focus_area'):
                    content += f"  - **Focus:** {activity['focus_area']}\n"
                
                # Add tips
                tips = activity.get('tips', [])
                if tips:
                    content += f"  - **Tips:** {', '.join(tips)}\n"
                
                # Add adaptations
                adaptations = activity.get('adaptations', [])
                if adaptations:
                    content += f"  - **Adaptations:** {', '.join(adaptations)}\n"
                
                content += "\n"
        
        # Add schedule section
        content += "## 😴 Sleep & Feeding Schedule\n\n"
        
        schedule_adjustments = template.get("schedule_adjustments", {})
        
        # Feeding times
        content += "### Feeding Times\n"
        feeding_times = schedule_adjustments.get("feeding_times", {})
        for time_key, time_value in feeding_times.items():
            content += f"- [ ] **{time_key.title()} Feeding:** {time_value}\n"
        content += "\n"
        
        # Sleep times
        content += "### Sleep Schedule\n"
        sleep_times = schedule_adjustments.get("sleep_times", {})
        for time_key, time_value in sleep_times.items():
            content += f"- [ ] **{time_key.title()}**: {time_value}\n"
        content += "\n"
        
        # Add focus areas and developmental targets
        content += "## 🎯 Today's Focus\n\n"
        
        focus_areas = template.get("focus_areas", [])
        if focus_areas:
            content += f"**Primary Focus Areas:** {', '.join(focus_areas)}\n\n"
        
        developmental_targets = template.get("developmental_targets", [])
        if developmental_targets:
            content += f"**Developmental Targets:** {', '.join(developmental_targets)}\n\n"
        
        # Add parenting tips
        parenting_tips = template.get("parenting_tips", [])
        if parenting_tips:
            content += "## 💡 Parenting Tips\n\n"
            for tip in parenting_tips:
                content += f"- {tip}\n"
            content += "\n"
        
        # Add adaptation notes
        adaptation_notes = template.get("adaptation_notes")
        if adaptation_notes:
            content += f"## 🔄 Adaptation Notes\n\n{adaptation_notes}\n\n"
        
        # Add feedback sections
        content += """## ✅ Completed Activities
*Fill this section throughout the day*

### Baby Activities Completed
- [ ] Activity 1 - Notes about baby's response
- [ ] Activity 2 - Notes about baby's response
- [ ] Activity 3 - Notes about baby's response

### Sleep & Feeding Completed
- [ ] Morning Feeding - Amount, duration, baby's response
- [ ] Midday Feeding - Amount, duration, baby's response
- [ ] Afternoon Feeding - Amount, duration, baby's response
- [ ] Evening Feeding - Amount, duration, baby's response
- [ ] Night Feeding - Amount, duration, baby's response

- [ ] Morning Nap - Duration, quality, notes
- [ ] Afternoon Nap - Duration, quality, notes
- [ ] Evening Nap - Duration, quality, notes
- [ ] Night Sleep - Bedtime routine, duration, notes

---

## 📝 Baby Feedback Section

### What Baby Enjoyed Most ✅
- [ ] Activity 1 - Specific details about what baby loved
- [ ] Activity 2 - Specific details about what baby loved
- [ ] Activity 3 - Specific details about what baby loved

### What Baby Didn't Like ❌
- [ ] Activity 1 - What baby disliked and possible reasons
- [ ] Activity 2 - What baby disliked and possible reasons

### Sleep Quality (1-10)
**Sleep Quality:** TBD / 10

### Feeding Response
**Feeding Response:** TBD

### Fussy Periods
- [ ] Time - Duration - Possible triggers - Soothing techniques that worked

### Happy Periods
- [ ] Time - Duration - Activities or conditions that made baby happy

### Developmental Observations
- [ ] New skills or attempts
- [ ] Changes in awareness or responsiveness
- [ ] Physical development milestones
- [ ] Communication developments

---

## 🌟 Special Moments & Journal Notes

### Daily Highlights
- [ ] Special moment 1 - Description and emotional impact
- [ ] Special moment 2 - Description and emotional impact
- [ ] Special moment 3 - Description and emotional impact

### Parent Journal Notes 📔
- [ ] {{PARENT_JOURNAL_1}}
- [ ] {{PARENT_JOURNAL_2}}
- [ ] {{PARENT_JOURNAL_3}}

---

## 📊 Memory & Pattern Summary

### Recent Patterns (Last 7 Days)
- **Top Enjoyed Activities:** {{TOP_ENJOYED}}
- **Common Dislikes:** {{TOP_DISLIKED}}
- **Average Sleep Quality:** {{AVG_SLEEP}}/10
- **Feeding Trends:** {{FEEDING_TRENDS}}

### Developmental Progress
- **New Skills:** {{NEW_SKILLS}}
- **Progressing Skills:** {{PROGRESSING_SKILLS}}
- **Recent Milestones:** {{MILESTONES}}

---

## 📧 Email Commands

Reply to this email with these commands for instant memory access:

📊 **Memory Retrieval:**
- `memory today` - Get today's complete journal entry
- `memory week` - Get last 7 days summary with trends
- `memory month` - Get last 30 days comprehensive summary
- `memory search [keyword]` - Search all journal entries

📝 **Quick Actions:**
- `feedback [observation]` - Add quick feedback note
- `journal [note]` - Add journal entry to today's record
- `patterns` - Get current baby patterns and preferences
- `help` - Show all available commands

💡 **Examples:**
- `memory week`
- `memory search sleep`
- `journal Baby had lots of smiles during tummy time`
- `feedback Loved the gentle music today`

---

📅 **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 **Powered by:** ZeroClaw Baby Daily Planning System
🧠 **Template:** LLM-Generated with Feedback Adaptation
"""
        
        return content
    
    def _format_age_display(self, plan_data: Dict[str, Any], target_date: datetime.date) -> str:
        """Format age display string"""
        if plan_data['baby_age'] > 0:
            return f"{plan_data['baby_age']} months ({plan_data.get('developmental_stage', 'unknown')} stage)"
        else:
            days_old = self._calculate_baby_age_days(target_date, patterns_manager.get_baby_patterns())
            return f"{days_old} days ({plan_data.get('developmental_stage', 'unknown')} stage)"
    
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
        """Display plan summary with performance metrics"""
        print("\nBaby Plan Summary:")
        
        if plan_data['baby_age'] == 0:
            days_old = self._calculate_baby_age_days(target_date, patterns_manager.get_baby_patterns())
            print(f"  Baby Age: {days_old} days ({plan_data.get('developmental_stage', 'unknown')} stage)")
        else:
            print(f"  Baby Age: {plan_data['baby_age']} months ({plan_data.get('developmental_stage', 'unknown')} stage)")
        
        print(f"  Focus: {', '.join(plan_data['focus_areas'])}")
        print(f"  Tummy Time: {len([k for k in plan_data.keys() if 'tummy' in k])} sessions")
        print(f"  Reading Time: {len([k for k in plan_data.keys() if 'reading' in k])} sessions")
        
        # Display LLM performance metrics
        performance_report = optimized_llm_generator.get_performance_report()
        print(f"\n🤖 LLM Performance:")
        print(f"  Performance Level: {performance_report['current_level']}")
        print(f"  Success Rate: {performance_report['success_rate']}")
        print(f"  Response Time: {performance_report['avg_response_time']}")
        print(f"  Cache Size: {performance_report['cache_size']} templates")
        
        if performance_report['recommendations']:
            print(f"  Recommendations:")
            for rec in performance_report['recommendations']:
                print(f"    - {rec}")
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance report"""
        return {
            "llm_performance": optimized_llm_generator.get_performance_report(),
            "memory_usage": memory_manager.get_summary(30),
            "patterns_status": patterns_manager.get_baby_patterns(),
            "system_health": {
                "cache_status": "healthy" if len(optimized_llm_generator.template_cache) > 0 else "empty",
                "memory_status": "healthy" if len(memory_manager._memory_cache) > 0 else "empty",
                "patterns_status": "loaded"
            }
        }

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "baby":
        date_arg = sys.argv[2] if len(sys.argv) > 2 else None
        age_arg = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else None
        
        generator = BabyPlanGenerator()
        success = generator.generate(date_arg, age_arg)
        
        if not success:
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "performance":
        generator = BabyPlanGenerator()
        performance = generator.get_system_performance()
        
        print("🔍 ZeroClaw Baby Planner - Performance Report")
        print("=" * 50)
        
        llm_perf = performance["llm_performance"]
        print(f"\n🤖 LLM Performance:")
        print(f"  Level: {llm_perf['current_level']}")
        print(f"  Success Rate: {llm_perf['success_rate']}")
        print(f"  Response Time: {llm_perf['avg_response_time']}")
        print(f"  Total Requests: {llm_perf['total_requests']}")
        print(f"  Cache Size: {llm_perf['cache_size']}")
        
        if llm_perf['recommendations']:
            print(f"  Recommendations:")
            for rec in llm_perf['recommendations']:
                print(f"    - {rec}")
        
        memory = performance["memory_usage"]
        print(f"\n📊 Memory Usage:")
        print(f"  Total Entries: {memory['total_entries']}")
        print(f"  Most Enjoyed: {len(memory['most_enjoyed'])}")
        print(f"  Disliked: {len(memory['most_disliked'])}")
        print(f"  Avg Sleep: {memory['avg_sleep']:.1f}/10")
        
        health = performance["system_health"]
        print(f"\n🏥 System Health:")
        for component, status in health.items():
            print(f"  {component.replace('_', ' ').title()}: {status}")
        
    else:
        print("Usage:")
        print("  python3 generate-baby-plan.py baby [YYYY-MM-DD] [age_months]")
        print("  python3 generate-baby-plan.py performance")
        sys.exit(1)

if __name__ == "__main__":
    main()
