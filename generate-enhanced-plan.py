#!/usr/bin/env python3
"""
ZeroClaw Enhanced Daily Plan Generator
Generates personalized daily plans using ZeroClaw AI when available
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

class DailyPlanGenerator:
    def __init__(self):
        self.plan_dir = Path.home() / "daily-plans"
        self.patterns_file = self.plan_dir / "patterns.json"
        self.template_file = self.plan_dir / "template.md"
        
    def ensure_directories(self):
        """Create necessary directories and files"""
        self.plan_dir.mkdir(exist_ok=True)
        
    def load_patterns(self):
        """Load existing patterns or create default"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return self.get_default_patterns()
    
    def get_default_patterns(self):
        """Return default patterns structure"""
        return {
            "patterns": {
                "energy_levels": {
                    "morning_peak": 9,
                    "afternoon_peak": 2,
                    "evening_peak": 7,
                    "overall_pattern": "morning_person"
                },
                "task_preferences": {
                    "preferred_task_types": ["deep_work", "learning"],
                    "avoid_task_types": ["maintenance"],
                    "complex_task_times": ["morning"],
                    "quick_task_times": ["afternoon"]
                },
                "completion_patterns": {
                    "optimal_task_count": 5,
                    "best_task_duration": 90,
                    "break_frequency": 120
                }
            }
        }
    
    def get_yesterday_feedback(self, target_date):
        """Extract feedback from yesterday's plan"""
        yesterday = target_date - timedelta(days=1)
        yesterday_plan = self.plan_dir / f"{yesterday.strftime('%Y-%m-%d')}-plan.md"
        
        if not yesterday_plan.exists():
            return None
            
        with open(yesterday_plan, 'r') as f:
            content = f.read()
            
        # Extract feedback sections
        feedback = {
            "what_worked": self.extract_section(content, "What Worked Well ✅"),
            "what_didnt_work": self.extract_section(content, "What Didn't Work ❌"),
            "energy_levels": self.extract_energy_levels(content),
            "completion_rate": self.calculate_completion_rate(content)
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
    
    def extract_energy_levels(self, content):
        """Extract energy levels from feedback"""
        import re
        energy_pattern = r'\*\*(\w+) Energy.*?\*\*.*?(\d+)'
        matches = re.findall(energy_pattern, content)
        return {time: int(level) for time, level in matches}
    
    def calculate_completion_rate(self, content):
        """Calculate task completion rate"""
        todo_section = content.split('## ✅ TODO Section')[1].split('## ✅ DONE Section')[0]
        done_section = content.split('## ✅ DONE Section')[1].split('## 📝 FEEDBACK Section')[0]
        
        todo_count = todo_section.count('- [ ]')
        done_count = done_section.count('- [x]') + done_section.count('- [X]')
        
        if todo_count == 0:
            return 0
        return (done_count / todo_count) * 100
    
    def generate_plan_with_zeroclaw(self, target_date, patterns, yesterday_feedback):
        """Generate plan using ZeroClaw AI"""
        day_name = target_date.strftime('%A')
        
        # Build context for ZeroClaw
        context = f"Generate a personalized daily plan for {day_name}, {target_date.strftime('%Y-%m-%d')}."
        
        if yesterday_feedback:
            context += f"\n\nBased on yesterday's feedback:\n"
            context += f"- What worked: {', '.join(yesterday_feedback.get('what_worked', []))}\n"
            context += f"- What didn't work: {', '.join(yesterday_feedback.get('what_didnt_work', []))}\n"
            context += f"- Completion rate: {yesterday_feedback.get('completion_rate', 0):.1f}%\n"
        
        context += f"\n\nCurrent patterns show: {patterns['patterns']['energy_levels']['overall_pattern']} pattern, "
        context += f"optimal task count: {patterns['patterns']['completion_patterns'].get('optimal_task_count', 5)}"
        
        # Generate plan content
        try:
            result = subprocess.run([
                'zeroclaw', 'agent', '-m', context + """
                
Generate a daily plan with this JSON structure:
{
  "priority_level": "High/Medium/Low",
  "focus_areas": ["area1", "area2"],
  "morning_tasks": ["Specific task 1", "Specific task 2", "Quick win task"],
  "afternoon_tasks": ["Deep work task", "Collaboration task", "Maintenance task"],
  "evening_tasks": ["Learning task", "Planning task", "Reflection task"],
  "reasoning": "Brief explanation of why this plan fits the user"
}

Make tasks specific, actionable, and realistic for the day of week.
""", '--output-json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
            
        return self.generate_fallback_plan(day_name, patterns)
    
    def generate_fallback_plan(self, day_name, patterns):
        """Generate basic plan without ZeroClaw"""
        return {
            "priority_level": "Medium",
            "focus_areas": ["Productivity", "Learning"],
            "morning_tasks": [
                "Review and prioritize today's tasks",
                "Work on most important project",
                "Quick administrative task"
            ],
            "afternoon_tasks": [
                "Deep work session",
                "Team collaboration/check-in",
                "Email and communication"
            ],
            "evening_tasks": [
                "Learning or skill development",
                "Plan tomorrow's priorities",
                "Daily reflection"
            ],
            "reasoning": f"Standard {day_name} plan based on typical productivity patterns"
        }
    
    def create_plan_file(self, target_date, plan_data):
        """Create the plan markdown file"""
        # Read template
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # Replace template variables
        replacements = {
            '{{DATE}}': target_date.strftime('%Y-%m-%d'),
            '{{DAY_OF_WEEK}}': target_date.strftime('%A'),
            '{{TIMESTAMP}}': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '{{PRIORITY_LEVEL}}': plan_data['priority_level'],
            '{{FOCUS_AREAS}}': ', '.join(plan_data['focus_areas']),
            '{{MORNING_TASK_1}}': plan_data['morning_tasks'][0] if len(plan_data['morning_tasks']) > 0 else '',
            '{{MORNING_TASK_2}}': plan_data['morning_tasks'][1] if len(plan_data['morning_tasks']) > 1 else '',
            '{{MORNING_TASK_3}}': plan_data['morning_tasks'][2] if len(plan_data['morning_tasks']) > 2 else '',
            '{{AFTERNOON_TASK_1}}': plan_data['afternoon_tasks'][0] if len(plan_data['afternoon_tasks']) > 0 else '',
            '{{AFTERNOON_TASK_2}}': plan_data['afternoon_tasks'][1] if len(plan_data['afternoon_tasks']) > 1 else '',
            '{{AFTERNOON_TASK_3}}': plan_data['afternoon_tasks'][2] if len(plan_data['afternoon_tasks']) > 2 else '',
            '{{EVENING_TASK_1}}': plan_data['evening_tasks'][0] if len(plan_data['evening_tasks']) > 0 else '',
            '{{EVENING_TASK_2}}': plan_data['evening_tasks'][1] if len(plan_data['evening_tasks']) > 1 else '',
            '{{EVENING_TASK_3}}': plan_data['evening_tasks'][2] if len(plan_data['evening_tasks']) > 2 else '',
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
    
    def generate(self, date_str=None):
        """Main generation method"""
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        
        print(f"=== ZeroClaw Enhanced Daily Plan Generator ===")
        print(f"Generating plan for: {target_date}")
        print()
        
        # Load patterns and feedback
        patterns = self.load_patterns()
        yesterday_feedback = self.get_yesterday_feedback(target_date)
        
        # Generate plan content
        print("Generating personalized plan content...")
        plan_data = self.generate_plan_with_zeroclaw(target_date, patterns, yesterday_feedback)
        
        # Create plan file
        plan_file = self.create_plan_file(target_date, plan_data)
        
        print(f"✅ Plan generated: {plan_file}")
        print()
        print("Plan Summary:")
        print(f"  Priority: {plan_data['priority_level']}")
        print(f"  Focus: {', '.join(plan_data['focus_areas'])}")
        print(f"  Total tasks: {len(plan_data['morning_tasks']) + len(plan_data['afternoon_tasks']) + len(plan_data['evening_tasks'])}")
        if yesterday_feedback:
            print(f"  Based on yesterday's {yesterday_feedback.get('completion_rate', 0):.1f}% completion rate")
        print()
        print("Next steps:")
        print("  1. Review your daily plan")
        print("  2. Complete tasks throughout the day")
        print("  3. Run 'daily-planner.sh feedback' in the evening")
        print("  4. System will learn and improve tomorrow's plan")

if __name__ == "__main__":
    generator = DailyPlanGenerator()
    generator.ensure_directories()
    
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    generator.generate(date_arg)
