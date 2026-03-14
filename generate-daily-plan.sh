#!/bin/bash

# ZeroClaw Daily Plan Generator
# Usage: ./generate-daily-plan.sh [--date YYYY-MM-DD] [--analyze-only]

DATE_ARG=${1:-$(date +%Y-%m-%d)}
ANALYZE_ONLY=${2:-false}
PLAN_DIR="$HOME/daily-plans"
TEMPLATE_FILE="$PLAN_DIR/template.md"
PATTERNS_FILE="$PLAN_DIR/patterns.json"

# Create plan directory if it doesn't exist
mkdir -p "$PLAN_DIR"

# Function to get yesterday's plan for analysis
get_yesterday_plan() {
    local yesterday=$(date -d "$DATE_ARG -1 day" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
    local yesterday_plan="$PLAN_DIR/${yesterday}-plan.md"
    
    if [[ -f "$yesterday_plan" ]]; then
        echo "$yesterday_plan"
    else
        echo ""
    fi
}

# Function to analyze previous day's feedback
analyze_feedback() {
    local yesterday_plan=$(get_yesterday_plan)
    
    if [[ -z "$yesterday_plan" ]]; then
        echo "No previous plan found for analysis"
        return
    fi
    
    echo "Analyzing feedback from $(basename "$yesterday_plan")..."
    
    # Extract feedback sections using ZeroClaw
    if command -v zeroclaw >/dev/null 2>&1; then
        zeroclaw agent -m "Analyze the feedback sections in $yesterday_plan and extract:
1. What activities worked well and why
2. What didn't work and why  
3. Energy patterns throughout the day
4. Task completion patterns
5. Key lessons learned

Provide a concise summary of patterns to consider for today's plan." \
        --output-json > "$PLAN_DIR/feedback-analysis.json" 2>/dev/null || true
    fi
}

# Function to generate today's plan
generate_plan() {
    local today_date="$DATE_ARG"
    local day_of_week=$(date -d "$today_date" +%A 2>/dev/null || date -j -f "%Y-%m-%d" "$today_date" +%A)
    local plan_file="$PLAN_DIR/${today_date}-plan.md"
    
    echo "Generating daily plan for $today_date ($day_of_week)..."
    
    # Create plan from template
    cp "$TEMPLATE_FILE" "$plan_file"
    
    # Replace template variables
    sed -i '' "s/{{DATE}}/$today_date/g" "$plan_file"
    sed -i '' "s/{{DAY_OF_WEEK}}/$day_of_week/g" "$plan_file"
    sed -i '' "s/{{TIMESTAMP}}/$(date '+%Y-%m-%d %H:%M:%S')/g" "$plan_file"
    
    # Generate personalized content using ZeroClaw
    if command -v zeroclaw >/dev/null 2>&1; then
        echo "Generating personalized plan content with ZeroClaw..."
        
        # Get context from previous day
        local context=""
        local yesterday_plan=$(get_yesterday_plan)
        if [[ -n "$yesterday_plan" ]]; then
            context="Based on yesterday's plan in $yesterday_plan and the feedback provided, "
        fi
        
        # Generate plan content
        zeroclaw agent -m "${context}generate a personalized daily plan for $day_of_week, $today_date.

Consider:
- It's a $day_of_week
- Typical energy patterns for this day
- Mix of deep work and quick tasks
- 3-4 priority tasks total
- Learning and reflection time

Provide the following in JSON format:
{
  \"priority_level\": \"High/Medium/Low\",
  \"focus_areas\": [\"area1\", \"area2\"],
  \"morning_tasks\": [\"task1\", \"task2\", \"task3\"],
  \"afternoon_tasks\": [\"task1\", \"task2\", \"task3\"],
  \"evening_tasks\": [\"task1\", \"task2\", \"task3\"]
}" \
        --output-json > "$PLAN_DIR/generated-content.json" 2>/dev/null || true
        
        # Apply generated content if available
        if [[ -f "$PLAN_DIR/generated-content.json" ]]; then
            # Parse JSON and replace template variables (simplified approach)
            python3 -c "
import json
import sys
try:
    with open('$PLAN_DIR/generated-content.json', 'r') as f:
        data = json.load(f)
    
    with open('$plan_file', 'r') as f:
        content = f.read()
    
    # Replace variables with generated content
    content = content.replace('{{PRIORITY_LEVEL}}', data.get('priority_level', 'Medium'))
    content = content.replace('{{FOCUS_AREAS}}', ', '.join(data.get('focus_areas', ['General productivity'])))
    
    tasks = data.get('morning_tasks', ['', '', ''])
    for i, task in enumerate(tasks[:3], 1):
        content = content.replace('{{MORNING_TASK_' + str(i) + '}}', task)
    
    tasks = data.get('afternoon_tasks', ['', '', ''])
    for i, task in enumerate(tasks[:3], 1):
        content = content.replace('{{AFTERNOON_TASK_' + str(i) + '}}', task)
    
    tasks = data.get('evening_tasks', ['', '', ''])
    for i, task in enumerate(tasks[:3], 1):
        content = content.replace('{{EVENING_TASK_' + str(i) + '}}', task)
    
    # Fill remaining placeholders
    placeholders = ['{{COMPLETION_RATE}}', '{{PRODUCTIVE_TIME}}', '{{TASK_TYPE_PATTERNS}}', '{{ENERGY_PATTERNS}}']
    for placeholder in placeholders:
        content = content.replace(placeholder, 'TBD')
    
    with open('$plan_file', 'w') as f:
        f.write(content)
        
except Exception as e:
    print(f'Error processing generated content: {e}')
    # Keep template with basic date replacements
" 2>/dev/null || true
        fi
    fi
    
    # Fill remaining placeholders with defaults
    sed -i '' 's/{{[^}]*}}/TBD/g' "$plan_file"
    
    echo "Plan generated: $plan_file"
}

# Function to update patterns
update_patterns() {
    echo "Updating learning patterns..."
    
    if [[ -f "$PLAN_DIR/feedback-analysis.json" ]] && command -v zeroclaw >/dev/null 2>&1; then
        zeroclaw agent -m "Update the patterns.json file based on feedback-analysis.json. 
Extract and update:
1. Energy level patterns
2. Task type preferences  
3. Completion patterns
4. Feedback themes
5. Productivity insights

Maintain existing patterns and add new insights. Return updated JSON." \
        --output-json > "$PLAN_DIR/patterns-updated.json" 2>/dev/null || true
        
        # Backup and update patterns
        if [[ -f "$PLAN_DIR/patterns-updated.json" ]]; then
            cp "$PATTERNS_FILE" "$PLAN_DIR/patterns-backup-$(date +%Y%m%d).json"
            mv "$PLAN_DIR/patterns-updated.json" "$PATTERNS_FILE"
        fi
    fi
}

# Main execution
main() {
    echo "=== ZeroClaw Daily Plan Generator ==="
    echo "Date: $DATE_ARG"
    echo "Analyze only: $ANALYZE_ONLY"
    echo ""
    
    if [[ "$ANALYZE_ONLY" == "true" ]]; then
        analyze_feedback
        update_patterns
    else
        analyze_feedback
        generate_plan
        update_patterns
    fi
    
    echo ""
    echo "=== Summary ==="
    echo "Plan directory: $PLAN_DIR"
    echo "Today's plan: $PLAN_DIR/${DATE_ARG}-plan.md"
    echo "Patterns file: $PATTERNS_FILE"
    echo ""
    echo "Next steps:"
    echo "1. Review your daily plan"
    echo "2. Complete tasks throughout the day"
    echo "3. Fill in feedback section at end of day"
    echo "4. Run again tomorrow for improved planning"
}

# Run main function
main "$@"
