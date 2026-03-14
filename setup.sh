#!/bin/bash

# ZeroClaw Daily Planning System - Complete Setup
# This script sets up the entire daily planning system

set -e

echo "🚀 ZeroClaw Daily Planning System Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PLAN_DIR="$HOME/daily-plans"

echo -e "${BLUE}Setting up ZeroClaw Daily Planning System...${NC}"
echo ""

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p "$PLAN_DIR"
echo "   ✅ Created: $PLAN_DIR"

# Check if files already exist
if [[ -f "$PLAN_DIR/template.md" ]]; then
    echo -e "${YELLOW}⚠️  Files already exist. Updating...${NC}"
fi

# Create symbolic links for easy access
echo "🔗 Creating convenient commands..."
if [[ ! -L "$HOME/bin/daily-plan" ]]; then
    mkdir -p "$HOME/bin"
    ln -sf "$PLAN_DIR/daily-planner.sh" "$HOME/bin/daily-plan"
    echo "   ✅ Created: ~/bin/daily-plan command"
fi

if [[ ! -L "$HOME/bin/generate-plan" ]]; then
    ln -sf "$PLAN_DIR/generate-enhanced-plan.py" "$HOME/bin/generate-plan"
    echo "   ✅ Created: ~/bin/generate-plan command"
fi

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "📝 Adding ~/bin to PATH..."
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc" 2>/dev/null || echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null
    echo "   ✅ Added to PATH (restart terminal or run: export PATH=\"\$HOME/bin:\$PATH\")"
fi

# Test ZeroClaw availability
echo ""
echo "🤖 Checking ZeroClaw availability..."
if command -v zeroclaw >/dev/null 2>&1; then
    echo "   ✅ ZeroClaw found - AI features enabled"
    ZEROCLAW_AVAILABLE=true
else
    echo -e "${YELLOW}   ⚠️  ZeroClaw not found - Using basic mode${NC}"
    echo "   Install ZeroClaw for AI-enhanced planning:"
    echo "   curl -fsSL https://raw.githubusercontent.com/zeroclaw-labs/zeroclaw/main/install.sh | bash"
    ZEROCLAW_AVAILABLE=false
fi

# Generate first plan
echo ""
echo "📋 Generating your first daily plan..."
if [[ "$ZEROCLAW_AVAILABLE" == true ]]; then
    python3 "$PLAN_DIR/generate-enhanced-plan.py"
else
    "$PLAN_DIR/daily-planner.sh" generate
fi

# Set up cron (optional)
echo ""
echo "⏰ Would you like to set up automatic daily plan generation at 6 AM?"
echo "   This will add a cron job to generate plans automatically."
echo ""
read -p "Enable automatic generation? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create cron entry
    CRON_ENTRY="0 6 * * * python3 $PLAN_DIR/generate-enhanced-plan.py"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab - 2>/dev/null || {
        echo -e "${YELLOW}   ⚠️  Could not add cron job automatically${NC}"
        echo "   Add this line manually with 'crontab -e':"
        echo "   $CRON_ENTRY"
    }
    
    if [[ $? -eq 0 ]]; then
        echo "   ✅ Cron job added - Plans will generate daily at 6 AM"
    fi
else
    echo "   ℹ️  Manual generation - Run 'daily-plan generate' each morning"
fi

# Show quick start
echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo "📖 Quick Start Guide:"
echo "==================="
echo ""
echo "Generate today's plan:"
echo "   daily-plan generate"
echo "   # or: generate-plan"
echo ""
echo "Add feedback at end of day:"
echo "   daily-plan feedback"
echo ""
echo "Review your plan:"
echo "   daily-plan review"
echo ""
echo "See weekly overview:"
echo "   daily-plan week"
echo ""
echo "View learned patterns:"
echo "   daily-plan patterns"
echo ""
echo "Show help:"
echo "   daily-plan help"
echo ""
echo "📁 Files Location:"
echo "   Plans: $PLAN_DIR/YYYY-MM-DD-plan.md"
echo "   Template: $PLAN_DIR/template.md"
echo "   Patterns: $PLAN_DIR/patterns.json"
echo ""
echo "📚 Documentation:"
echo "   Quick start: $PLAN_DIR/QUICKSTART.md"
echo "   Full guide: $PLAN_DIR/README.md"
echo ""
echo -e "${BLUE}🔄 Daily Workflow:${NC}"
echo "   1. Morning: 'daily-plan generate' (or automatic at 6 AM)"
echo "   2. Day: Complete tasks, mark progress in plan file"
echo "   3. Evening: 'daily-plan feedback' - add reflections"
echo "   4. Learning: System analyzes feedback and improves tomorrow"
echo ""
echo -e "${GREEN}✨ Your personalized daily planning system is ready!${NC}"
echo "   The more you use it, the better it understands your patterns."
