# ZeroClaw Baby Planner - Email User Guide

## 📧 Overview

The ZeroClaw Baby Planner supports email-based interaction, allowing you to:
- Receive daily baby development plans via email
- Provide feedback on activities and experiences
- Store journal entries and observations
- Retrieve memory summaries and patterns
- Update baby preferences and schedules

## 🚀 Quick Start

### 1. Initial Setup

First, configure your email settings:

```bash
# Edit email configuration
nano email_config.json
```

Add your email credentials:
```json
{
  "sender_email": "your-email@gmail.com",
  "app_password": "your-app-password",
  "recipient_email": "parent-email@gmail.com"
}
```

### 2. Generate Your First Plan

```bash
# Generate daily plan
python3 generate-baby-plan.py

# Send via email (if configured)
python3 email_integration.py
```

## 📧 Email Commands Reference

### 📝 Feedback Commands

#### Basic Feedback
```
feedback Baby loved tummy time today and enjoyed reading books
```

#### Detailed Feedback
```
feedback Baby had a great morning with tummy time - held head up for 2 minutes! Really enjoyed the sensory play with soft textures. Didn't like the loud music in the afternoon - became fussy.
```

#### Sleep Feedback
```
feedback Baby slept well last night - 8 hours with only 1 wakeup. Morning nap was 1.5 hours.
```

#### Feeding Feedback
```
feedback Baby had excellent feeding this morning - took full bottle without fussiness.
```

### 📓 Journal Commands

#### Daily Journal Entry
```
journal Had a wonderful morning with lots of smiles and cooing. Baby was very alert during tummy time.
```

#### Developmental Observations
```
journal Baby showing better head control today and tracking objects more consistently. Starting to reach for toys.
```

#### Behavioral Notes
```
journal Afternoon was challenging - baby seemed overstimulated. Calmed down after quiet time.
```

### 🧠 Memory Retrieval Commands

#### Today's Memory
```
memory today
```

#### Weekly Summary
```
memory week
```

#### Monthly Summary
```
memory month
```

#### Search Specific Topics
```
memory search tummy
memory search sleep
memory search feeding
```

### 📊 Pattern Information Commands

#### Current Patterns
```
patterns
```

#### Favorite Activities
```
patterns activities
```

#### Sleep Schedule
```
patterns sleep
```

#### Developmental Stage
```
patterns development
```

### ❓ Help Command
```
help
```

## 📧 Email Format Examples

### Example 1: Daily Feedback Email

**Subject:** Baby Feedback - 2025-03-22

**Body:**
```
Hi ZeroClaw,

Today's feedback:

feedback Baby absolutely loved tummy time this morning! Held head up for almost 2 minutes and was so engaged. Really enjoyed the soft sensory toys and high-contrast books.

journal Had a great morning session with lots of smiles and babbles. Baby was very alert and responsive.

feedback Afternoon was a bit challenging - baby got fussy during loud music time but calmed down with gentle singing.

journal Evening routine went smoothly. Baby seemed tired but happy.

Can you show me this week's memory summary?
memory week

Thanks,
Parent
```

### Example 2: Journal-Only Email

**Subject:** Daily Journal - Great Progress!

**Body:**
```
Hello!

Today was such a good day with the baby!

journal Amazing tummy time session today - baby held head up steadily for 3 minutes! Much stronger than last week.

journal Baby tracked the colorful book pages really well today - following objects from left to right.

journal Started making new sounds today - lots of babbling and giggles during playtime.

journal Feeding went well - baby took full bottle without any issues.

journal Sleep was good last night - only woke up once for feeding.

Overall, excellent developmental progress today!

Best,
Parent
```

### Example 3: Memory Retrieval Email

**Subject:** Memory Request

**Body:**
```
Hi ZeroClaw,

Can you help me with some information?

memory search tummy
memory sleep quality
patterns
patterns activities

Thanks!
```

### Example 4: Multi-Command Email

**Subject:** Daily Update

**Body:**
```
feedback Baby loved sensory play today with the soft textures
journal Had a calm afternoon with good napping
feedback Didn't like sudden loud noises - became fussy
journal Evening routine went smoothly
memory today
patterns
```

## 🔄 Daily Workflow

### Morning (Plan Generation)
1. **System generates** daily baby development plan
2. **Email sent** with activities and schedule
3. **Parent receives** plan and follows activities

