#!/bin/bash

# ZeroClaw Baby Planner Remote Management
# Manage your baby daily planning system on remote server

REMOTE_SERVER="agent1@10.0.0.231"
REMOTE_PATH="/home/agent1/daily-plans"
REMOTE_SCRIPT="daily-planner.sh"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

# Helper functions
print_header() {
    echo -e "${BLUE}👶 ZeroClaw Baby Planner - Remote Management${NC}"
    echo "============================================"
    echo ""
}

# Check ZeroClaw status
cmd_status() {
    print_header
    echo "🤖 ZeroClaw Status:"
    ssh $SSH_OPTS "$REMOTE_SERVER" "cd $REMOTE_PATH && ./$REMOTE_SCRIPT status"
    echo ""
    echo "📋 Baby Planner Status:"
    ssh "$REMOTE_SERVER" "crontab -l | grep baby || echo 'No cron job found'"
}

# Generate baby plan
cmd_generate() {
    local date="${1:-}"
    local age="${2:-}"
    
    # Convert "today" to actual date
    if [[ "$date" == "today" ]] || [[ -z "$date" ]]; then
        date=$(date +%Y-%m-%d)
    fi
    
    print_header
    echo -e "${PURPLE}👶 Generating Baby Plan${NC}"
    echo "Date: $date"
    [[ -n "$age" ]] && echo "Age: $age months"
    echo ""
    
    if [[ -n "$age" ]]; then
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$REMOTE_SERVER" "cd $REMOTE_PATH && ./$REMOTE_SCRIPT generate $date $age"
    else
        ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && python3 generate-baby-plan.py $date"
    fi
}

# View plan
cmd_view() {
    local date="${1:-}"
    
    # Convert "today" to actual date
    if [[ "$date" == "today" ]] || [[ -z "$date" ]]; then
        date=$(date +%Y-%m-%d)
    fi
    
    print_header
    echo "📋 Baby Plan for $date:"
    echo ""
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && ./$REMOTE_SCRIPT review $date"
}

# Add feedback
cmd_feedback() {
    local date="${1:-}"
    
    # Convert "today" to actual date
    if [[ "$date" == "today" ]] || [[ -z "$date" ]]; then
        date=$(date +%Y-%m-%d)
    fi
    
    print_header
    echo -e "${PURPLE}📝 Adding Feedback for $date${NC}"
    echo ""
    echo "Opening plan for feedback entry..."
    echo "Fill in these sections:"
    echo "  ✅ What Baby Enjoyed Most"
    echo "  ❌ What Baby Didn't Like" 
    echo "  🎓 Sleep & Feeding Patterns"
    echo "  📝 Developmental Observations"
    echo ""
    
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && ./$REMOTE_SCRIPT feedback $date"
    
    echo ""
    echo -e "${GREEN}✅ Feedback saved!${NC}"
}

# View patterns
cmd_patterns() {
    print_header
    echo "🧠 Baby Learning Patterns:"
    echo ""
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && cat patterns.json | python3 -m json.tool 2>/dev/null || cat patterns.json"
}

# Week overview
cmd_week() {
    print_header
    echo "📅 Week Overview:"
    echo ""
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && ./$REMOTE_SCRIPT week"
}

# Test ZeroClaw
cmd_test() {
    print_header
    echo "🧪 Testing ZeroClaw Integration:"
    echo ""
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && zeroclaw agent -m 'Generate a simple baby activity for a 6-month-old' --quiet"
}

# Email setup
cmd_email_setup() {
    print_header
    echo -e "${YELLOW}📧 Setting up Email Integration...${NC}"
    echo ""
    echo "This will configure Gmail to send daily baby plans."
    echo "You'll need a Gmail App Password from:"
    echo "https://myaccount.google.com/apppasswords"
    echo ""
    
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && python3 email_integration.py setup"
}

# Test email
cmd_email_test() {
    print_header
    echo "📧 Testing Email Configuration:"
    echo ""
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && python3 email_integration.py test"
}

# Process feedback emails
cmd_process_feedback() {
    print_header
    echo -e "${YELLOW}🔍 Processing Feedback Emails...${NC}"
    echo ""
    echo "Checking fvachaparambil@gmail.com for baby feedback..."
    echo ""
    
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && python3 email_feedback_processor.py process"
}

