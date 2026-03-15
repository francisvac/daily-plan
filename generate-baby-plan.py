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
    
    def calculate_activity_success(self, content):
        """Calculate baby activity success rate"""
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
            0: {  # 0-3 months
                "tummy_time": ["2-3 minutes on playmat", "on parent's chest", "during diaper changes"],
                "reading": ["high contrast books", "black and white cards", "face-to-face reading"],
                "play": ["gentle mobile watching", "soft rattle sounds", "mirrored play"]
            },
            3: {  # 3-6 months
                "tummy_time": ["5-10 minutes with toys", "propped on pillows", "during playtime"],
                "reading": ["board books", "texture books", "rhyming stories"],
                "play": ["activity gym", "sensory toys", "peek-a-boo games"]
            },
            6: {  # 6-9 months
                "tummy_time": ["10-15 minutes with reaching", "ball rolling", "toy exploration"],
                "reading": ["lift-the-flap books", "animal books", "sound books"],
                "play": ["sitting games", "crawling practice", "block stacking"]
            },
            9: {  # 9-12 months
                "tummy_time": ["crawling games", "pulling up practice", "cruising activities"],
                "reading": ["picture books", "story books", "interactive books"],
                "play": ["standing practice", "simple puzzles", "music making"]
            }
        }
        
        # Find appropriate age range
        age_range = max([k for k in activities.keys() if age_months >= k])
        return activities[age_range]
    
    def generate_baby_plan_with_zeroclaw(self, target_date, patterns, yesterday_feedback):
        """Generate baby plan using ZeroClaw AI"""
        day_name = target_date.strftime('%A')
        age_months = patterns["baby_patterns"]["age_months"]
        
        # Build context for ZeroClaw
        context = f"Generate a personalized baby daily plan for {day_name}, {target_date.strftime('%Y-%m-%d')}."
        context += f"\n\nBaby is {age_months} months old."
        
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
  "focus_areas": ["development", "sensory", "bonding"],
  "morning_activities": {{
    "tummy_time": "Specific age-appropriate tummy time activity",
    "reading": "Age-appropriate reading activity", 
    "play": "Interactive play activity"
  }},
  "afternoon_activities": {{
    "tummy_time": "Different tummy time activity",
    "reading": "Different reading activity",
    "sensory": "Sensory development activity"
  }},
  "evening_activities": {{
    "play": "Gentle evening activity",
    "reading": "Bedtime reading",
    "bedtime": "Calming bedtime routine"
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
  "reasoning": "Why these activities are perfect for this age and routine"
}}

Make activities specific, age-appropriate, and developmentally beneficial.
""", '--output-json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
            
        return self.generate_fallback_baby_plan(age_months, patterns, day_name)
    
    def generate_fallback_baby_plan(self, age_months, patterns, day_name):
        """Generate basic baby plan without ZeroClaw"""
        activities = self.get_age_appropriate_activities(age_months, patterns["baby_patterns"])
        
        return {
            "baby_age": age_months,
            "focus_areas": ["development", "sensory", "bonding"],
            "morning_activities": {
                "tummy_time": activities["tummy_time"][0],
                "reading": activities["reading"][0],
                "play": activities["play"][0]
            },
            "afternoon_activities": {
                "tummy_time": activities["tummy_time"][1],
                "reading": activities["reading"][1],
                "sensory": activities["play"][1]
            },
            "evening_activities": {
                "play": "Gentle play with soft toys",
                "reading": "Bedtime story with cuddles",
                "bedtime": "Bath, massage, and lullaby routine"
            },
            "feeding_schedule": {
                "morning": "7:00 AM - Alert and hungry",
                "midday": "11:30 AM - After morning activities",
                "afternoon": "3:30 PM - Post-nap feeding",
                "evening": "6:30 PM - Before dinner routine",
                "night": "10:00 PM - Dream feed if needed"
            },
            "sleep_schedule": {
                "morning_nap": "9:00 AM - 2 hours",
                "afternoon_nap": "1:00 PM - 2.5 hours", 
                "evening_nap": "4:00 PM - 1 hour",
                "night_sleep": "7:30 PM - Until morning"
            },
            "reasoning": f"Age-appropriate activities for {age_months}-month-old baby on {day_name}"
        }
    
    def create_baby_plan_file(self, target_date, plan_data):
        """Create baby plan markdown file"""
        # Read template
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # Replace template variables
        replacements = {
            '{{DATE}}': target_date.strftime('%Y-%m-%d'),
            '{{DAY_OF_WEEK}}': target_date.strftime('%A'),
            '{{TIMESTAMP}}': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '{{BABY_AGE}}': f"{plan_data['baby_age']} months",
            '{{FOCUS_AREAS}}': ', '.join(plan_data['focus_areas']),
            
            # Morning activities
            '{{MORNING_TUMMY}}': plan_data['morning_activities']['tummy_time'],
            '{{MORNING_READING}}': plan_data['morning_activities']['reading'],
            '{{MORNING_PLAY}}': plan_data['morning_activities']['play'],
            
            # Afternoon activities
            '{{AFTERNOON_TUMMY}}': plan_data['afternoon_activities']['tummy_time'],
            '{{AFTERNOON_READING}}': plan_data['afternoon_activities']['reading'],
            '{{AFTERNOON_SENSORY}}': plan_data['afternoon_activities']['sensory'],
            
            # Evening activities
            '{{EVENING_PLAY}}': plan_data['evening_activities']['play'],
            '{{EVENING_READING}}': plan_data['evening_activities']['reading'],
            '{{BEDTIME_ROUTINE}}': plan_data['evening_activities']['bedtime'],
            
            # Feeding schedule
            '{{MORNING_FEEDING}}': plan_data['feeding_schedule']['morning'],
            '{{MIDDAY_FEEDING}}': plan_data['feeding_schedule']['midday'],
            '{{AFTERNOON_FEEDING}}': plan_data['feeding_schedule']['afternoon'],
            '{{EVENING_FEEDING}}': plan_data['feeding_schedule']['evening'],
            '{{NIGHT_FEEDING}}': plan_data['feeding_schedule']['night'],
            
            # Sleep schedule
            '{{MORNING_NAP}}': plan_data['sleep_schedule']['morning_nap'],
            '{{AFTERNOON_NAP}}': plan_data['sleep_schedule']['afternoon_nap'],
            '{{EVENING_NAP}}': plan_data['sleep_schedule']['evening_nap'],
            '{{NIGHT_SLEEP}}': plan_data['sleep_schedule']['night_sleep'],
        }
        
        # Apply replacements
        content = template
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        # Fill remaining placeholders
        import re
        content = re.sub(r'\{\{[^}]+\}\}', 'TBD', content)
        
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
        
        # Update baby age if provided
        if baby_age_months:
            patterns["baby_patterns"]["age_months"] = baby_age_months
            self.save_patterns(patterns)
            
        yesterday_feedback = self.get_yesterday_feedback(target_date)
        
        # Generate plan content
        print("Generating age-appropriate baby activities...")
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