### During Day (Activities & Observations)
1. **Parent engages** in planned activities
2. **Notes taken** on baby's responses
3. **Observations recorded** about development

### Evening (Feedback & Journal)
1. **Parent sends** feedback email with observations
2. **System processes** feedback and updates patterns
3. **Memory entries created** for future reference

### Ongoing (Learning & Adaptation)
1. **System learns** from feedback patterns
2. **Future plans adapt** based on preferences
3. **Developmental progress tracked** over time

## 📱 Email Tips & Best Practices

### ✅ Do's
- **Be specific** in your feedback ("loved tummy time" vs "liked activities")
- **Include context** (time of day, environment, baby's mood)
- **Note developmental milestones** (head control, tracking, reaching)
- **Record sleep and feeding patterns** regularly
- **Use multiple commands** in one email when convenient
- **Include dates** in subject lines for organization

### ❌ Don'ts
- **Don't worry about perfect grammar** - system understands natural language
- **Don't send sensitive personal information** beyond baby-related data
- **Don't feel pressured to respond immediately** - send when convenient
- **Don't repeat the same feedback** unless it's noteworthy

### 📝 Subject Line Guidelines
- **Include dates**: "Baby Feedback - 2025-03-22"
- **Be descriptive**: "Daily Journal - Great Progress!"
- **Keep it simple**: "Memory Request" or "Daily Update"

## 🔍 Advanced Features

### Pattern Learning
The system automatically learns from your feedback:
- **Favorite activities** are identified and prioritized
- **Disliked activities** are avoided in future plans
- **Optimal timing** is learned from your feedback
- **Developmental progress** is tracked over time

### Memory Search
Use the memory search to find specific information:
```
memory search [keyword]
```
Examples:
- `memory search tummy` - Find all tummy time related entries
- `memory search sleep` - Find sleep patterns and quality
- `memory search feeding` - Find feeding responses and schedules

### Pattern History
Track how the system is learning:
```
patterns
```
This shows:
- Current developmental stage
- Favorite activities identified
- Success rates and accuracy
- Historical progress

## 🛠️ Troubleshooting

### Email Not Sending
1. **Check email configuration** in `email_config.json`
2. **Verify Gmail App Password** (not regular password)
3. **Check internet connection**
4. **Verify recipient email address**

### Commands Not Working
1. **Use exact command names**: `feedback`, `journal`, `memory`, `patterns`, `help`
2. **Check spelling** of commands
3. **One command per line** for multiple commands
4. **Include space** after command name

### No Response Received
1. **Check email was sent** to correct address
2. **Wait a few minutes** for processing
3. **Check spam folder** for responses
4. **Verify system is running**: `python3 email_command_processor.py`

### Memory Not Found
1. **Use correct date ranges**: `today`, `week`, `month`
2. **Check search terms**: `memory search [keyword]`
3. **Verify entries exist** by checking `memory_entries.json`

## 📞 Support

### Common Issues & Solutions

**Q: How do I set up Gmail App Password?**
A: 
1. Go to Google Account settings
2. Enable 2-factor authentication
3. Go to Security → App Passwords
4. Generate new app password for "Mail"
5. Use this password in `email_config.json`

**Q: Can I send multiple commands in one email?**
A: Yes! Put each command on a separate line:
```
feedback Baby loved tummy time
journal Great morning session
memory today
```

**Q: How often should I send feedback?**
A: Daily is ideal, but the system works with any frequency. More feedback = better learning.

**Q: Can I correct mistakes in previous entries?**
A: Yes, send new feedback with corrections. The system learns from patterns over time.

**Q: How do I see what the system has learned?**
A: Use the `patterns` command to see current learning and preferences.

### Getting Help
- **Command reference**: Send `help` in an email
- **System status**: Check logs in the application
- **Configuration**: Verify `email_config.json` settings
- **Memory backup**: Check `memory_entries.json` file

## 🎯 Success Tips

1. **Be Consistent**: Send feedback regularly for best learning
2. **Be Specific**: Detailed feedback helps the system learn better
3. **Be Patient**: Pattern learning improves over time
4. **Be Comprehensive**: Include activities, sleep, feeding, and developmental notes
5. **Be Organized**: Use consistent subject lines and dates

---

**🎉 You're all set!** The ZeroClaw Baby Planner email system is ready to help you track your baby's development and learn from your feedback to provide increasingly personalized and effective daily plans.

**📧 Start by sending your first feedback email today!**
