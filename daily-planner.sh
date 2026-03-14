#!/bin/bash

# ZeroClaw Daily Planning Interface
# Provides easy commands for daily plan management

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAN_DIR="$HOME/daily-plans"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}=== ZeroClaw Daily Planning System ===${NC}"
    echo ""
}

print_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  generate [date]     Generate daily plan (default: today)"
    echo "  analyze            Analyze yesterday's feedback only"
    echo "  review [date]      Review a specific day's plan"
    echo "  feedback [date]    Open today's plan for feedback entry"
    echo "  patterns           Show learned patterns"
    echo "  week               Show week overview"
    echo "  setup              Set up cron job for automatic generation"
    echo "  help               Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 generate                    # Generate today's plan"
    echo "  $0 generate 2026-03-15        # Generate plan for specific date"
    echo "  $0 feedback                    # Open today's plan for feedback"
    echo "  $0 patterns                    # Show learned patterns"
}

# Generate plan for specific date
cmd_generate() {
    local date="${1:-$(date +%Y-%m-%d)}"
    print_header
    echo "Generating daily plan for: $date"
    echo ""
    "$SCRIPT_DIR/generate-daily-plan.sh" "$date"
}

# Analyze feedback only
cmd_analyze() {
    print_header
    echo "Analyzing yesterday's feedback..."
    echo ""
    "$SCRIPT_DIR/generate-daily-plan.sh" "$(date +%Y-%m-%d)" "true"
}

# Review a plan
cmd_review() {
    local date="${1:-$(date +%Y-%m-%d)}"
    local plan_file="$PLAN_DIR/${date}-plan.md"
    
    print_header
    if [[ -f "$plan_file" ]]; then
        echo "Reviewing plan for: $date"
        echo ""
        cat "$plan_file"
    else
        echo -e "${RED}No plan found for $date${NC}"
        echo "Generate one first: $0 generate $date"
    fi
}

# Open plan for feedback
cmd_feedback() {
    local date="${1:-$(date +%Y-%m-%d)}"
    local plan_file="$PLAN_DIR/${date}-plan.md"
    
    print_header
    if [[ -f "$plan_file" ]]; then
        echo "Opening plan for feedback: $date"
        echo ""
        echo "Edit the following sections:"
        echo "  ✅ DONE Section - Mark completed tasks"
        echo "  📝 FEEDBACK Section - What worked/didn't work"
        echo "  🔄 Tomorrow's Prep - Insights for tomorrow"
        echo ""
        echo "Press Enter to open in editor..."
        read
        
        # Open in default editor
        ${EDITOR:-nano} "$plan_file"
        
        echo ""
        echo -e "${GREEN}Feedback saved!${NC}"
        echo "Patterns will be updated when you generate tomorrow's plan."
    else
        echo -e "${RED}No plan found for $date${NC}"
        echo "Generate one first: $0 generate $date"
    fi
}

# Show learned patterns
cmd_patterns() {
    local patterns_file="$PLAN_DIR/patterns.json"
    
    print_header
    echo "Learned Patterns & Insights"
    echo ""
    
    if [[ -f "$patterns_file" ]]; then
        if command -v zeroclaw >/dev/null 2>&1; then
            zeroclaw agent -m "Analyze the patterns.json file and provide a human-readable summary of:
1. Energy level patterns
2. Task preferences 
3. Completion patterns
4. Key insights
5. Recommendations for future planning

Keep it concise and actionable." --quiet
        else
            echo "ZeroClaw not available. Showing raw patterns:"
            cat "$patterns_file"
        fi
    else
        echo -e "${YELLOW}No patterns data found yet.${NC}"
        echo "Generate some plans and provide feedback to build patterns."
    fi
}

# Show week overview
cmd_week() {
    print_header
    echo "Weekly Overview"
    echo ""
    
    # Get current date in a cross-platform way
    if command -v python3 >/dev/null 2>&1; then
        start_of_week=$(python3 -c "
import datetime
today = datetime.date.today()
start = today - datetime.timedelta(days=today.weekday())
print(start.strftime('%Y-%m-%d'))
")
    else
        start_of_week=$(date +%Y-%m-%d)
    fi
    
    for i in {0..6}; do
        if command -v python3 >/dev/null 2>&1; then
            date=$(python3 -c "
import datetime
start = datetime.datetime.strptime('$start_of_week', '%Y-%m-%d').date()
current = start + datetime.timedelta(days=$i)
print(current.strftime('%Y-%m-%d'))
")
            day_name=$(python3 -c "
import datetime
start = datetime.datetime.strptime('$start_of_week', '%Y-%m-%d').date()
current = start + datetime.timedelta(days=$i)
print(current.strftime('%A'))
")
        else
            date=$(date -d "$start_of_week + $i days" +%Y-%m-%d 2>/dev/null || date -v +${i}d -f "%Y-%m-%d" "$start_of_week" +%Y-%m-%d)
            day_name=$(date -d "$date" +%A 2>/dev/null || date -j -f "%Y-%m-%d" "$date" +%A)
        fi
        
        local plan_file="$PLAN_DIR/${date}-plan.md"
        
        echo -n "$day_name ($date): "
        if [[ -f "$plan_file" ]]; then
            if grep -q "TBD" "$plan_file"; then
                echo -e "${YELLOW}Generated (needs feedback)${NC}"
            else
                echo -e "${GREEN}Complete${NC}"
            fi
        else
            echo -e "${RED}Not generated${NC}"
        fi
    done
}

# Setup cron job
cmd_setup() {
    print_header
    echo "Setting up automatic daily plan generation..."
    echo ""
    
    # Create cron job to generate plan at 6 AM daily
    local cron_entry="0 6 * * * $SCRIPT_DIR/generate-daily-plan.sh"
    
    echo "This will add a cron job to generate daily plans at 6:00 AM."
    echo "Cron entry: $cron_entry"
    echo ""
    echo "Press Enter to continue, or Ctrl+C to cancel..."
    read
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    
    echo ""
    echo -e "${GREEN}✅ Cron job added successfully!${NC}"
    echo "Daily plans will be generated at 6:00 AM."
    echo ""
    echo "To manage cron jobs:"
    echo "  crontab -l  # List jobs"
    echo "  crontab -e  # Edit jobs"
}

# Main command router
case "${1:-help}" in
    "generate")
        cmd_generate "$2"
        ;;
    "analyze")
        cmd_analyze
        ;;
    "review")
        cmd_review "$2"
        ;;
    "feedback")
        cmd_feedback "$2"
        ;;
    "patterns")
        cmd_patterns
        ;;
    "week")
        cmd_week
        ;;
    "setup")
        cmd_setup
        ;;
    "help"|*)
        print_usage
        ;;
esac