# Test email feedback connection
cmd_test_feedback() {
    print_header
    echo "📧 Testing Feedback Email Connection:"
    echo ""
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && python3 email_feedback_processor.py test"
}

# Send plan via email
cmd_email_send() {
    local date="${1:-}"
    
    # Convert "today" to actual date
    if [[ "$date" == "today" ]] || [[ -z "$date" ]]; then
        date=$(date +%Y-%m-%d)
    fi
    
    print_header
    echo "📧 Sending Baby Plan for $date:"
    echo ""
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && python3 email_integration.py send $date"
}

# Sync with remote repository
cmd_sync() {
    print_header
    echo -e "${YELLOW}🔄 Syncing with Remote Repository...${NC}"
    echo ""
    
    # Push local changes to remote
    echo "📤 Pushing local changes to remote..."
    git -C ~/daily-plans push origin main
    
    # Pull remote changes to local
    echo "📥 Pulling remote changes to local..."
    git -C ~/daily-plans pull origin main
    
    echo ""
    echo -e "${GREEN}✅ Synchronization complete!${NC}"
    echo "Local and remote repositories are now in sync."
}

# Setup/Install
cmd_setup() {
    print_header
    echo -e "${YELLOW}🔧 Setting up Baby Planner...${NC}"
    echo ""
    
    # Ensure permissions
    ssh "$REMOTE_SERVER" "cd $REMOTE_PATH && chmod +x *.sh *.py"
    
    # Set up cron job
    ssh "$REMOTE_SERVER" "(crontab -l 2>/dev/null; echo '0 6 * * * python3 $REMOTE_PATH/generate-baby-plan.py') | crontab -"
    
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo "Baby plans will generate daily at 6 AM"
}

# Help
cmd_help() {
    print_header
    echo "Commands:"
    echo "  status                    Show ZeroClaw and planner status"
    echo "  generate [date] [age]     Generate baby plan"
    echo "  view [date]              View baby plan"
    echo "  feedback [date]          Add feedback to plan"
    echo "  process-feedback           Process feedback emails from fvachaparambil@gmail.com"
    echo "  test-feedback             Test feedback email connection"
    echo "  patterns                 Show learning patterns"
    echo "  week                     Week overview"
    echo "  test                     Test ZeroClaw integration"
    echo "  email-setup              Configure Gmail for email sending"
    echo "  email-test               Test email configuration"
    echo "  email-send [date]        Send plan via email"
    echo "  sync                     Sync local and remote repositories"
    echo "  setup                    Setup/install system"
    echo "  help                     Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 sync                 # Sync local and remote repositories"
    echo "  $0 setup                # Check system status"
    echo "  $0 generate today 6      # Generate today's plan for 6-month-old"
    echo "  $0 feedback              # Add feedback to today's plan"
    echo "  $0 process-feedback       # Process feedback emails"
    echo "  $0 view 2026-03-15       # View specific date's plan"
    echo "  $0 email-setup           # Configure Gmail"
    echo "  $0 email-send today      # Email today's plan"
    echo ""
    echo "📧 Email Feedback Workflow:"
    echo "  1. Reply to daily plan email with your feedback"
    echo "  2. Run: $0 process-feedback"
    echo "  3. System automatically applies feedback to plans"
}

# Main command router
case "${1:-help}" in
    "status")
        cmd_status
        ;;
    "generate")
        cmd_generate "$2" "$3"
        ;;
    "view")
        cmd_view "$2"
        ;;
    "feedback")
        cmd_feedback "$2"
        ;;
    "process-feedback")
        cmd_process_feedback
        ;;
    "test-feedback")
        cmd_test_feedback
        ;;
    "patterns")
        cmd_patterns
        ;;
    "week")
        cmd_week
        ;;
    "test")
        cmd_test
        ;;
    "email-setup")
        cmd_email_setup
        ;;
    "email-test")
        cmd_email_test
        ;;
    "email-send")
        cmd_email_send "$2"
        ;;
    "sync")
        cmd_sync
        ;;
    "setup")
        cmd_setup
        ;;
    "help"|*)
        cmd_help
        ;;
esac
