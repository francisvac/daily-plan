# ZeroClaw Daily Planning Configuration

## System Instructions
When generating daily plans, follow these guidelines:

### Plan Generation Principles
1. **Adaptive Learning**: Analyze previous day's feedback to improve recommendations
2. **Energy Awareness**: Consider user's energy patterns throughout the day
3. **Task Balance**: Mix deep work, quick tasks, learning, and reflection
4. **Realistic Goals**: 3-6 priority tasks per day, not overwhelming
5. **Time Awareness**: Consider day of week and typical schedule patterns

### Task Categories
- **Deep Work**: Requires focus, minimal interruptions (2-3 hours)
- **Collaboration**: Meetings, calls, teamwork (1-2 hours)
- **Maintenance**: Email, admin, routine tasks (1 hour)
- **Learning**: Study, research, skill development (1 hour)
- **Planning**: Strategy, goal setting, reflection (30 minutes)

### Feedback Analysis Focus
- **Energy Patterns**: When user has most/least energy
- **Task Success**: Which types of tasks get completed
- **Obstacles**: What prevents task completion
- **Success Factors**: What enables productivity
- **Time Management**: How well estimates match reality

### Plan Structure Requirements
- Morning tasks (9 AM - 12 PM): 3 items with priority levels
- Afternoon tasks (1 PM - 5 PM): 3 items with variety
- Evening tasks (6 PM - 9 PM): 2-3 lighter tasks
- Include learning and reflection time
- Allow for breaks and flexibility

### Pattern Learning Rules
- Track completion rates by task type and time
- Identify optimal task sequencing
- Learn from user's energy patterns
- Adapt to seasonal/weekly patterns
- Update recommendations based on feedback themes

### Quality Standards
- Tasks should be specific and actionable
- Time estimates should be realistic
- Plans should feel achievable, not overwhelming
- Include both professional and personal development
- Allow for unexpected interruptions

## ZeroClaw Integration Commands

### Daily Plan Generation
```bash
# Generate today's plan
~/daily-plans/daily-planner.sh generate

# Generate plan for specific date
~/daily-plans/daily-planner.sh generate 2026-03-15

# Analyze feedback only
~/daily-plans/daily-planner.sh analyze
```

### Plan Management
```bash
# Review today's plan
~/daily-plans/daily-planner.sh review

# Add feedback to today's plan
~/daily-plans/daily-planner.sh feedback

# View learned patterns
~/daily-plans/daily-planner.sh patterns

# Show weekly overview
~/daily-plans/daily-planner.sh week
```

### Automation Setup
```bash
# Set up automatic daily generation
~/daily-plans/daily-planner.sh setup
```

## File Locations
- **Plans**: `~/daily-plans/YYYY-MM-DD-plan.md`
- **Template**: `~/daily-plans/template.md`
- **Patterns**: `~/daily-plans/patterns.json`
- **Scripts**: `~/daily-plans/generate-daily-plan.sh`
- **Interface**: `~/daily-plans/daily-planner.sh`

## Usage Workflow
1. **Morning**: Run `daily-planner.sh generate` or use cron automation
2. **Throughout Day**: Complete tasks, mark them in DONE section
3. **Evening**: Run `daily-planner.sh feedback` to add reflections
4. **Next Day**: System learns from feedback and improves plan

## ZeroClaw Memory Integration
The system integrates with ZeroClaw's memory to:
- Store patterns and insights
- Cross-reference with other user data
- Provide contextual recommendations
- Learn from long-term trends
