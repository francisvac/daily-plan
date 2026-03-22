#!/usr/bin/env python3
"""
ZeroClaw Baby Daily Plan Generator
Generates personalized daily plans for baby activities based on age and feedback
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

class BabyPlanGenerator:
    def __init__(self):
        self.plan_dir = Path.home() / "daily-plans"
        self.patterns_file = self.plan_dir / "patterns.json"
        self.template_file = self.plan_dir / "template.md"
        
    def ensure_directories(self):
        """Create necessary directories and files"""
        self.plan_dir.mkdir(exist_ok=True)
        
    def load_patterns(self):
        """Load existing baby patterns or create default"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return self.get_default_baby_patterns()
    
    def get_default_baby_patterns(self):
        """Return default baby patterns structure"""
        return {
            "baby_patterns": {
                "age_months": 6,  # Default age
                "favorite_activities": ["tummy_time", "reading", "sensory_play"],
                "sleep_schedule": {
                    "morning_nap": "9:00 AM",
                    "afternoon_nap": "1:00 PM", 
                    "evening_nap": "4:00 PM",
                    "night_bedtime": "7:30 PM"
                },
                "feeding_schedule": {
                    "morning": "7:00 AM",
                    "midday": "11:30 AM",
                    "afternoon": "3:30 PM",
                    "evening": "6:30 PM",
                    "night": "10:00 PM"
                },
                "preferred_tummy_times": ["morning", "afternoon"],
                "favorite_reading_times": ["morning", "before_naps", "bedtime"],
                "sleep_patterns": {
                    "best_sleep_duration": "2-3 hours",
                    "sleep_cues": ["rubbing eyes", "yawning", "fussy"],
                    "optimal_environment": ["dark", "quiet", "white_noise"]
                }
            }
        }
    
    def get_yesterday_feedback(self, target_date):
        """Extract feedback from yesterday's baby plan"""
        yesterday = target_date - timedelta(days=1)
        yesterday_plan = self.plan_dir / f"{yesterday.strftime('%Y-%m-%d')}-plan.md"
        
        if not yesterday_plan.exists():
            return None
            
        with open(yesterday_plan, 'r') as f:
            content = f.read()
            
        # Extract baby-specific feedback
        feedback = {
            "enjoyed_activities": self.extract_section(content, "What Baby Enjoyed Most ✅"),
            "disliked_activities": self.extract_section(content, "What Baby Didn't Like ❌"),
            "sleep_quality": self.extract_sleep_quality(content),
            "feeding_response": self.extract_feeding_response(content),
            "developmental_notes": self.extract_section(content, "Developmental Observations"),
            "activity_success": self.calculate_activity_success(content)
        }
        
        return feedback
    
    def extract_section(self, content, section_header):
        """Extract content from a specific section"""
        lines = content.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_header in line:
                in_section = True
                continue
            elif in_section and line.startswith('###'):
                break
            elif in_section and line.strip() and not line.startswith('-'):
                section_content.append(line.strip('- ').strip())
                
        return [c for c in section_content if c and c != 'TBD']
    
    def extract_sleep_quality(self, content):
        """Extract sleep quality rating"""
        import re
        sleep_pattern = r'\*\*Sleep Quality.*?\*\*.*?(\d+)'
        match = re.search(sleep_pattern, content)
        return int(match.group(1)) if match else 5
    
    def extract_feeding_response(self, content):
        """Extract feeding response information"""
        import re
        feeding_pattern = r'\*\*Feeding Response:\*\* (.+)'
        match = re.search(feeding_pattern, content)
        return match.group(1).strip() if match else "Normal"
    
    def calculate_baby_age(self, target_date):
        """Calculate baby's age in months based on birth date"""
        patterns = self.load_patterns()
        birth_date_str = patterns.get("baby_patterns", {}).get("birth_date")
        
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                # Calculate months difference
                years_diff = target_date.year - birth_date.year
                months_diff = target_date.month - birth_date.month
                
                total_months = years_diff * 12 + months_diff
                
                # Adjust for day of month
                if target_date.day < birth_date.day:
                    total_months -= 1
                
                return total_months
            except ValueError:
                print(f"Warning: Invalid birth date format: {birth_date_str}")
                return None
        return patterns.get("baby_patterns", {}).get("age_months", -1)
    
    def calculate_activity_success(self, content):
        try:
            # Try new baby template format first
            if '## 🍼 Daily Baby Activities' in content:
                todo_section = content.split('## 🍼 Daily Baby Activities')[1].split('## 😴 Sleep & Feeding Schedule')[0]
                completed_section = content.split('## ✅ Completed Activities')[1].split('## 📝 Baby Feedback Section')[0]
            else:
                # Fall back to old template format
                todo_section = content.split('## ✅ TODO Section')[1].split('## ✅ DONE Section')[0]
                completed_section = content.split('## ✅ DONE Section')[1].split('## 📝 FEEDBACK Section')[0]
            
            todo_count = todo_section.count('- [ ]')
            completed_count = completed_section.count('- [x]') + completed_section.count('- [X]')
            
            if todo_count == 0:
                return 0
            return (completed_count / todo_count) * 100
        except (IndexError, KeyError):
            return 50  # Default if parsing fails
    
    def get_age_appropriate_activities(self, age_months, patterns):
        """Get age-appropriate activities based on baby's age"""
        activities = {
            -1: {  # Prenatal
                "morning": ["belly_rubbing", "reading_stories", "gentle_music"],
                "afternoon": ["mother_voice", "gentle_movement", "relaxation"],
                "evening": ["calming_music", "bedtime_stories", "mother_bonding"]
            },
            0: {   # Newborn
                "morning": ["gentle_touch", "skin_to_skin", "voice_soothing"],
                "afternoon": ["swaddling", "white_noise", "gentle_rocking"],
                "evening": ["bath_time", "massage", "bedtime_routine"]
            },
            1: {   # 1 month
                "morning": ["tummy_time", "face_tracking", "gentle_play"],
                "afternoon": ["sensory_stimulation", "baby_massage", "outdoor_time"],
                "evening": ["quiet_time", "bedtime_routine", "gentle_soothing"]
            },
            3: {   # 3 months
                "morning": ["tummy_time", "reaching_toys", "sensory_play"],
                "afternoon": ["baby_gym", "mirror_play", "music_time"],
                "evening": ["reading_time", "quiet_play", "bedtime_routine"]
            },
            6: {   # 6 months
                "morning": ["tummy_time", "sitting_practice", "sensory_bins"],
                "afternoon": ["baby_gym", "reading_books", "music_classes"],
                "evening": ["quiet_play", "bedtime_stories", "gentle_soothing"]
            },
            9: {   # 9 months
                "morning": ["crawling_practice", "stacking_toys", "sensory_play"],
                "afternoon": ["pulling_up", "peek_a_boo", "music_time"],
                "evening": ["quiet_time", "reading_books", "bedtime_routine"]
            },
            12: {  # 12 months
                "morning": ["walking_practice", "stacking_blocks", "shape_sorters"],
                "afternoon": ["simple_puzzles", "music_toys", "outdoor_play"],
                "evening": ["quiet_time", "reading_books", "bedtime_routine"]
            }
        }
        
        # Find appropriate age range
        if age_months < 0:
            return activities[-1]
        elif age_months == 0:
            return activities[0]
        else:
            # Find the highest age key that's <= age_months
            valid_ages = [k for k in activities.keys() if k <= age_months and k >= 0]
            if valid_ages:
                age_range = max(valid_ages)
                return activities[age_range]
            else:
                return activities[0]  # Default to newborn
    
    def generate_baby_plan_with_zeroclaw(self, target_date, patterns, yesterday_feedback):
        """Generate baby plan using ZeroClaw AI"""
        day_name = target_date.strftime('%A')
        age_months = patterns["baby_patterns"]["age_months"]
        developmental_stage = patterns["baby_patterns"].get("developmental_stage", "unknown")
        
        # Build context for ZeroClaw
        context = f"Generate a personalized baby daily plan for {day_name}, {target_date.strftime('%Y-%m-%d')}."
        
        if age_months < 0:
            # Prenatal activities
            context += f"\n\nBaby is currently in the womb (prenatal stage), due on {patterns['baby_patterns'].get('birth_date', '2025-03-17')}."
            context += f"\nFocus on activities that bond with the baby and prepare for birth."
        elif age_months == 0:
            # Newborn
            context += f"\n\nBaby is a newborn (0 months old)."
            context += f"\nFocus on gentle activities, bonding, and basic care routines."
        else:
            # Postnatal
            context += f"\n\nBaby is {age_months} months old."
            context += f"\nDevelopmental stage: {developmental_stage}"
        
        if yesterday_feedback:
            context += f"\n\nBased on yesterday's feedback:\n"
            context += f"- Enjoyed: {', '.join(yesterday_feedback.get('enjoyed_activities', []))}\n"
            context += f"- Disliked: {', '.join(yesterday_feedback.get('disliked_activities', []))}\n"
            context += f"- Sleep quality: {yesterday_feedback.get('sleep_quality', 5)}/10\n"
        
        # Generate plan content
        try:
            result = subprocess.run([
                'zeroclaw', 'agent', '-m', context + f"""
                
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

Make activities specific, age-appropriate, and developmentally beneficial.
For prenatal stage: focus on mother-baby bonding, reading to baby, gentle movement, music.
For newborn stage: focus on gentle touch, bonding, basic care routines.
For older babies: focus on sensory development, motor skills, cognitive activities.
""", '--output-json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
            
        return self.generate_fallback_baby_plan(age_months, patterns, day_name)
    
    def generate_fallback_baby_plan(self, age_months, patterns, day_name):
        """Generate fallback baby plan when ZeroClaw is not available"""
        activities = self.get_age_appropriate_activities(age_months, patterns["baby_patterns"])
        
        # Adjust activity keys based on developmental stage
        if age_months < 0:
            # Prenatal activities
            activity_keys = ["belly_rubbing", "reading_stories", "gentle_music"]
        else:
            # Postnatal activities
            activity_keys = ["tummy_time", "reading", "sensory_play"]
        
        plan_data = {
            "baby_age": age_months,
            "developmental_stage": patterns["baby_patterns"].get("developmental_stage", "unknown"),
            "focus_areas": ["bonding", "development", "comfort"],
            "morning_activities": {},
            "afternoon_activities": {},
            "evening_activities": {},
            "feeding_schedule": {
                "morning": "Regular feeding",
                "midday": "Regular feeding", 
                "afternoon": "Regular feeding",
                "evening": "Regular feeding",
                "night": "Regular feeding"
            },
            "sleep_schedule": {
                "morning_nap": "Regular nap",
                "afternoon_nap": "Regular nap",
                "evening_nap": "Regular nap",
                "night_sleep": "Regular bedtime"
            },
            "reasoning": f"Age-appropriate activities for {age_months} months old baby"
        }
        
        # Fill activities based on available keys
        for period in ["morning", "afternoon", "evening"]:
            for i, activity in enumerate(activity_keys):
                if i < len(activities[period]):
                    plan_data[f"{period}_activities"][activity] = activities[period][i]
        
        return plan_data
    
    def get_memory_summary(self, target_date):
        """Get memory summary for last 7 days"""
        try:
            memory_file = self.plan_dir / "memory_entries.json"
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                
                # Get feedback from last 7 days
                cutoff_date = target_date - timedelta(days=7)
                summary = {
                    'most_enjoyed': [],
                    'most_disliked': [],
                    'avg_sleep': 0,
                    'feeding_patterns': [],
                    'new_skills': [],
                    'progressing_skills': [],
                    'milestones': []
                }
                
                sleep_ratings = []
                for key, entry in memory_data.items():
                    if key.startswith('baby_feedback_'):
                        entry_date = datetime.fromisoformat(entry['timestamp']).date()
                        if entry_date >= cutoff_date:
                            feedback = entry['feedback']
                            
                            # Collect data
                            summary['most_enjoyed'].extend(feedback.get('what_enjoyed', []))
                            summary['most_disliked'].extend(feedback.get('didnt_like', []))
                            
                            if feedback.get('sleep_quality'):
                                try:
                                    sleep_ratings.append(int(feedback['sleep_quality']))
                                except ValueError:
                                    pass
                            
                            summary['feeding_patterns'].extend(feedback.get('feeding_response', []))
                            summary['new_skills'].extend(feedback.get('developmental', []))
                
                # Process summary
                summary['most_enjoyed'] = list(set(summary['most_enjoyed']))[:5]
                summary['most_disliked'] = list(set(summary['most_disliked']))[:3]
                summary['avg_sleep'] = sum(sleep_ratings) / len(sleep_ratings) if sleep_ratings else 0
                summary['feeding_patterns'] = list(set(summary['feeding_patterns']))[:2]
                summary['new_skills'] = list(set(summary['new_skills']))[:2]
                
                return summary
            else:
                return {
                    'most_enjoyed': [],
                    'most_disliked': [],
                    'avg_sleep': 0,
                    'feeding_patterns': [],
                    'new_skills': [],
                    'progressing_skills': [],
                    'milestones': []
                }
                    
        except Exception as e:
            print(f"❌ Error reading memory file: {e}")
            return None
    
    def create_baby_plan_file(self, target_date, plan_data):
        """Create baby plan markdown file"""
        # Read template
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # Determine activity type based on developmental stage
        is_prenatal = plan_data.get("baby_age", -1) < 0
        
        # Get memory summary for last 7 days
        memory_summary = self.get_memory_summary(target_date)
        
        # Replace template variables
        replacements = {
            '{{DATE}}': target_date.strftime('%Y-%m-%d'),
            '{{DAY_OF_WEEK}}': target_date.strftime('%A'),
            '{{BABY_AGE}}': f"{plan_data['baby_age']} months ({plan_data.get('developmental_stage', 'unknown')} stage)" if plan_data['baby_age'] > 0 else f"{plan_data['baby_age'] * 30} days ({plan_data.get('developmental_stage', 'unknown')} stage)",
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
        
        # Handle activity replacements based on developmental stage
        if is_prenatal:
            # Prenatal activities
            replacements.update({
                '{{MORNING_TUMMY}}': plan_data['morning_activities'].get('belly_rubbing', 'Gentle belly rubbing'),
                '{{MORNING_READING}}': plan_data['morning_activities'].get('reading_stories', 'Read stories to baby'),
                '{{MORNING_PLAY}}': plan_data['morning_activities'].get('gentle_music', 'Play gentle music'),
                '{{AFTERNOON_TUMMY}}': plan_data['afternoon_activities'].get('mother_voice', 'Talk to baby with mother voice'),
                '{{AFTERNOON_READING}}': plan_data['afternoon_activities'].get('gentle_movement', 'Gentle movement exercises'),
                '{{AFTERNOON_SENSORY}}': plan_data['afternoon_activities'].get('relaxation', 'Relaxation time'),
                '{{EVENING_PLAY}}': plan_data['evening_activities'].get('calming_music', 'Calming music'),
                '{{EVENING_READING}}': plan_data['evening_activities'].get('bedtime_stories', 'Bedtime stories'),
                '{{EVENING_BEDTIME}}': plan_data['evening_activities'].get('mother_bonding', 'Mother-baby bonding'),
            })
        else:
            # Postnatal activities
            replacements.update({
                '{{MORNING_TUMMY}}': plan_data['morning_activities'].get('tummy_time', 'Tummy time'),
                '{{MORNING_READING}}': plan_data['morning_activities'].get('reading', 'Reading time'),
                '{{MORNING_PLAY}}': plan_data['morning_activities'].get('play', 'Play time'),
                '{{AFTERNOON_TUMMY}}': plan_data['afternoon_activities'].get('tummy_time', 'Tummy time'),
                '{{AFTERNOON_READING}}': plan_data['afternoon_activities'].get('reading', 'Reading time'),
                '{{AFTERNOON_SENSORY}}': plan_data['afternoon_activities'].get('sensory', 'Sensory play'),
                '{{EVENING_PLAY}}': plan_data['evening_activities'].get('play', 'Play time'),
                '{{EVENING_READING}}': plan_data['evening_activities'].get('reading', 'Reading time'),
                '{{EVENING_BEDTIME}}': plan_data['evening_activities'].get('bedtime', 'Bedtime routine'),
            })
        
        # Add schedule replacements
        schedule_keys = ['morning', 'midday', 'afternoon', 'evening', 'night']
        for key in schedule_keys:
            replacements[f'{{FEEDING_{key.upper()}}}'] = plan_data['feeding_schedule'].get(key, 'Regular feeding')
        
        sleep_keys = ['morning_nap', 'afternoon_nap', 'evening_nap', 'night_sleep']
        for key in sleep_keys:
            replacements[f'{{SLEEP_{key.upper()}}}'] = plan_data['sleep_schedule'].get(key, 'Regular sleep')
        
        # Apply replacements
        content = template
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
        
        # Write plan file
        plan_file = self.plan_dir / f"{target_date.strftime('%Y-%m-%d')}-plan.md"
        with open(plan_file, 'w') as f:
            f.write(content)
        
        return plan_file
    
    def generate(self, date_str=None, baby_age_months=None):
        """Main generation method"""
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        
        print(f"=== ZeroClaw Baby Daily Plan Generator ===")
        print(f"Generating baby plan for: {target_date}")
        print()
        
        # Load patterns and feedback
        patterns = self.load_patterns()
        
        # Calculate baby age (from birth date or provided age)
        if baby_age_months:
            # Use provided age and update patterns
            patterns["baby_patterns"]["age_months"] = baby_age_months
            self.save_patterns(patterns)
            baby_age = baby_age_months
        else:
            # Calculate from birth date
            baby_age = self.calculate_baby_age(target_date)
            if baby_age is not None:
                patterns["baby_patterns"]["age_months"] = baby_age
                self.save_patterns(patterns)
            else:
                baby_age = patterns.get("baby_patterns", {}).get("age_months", -1)
             
        yesterday_feedback = self.get_yesterday_feedback(target_date)
        
        # Generate plan content
        print(f"Generating age-appropriate baby activities for {baby_age} months ({patterns['baby_patterns'].get('developmental_stage', 'unknown')} stage)...")
        plan_data = self.generate_baby_plan_with_zeroclaw(target_date, patterns, yesterday_feedback)
        
        # Create plan file
        plan_file = self.create_baby_plan_file(target_date, plan_data)
        
        print(f"✅ Baby plan generated: {plan_file}")
        print()
        print("Baby Plan Summary:")
        print(f"  Baby Age: {plan_data['baby_age']} months")
        print(f"  Focus: {', '.join(plan_data['focus_areas'])}")
        print(f"  Tummy Time: {len([k for k in plan_data.keys() if 'tummy' in k])} sessions")
        print(f"  Reading Time: {len([k for k in plan_data.keys() if 'reading' in k])} sessions")
        if yesterday_feedback:
            print(f"  Based on yesterday's {yesterday_feedback.get('activity_success', 0):.1f}% activity success")
        print()
        print("Next steps:")
        print("  1. Review your baby's daily plan")
        print("  2. Complete activities throughout the day")
        print("  3. Run 'daily-plan feedback' in the evening")
        print("  4. System will learn and improve tomorrow's plan")
        
        # Get historical feedback
        historical_feedback = self.get_historical_feedback_from_memory(target_date)
        if historical_feedback:
            print()
            print(historical_feedback)
        
        # Send email if configured
        self.send_email_if_configured(target_date, plan_file)
    
    def get_historical_feedback_from_memory(self, target_date):
        """Query historical feedback from memory file"""
        try:
            memory_file = self.plan_dir / "memory_entries.json"
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                
                # Get feedback from last 30 days
                cutoff_date = target_date - timedelta(days=30)
                historical_feedback = []
                
                for key, entry in memory_data.items():
                    if key.startswith('baby_feedback_'):
                        entry_date = datetime.fromisoformat(entry['timestamp']).date()
                        if entry_date >= cutoff_date:
                            historical_feedback.append(entry['feedback'])
                
                if historical_feedback:
                    # Create summary
                    enjoyed_activities = []
                    disliked_activities = []
                    sleep_ratings = []
                    
                    for feedback in historical_feedback:
                        enjoyed_activities.extend(feedback.get('what_enjoyed', []))
                        disliked_activities.extend(feedback.get('didnt_like', []))
                        sleep_ratings.append(int(feedback.get('sleep_quality', '5')))
                    
                    avg_sleep = sum(sleep_ratings) / len(sleep_ratings) if sleep_ratings else 5
                    
                    summary = f"""
Historical Feedback Summary (Last 30 Days):
- Most Enjoyed Activities: {list(set(enjoyed_activities))[:3]}
- Common Dislikes: {list(set(disliked_activities))[:3]}
- Average Sleep Quality: {avg_sleep:.1f}/10
- Total Feedback Entries: {len(historical_feedback)}

Key Patterns:
- Baby consistently enjoys: {', '.join(list(set(enjoyed_activities))[:2])}
- Baby dislikes: {', '.join(list(set(disliked_activities))[:2])}
- Sleep trends: {'Good' if avg_sleep >= 7 else 'Needs attention'}
"""
                    return summary.strip()
                else:
                    return "No historical feedback available in the last 30 days."
                    
        except Exception as e:
            print(f"❌ Error reading memory file: {e}")
            return None
    
    def send_email_if_configured(self, target_date, plan_file):
        """Send email if email is configured"""
        try:
            email_script = self.plan_dir / "email_integration.py"
            if email_script.exists():
                # Check if email is configured
                config_file = self.plan_dir / "email_config.json"
                if config_file.exists():
                    print()
                    print("📧 Sending plan via email...")
                    import subprocess
                    result = subprocess.run([
                        'python3', str(email_script), 'send', target_date.strftime('%Y-%m-%d')
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        print(result.stdout.strip())
                    else:
                        print(f"Email sending failed: {result.stderr.strip()}")
        except Exception as e:
            print(f"Email error: {e}")
    
    def save_patterns(self, patterns):
        """Save patterns to file"""
        with open(self.patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)

if __name__ == "__main__":
    generator = BabyPlanGenerator()
    generator.ensure_directories()
    
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    age_arg = None
    if len(sys.argv) > 2:
        try:
            age_arg = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid age '{sys.argv[2]}', using saved age")
            age_arg = None
    
    generator.generate(date_arg, age_arg)
