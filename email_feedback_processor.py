#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Email Feedback Processor
Reads emails from Gmail and processes baby feedback automatically
"""

import imaplib
import email
import json
import re
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

class EmailFeedbackProcessor:
    def __init__(self):
        self.config_file = Path.home() / "daily-plans" / "email_config.json"
        self.plan_dir = Path.home() / "daily-plans"
        self.processed_emails_file = self.plan_dir / "processed_emails.json"
        
    def load_config(self):
        """Load email configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return None
    
    def load_processed_emails(self):
        """Load list of already processed email IDs"""
        if self.processed_emails_file.exists():
            with open(self.processed_emails_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_processed_email(self, email_id):
        """Save email ID as processed"""
        processed = self.load_processed_emails()
        processed.add(email_id)
        with open(self.processed_emails_file, 'w') as f:
            json.dump(list(processed), f)
    
    def connect_to_gmail(self):
        """Connect to Gmail IMAP"""
        config = self.load_config()
        if not config:
            raise Exception("Email configuration not found")
        
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(config['sender_email'], config['app_password'])
        mail.select('inbox')
        return mail
    
    def extract_feedback_from_email(self, email_message):
        """Extract baby feedback and journal from email content"""
        # Extract email body
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()
        
        # Check for journal entries
        journal_entries = self.extract_journal_entries(body)
        
        # Parse feedback using patterns
        feedback = {
            'what_enjoyed': self.extract_section(body, ['enjoyed', 'liked', 'loved', 'happy']),
            'didnt_like': self.extract_section(body, ['didn\'t like', 'disliked', 'fussy', 'unhappy']),
            'sleep_quality': self.extract_rating(body, ['sleep quality', 'sleep', 'slept']),
            'feeding_response': self.extract_section(body, ['feeding', 'ate', 'nursing']),
            'developmental': self.extract_section(body, ['developmental', 'milestone', 'new skill', 'learned'])
        }
        
        return {
            'feedback': feedback,
            'journal_entries': journal_entries
        }
    
    def extract_journal_entries(self, text):
        """Extract journal entries from email content"""
        lines = text.split('\n')
        journal_entries = []
        
        for line in lines:
            line_lower = line.lower()
            # Look for journal keywords
            if any(keyword in line_lower for keyword in ['journal', 'note', 'thought', 'feeling', 'observation']):
                # Clean up the line
                clean_line = re.sub(r'^[-*•]\s*', '', line.strip())
                if clean_line and len(clean_line) > 3:
                    journal_entries.append(clean_line)
        
        return journal_entries[:5]  # Limit to 5 entries
    
    def extract_section(self, text, keywords):
        """Extract relevant sentences based on keywords"""
        lines = text.split('\n')
        relevant_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                # Clean up the line
                clean_line = re.sub(r'^[-*•]\s*', '', line.strip())
                if clean_line and len(clean_line) > 3:
                    relevant_lines.append(clean_line)
        
        return relevant_lines[:3]  # Limit to top 3 points
    
    def extract_rating(self, text, keywords):
        """Extract numerical rating from text"""
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                # Look for numbers 1-10
                rating_match = re.search(r'(\d+)/10|(\d+)', line_lower)
                if rating_match:
                    rating = rating_match.group(1) or rating_match.group(2)
                    if 1 <= int(rating) <= 10:
                        return rating
        return "5"  # Default rating
    
    def apply_feedback_to_plan(self, date, feedback_data):
        """Apply extracted feedback and journal to plan file"""
        plan_file = self.plan_dir / f"{date}-plan.md"
        
        if not plan_file.exists():
            print(f"No plan file found for {date}")
            return False
        
        # Read current plan
        with open(plan_file, 'r') as f:
            content = f.read()
        
        feedback = feedback_data.get('feedback', {})
        journal_entries = feedback_data.get('journal_entries', [])
        
        # Update feedback sections
        content = self.update_feedback_section(content, '### What Baby Enjoyed Most ✅', feedback['what_enjoyed'])
        content = self.update_feedback_section(content, '### What Baby Didn\'t Like ❌', feedback['didnt_like'])
        
        # Update sleep quality if found
        if feedback['sleep_quality'] != "5":
            content = re.sub(
                r'\*\*Sleep Quality \(1-10\):\*\* TBD',
                f'**Sleep Quality (1-10):** {feedback["sleep_quality"]}',
                content
            )
        
        # Add developmental observations
        if feedback['developmental']:
            dev_section = '\n'.join([f"- {obs}" for obs in feedback['developmental']])
            content = re.sub(
                r'### Developmental Observations\s*\n\s*- TBD\s*\n\s*- TBD\s*\n\s*- TBD',
                f'### Developmental Observations\n{dev_section}',
                content
            )
        
        # Add journal entries
        if journal_entries:
            journal_section = '\n'.join([f"- {entry}" for entry in journal_entries])
            content = re.sub(
                r'### Parent Journal Notes 📔\s*\n\s*- {{PARENT_JOURNAL_1}}\s*\n\s*- {{PARENT_JOURNAL_2}}\s*\n\s*- {{PARENT_JOURNAL_3}}',
                f'### Parent Journal Notes 📔\n{journal_section}',
                content
            )
        
        # Save updated plan
        with open(plan_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Applied feedback and journal to plan for {date}")
        return True
    
    def update_feedback_section(self, content, section_header, feedback_items):
        """Update a specific feedback section"""
        lines = content.split('\n')
        new_lines = []
        in_section = False
        feedback_added = False
        
        for i, line in enumerate(lines):
            if section_header in line:
                in_section = True
                new_lines.append(line)
                continue
            
            if in_section and line.startswith('###') and section_header not in line:
                in_section = False
                new_lines.append(line)
                continue
            
            if in_section and not feedback_added:
                if line.strip().startswith('-') and 'TBD' in line:
                    # Replace TBD with actual feedback
                    if feedback_items:
                        new_lines.append(f"- {feedback_items[0]}")
                        if len(feedback_items) > 1:
                            new_lines.append(f"- {feedback_items[1]}")
                        if len(feedback_items) > 2:
                            new_lines.append(f"- {feedback_items[2]}")
                        feedback_added = True
                        continue
                elif not line.strip():
                    new_lines.append(line)
                    continue
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def process_feedback_emails(self):
        """Main processing function"""
        print("🔍 Processing feedback emails...")
        
        try:
            # Connect to Gmail
            mail = self.connect_to_gmail()
            processed_emails = self.load_processed_emails()
            
            # Search for recent emails (last 24 hours)
            since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            search_criteria = f'(FROM "fvachaparambil@gmail.com" SINCE {since_date})'
            
            # Search for emails
            status, messages = mail.search(None, search_criteria)
            
            if status == 'OK':
                email_count = len(messages[0])
                print(f"Found {email_count} feedback emails to process")
                
                for email_id in messages[0]:
                    if email_id.decode() not in processed_emails:
                        # Fetch email
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        if status == 'OK':
                            # Parse email
                            email_message = email.message_from_bytes(msg_data[0][1])
                            subject = email_message['subject']
                            
                            # Extract date from subject
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', subject)
                            if date_match:
                                plan_date = date_match.group(1)
                                
                                print(f"📧 Processing feedback for {plan_date}")
                                
                                # Extract feedback
                                feedback = extracted_data['feedback']
                                journal_entries = extracted_data.get('journal_entries', [])
                                
                                # Store feedback in ZeroClaw memory and file
                                result = subprocess.run([
                                    'zeroclaw', 'memory', 'list', 
                                    '--key', f'baby_feedback_{plan_date}' 
                                ], capture_output=True, text=True, timeout=30)
                                
                                if result.returncode == 0:
                                    print(f"✅ Feedback stored in ZeroClaw memory for {plan_date}")
                                    print(f"Memory entry: baby_feedback_{plan_date}")
                                else:
                                    print(f"⚠️ Warning: Could not store feedback in memory: {result.stderr}")
                                
                                # Also store in a readable file for backup and query
                                memory_file = self.plan_dir / "memory_entries.json"
                                memory_data = {}
                                if memory_file.exists():
                                    with open(memory_file, 'r') as f:
                                        memory_data = json.load(f)
                                
                                memory_data[f'baby_feedback_{plan_date}'] = {
                                    'timestamp': datetime.now().isoformat(),
                                    'feedback': feedback,
                                    'journal_entries': journal_entries,
                                    'analysis': {
                                        'what_enjoyed': feedback.get('what_enjoyed', []),
                                        'didnt_like': feedback.get('didnt_like', []),
                                        'sleep_quality': feedback.get('sleep_quality', '5'),
                                        'feeding_response': feedback.get('feeding_response', 'Not specified'),
                                        'developmental': feedback.get('developmental', []),
                                        'preferences': self.generate_focus_areas(feedback),
                                        'schedule_adjustments': self.suggest_schedule_adjustments(feedback)
                                    }
                                }
                                
                                with open(memory_file, 'w') as f:
                                    json.dump(memory_data, f, indent=2)
                                
                                print(f"✅ Feedback also stored in memory_entries.json file")
                                
                                # Apply to plan
                                if self.apply_feedback_to_plan(plan_date, feedback):
                                    # Mark as processed
                                    self.save_processed_email(email_id.decode())
                                    print(f"✅ Feedback for {plan_date} processed and applied")
                                
            mail.close()
            mail.logout()
            
            print(f"📊 Processed {email_count} feedback emails")
            
        except Exception as e:
            print(f"❌ Error processing emails: {e}")

def main():
    processor = EmailFeedbackProcessor()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 email_feedback_processor.py process    # Process feedback emails")
        print("  python3 email_feedback_processor.py test      # Test email connection")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "process":
        processor.process_feedback_emails()
    elif command == "test":
        try:
            processor.connect_to_gmail()
            print("✅ Gmail connection test successful!")
        except Exception as e:
            print(f"❌ Gmail connection test failed: {e}")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
