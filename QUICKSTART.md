# ZeroClaw Daily Planning System - Quick Start

## 🚀 Getting Started

### 1. Generate Your First Plan
```bash
# Generate today's plan with AI enhancement
python3 ~/daily-plans/generate-enhanced-plan.py

# Or use the basic version
~/daily-plans/daily-planner.sh generate
```

### 2. Work Through Your Day
- Complete tasks from the TODO section
- Mark completed items in the DONE section
- Track your energy levels

### 3. Provide Feedback (End of Day)
```bash
# Open today's plan for feedback entry
~/daily-plans/daily-planner.sh feedback
```

Fill in these sections:
- ✅ **What Worked Well** - Tasks that went smoothly
- ❌ **What Didn't Work** - Obstacles and challenges  
- 🎓 **Lessons Learned** - Key insights
- ⚡ **Energy Levels** - Rate your energy 1-10

### 4. Automatic Learning
The system automatically:
- Analyzes your feedback
- Updates patterns
- Improves tomorrow's recommendations

## 📋 Daily Commands

```bash
# Generate plan for specific date
python3 ~/daily-plans/generate-enhanced-plan.py 2026-03-15

# Review any day's plan
~/daily-plans/daily-planner.sh review 2026-03-13

# View learned patterns
~/daily-plans/daily-planner.sh patterns

# Show week overview
~/daily-plans/daily-planner.sh week

# Set up automatic daily generation at 6 AM
~/daily-plans/daily-planner.sh setup
```

## 🔄 Daily Workflow

1. **Morning (6 AM)**: Plan auto-generates or run manually
2. **Throughout Day**: Complete tasks, mark progress
3. **Evening (9 PM)**: Add feedback to today's plan
4. **Next Day**: System uses feedback to improve planning

## 📊 How It Learns

### Energy Patterns
- Tracks your energy levels throughout the day
- Identifies when you're most productive
- Schedules important tasks accordingly

### Task Preferences
- Learns which task types you complete successfully
- Identifies tasks you tend to avoid
- Balances challenging and comfortable tasks

### Completion Patterns
- Analyzes optimal task count per day
- Learns realistic time estimates
- Adjusts difficulty based on success rates

### Feedback Themes
- Extracts recurring obstacles
- Identifies success factors
- Generates actionable insights

## 📁 File Structure

```
~/daily-plans/
├── 2026-03-13-plan.md          # Today's plan
├── 2026-03-12-plan.md          # Yesterday's plan  
├── template.md                 # Plan template
├── patterns.json              # Learned patterns
├── generate-enhanced-plan.py   # AI-powered generator
├── daily-planner.sh           # Command interface
└── README.md                  # This guide
```

## 🎯 Best Practices

### For Best Results
1. **Be Consistent**: Use it every day for better learning
2. **Honest Feedback**: Accurate feedback improves recommendations
3. **Specific Tasks**: Make tasks actionable and measurable
4. **Regular Reviews**: Check patterns weekly to see progress

### Task Examples
❌ Bad: "Work on project"  
✅ Good: "Complete user authentication module - 2 hours"

❌ Bad: "Learn something"  
✅ Good: "Complete Python decorators tutorial - 45 minutes"

### Feedback Tips
- Be specific about what worked/didn't work
- Include external factors (meetings, interruptions)
- Note your physical/mental state
- Mention tools or environments that helped

## 🤖 ZeroClaw Integration

When ZeroClaw is available, the system:
- Generates personalized task recommendations
- Analyzes feedback with AI
- Provides contextual insights
- Adapts to your unique patterns

Without ZeroClaw, it still provides:
- Structured daily planning
- Pattern tracking
- Feedback analysis
- Consistent workflow

## 🔧 Troubleshooting

### Plan Generation Issues
```bash
# Check if ZeroClaw is available
which zeroclaw

# Use basic generator if AI fails
~/daily-plans/daily-planner.sh generate
```

### Permission Issues
```bash
# Make scripts executable
chmod +x ~/daily-plans/*.sh ~/daily-plans/*.py
```

### Missing Dependencies
```bash
# Install Python 3 if needed
sudo apt install python3 python3-pip

# Install required packages
pip3 install --user pathlib
```

## 📈 Advanced Features

### Custom Templates
Edit `~/daily-plans/template.md` to customize:
- Task categories
- Time blocks
- Feedback sections
- Additional tracking metrics

### Pattern Analysis
Run `~/daily-plans/daily-planner.sh patterns` to see:
- Your productivity patterns
- Optimal work times
- Task type preferences
- Success factors

### Automation
Set up cron for automatic generation:
```bash
# Edit cron jobs
crontab -e

# Add this line for 6 AM generation
0 6 * * * python3 ~/daily-plans/generate-enhanced-plan.py
```

---

**Start using it today!** The more consistently you use it, the better it understands your patterns and preferences.
