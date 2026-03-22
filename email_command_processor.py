#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Email Command Processor
Processes email commands for memory retrieval and journal management
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

class EmailCommandProcessor:
    def __init__(self):
        self.config_file = Path.home() / "daily-plans" / "email_config.json"
        self.plan_dir = Path.home() / "daily-plans"
        self.memory_file = self.plan_dir / "memory_entries.json"
        
    def load_config(self):
        """Load email configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return None
    
    def load_memory(self):
        """Load memory entries"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_memory(self, memory_data):
        """Save memory entries"""
        with open(self.memory_file, 'w') as f:
            json.dump(memory_data, f, indent=2)
    
    def get_memory_summary(self, days=7):
        """Get memory summary for specified days"""
        memory = self.load_memory()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        summary = {
            'total_entries': 0,
            'enjoyed_activities': [],
            'disliked_activities': [],
            'sleep_ratings': [],
            'developmental_notes': [],
            'journal_entries': []
        }
        
        for key, entry in memory.items():
            if key.startswith('baby_feedback_'):
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if entry_date >= cutoff_date:
                    summary['total_entries'] += 1
                    feedback = entry['feedback']
                    
                    # Collect data
                    summary['enjoyed_activities'].extend(feedback.get('what_enjoyed', []))
                    summary['disliked_activities'].extend(feedback.get('didnt_like', []))
                    
                    if feedback.get('sleep_quality'):
                        try:
                            summary['sleep_ratings'].append(int(feedback['sleep_quality']))
                        except ValueError:
                            pass
                    
                    summary['developmental_notes'].extend(feedback.get('developmental', []))
        
        # Process summary
        summary['most_enjoyed'] = list(set(summary['enjoyed_activities']))[:5]
        summary['most_disliked'] = list(set(summary['disliked_activities']))[:3]
        summary['avg_sleep'] = sum(summary['sleep_ratings']) / len(summary['sleep_ratings']) if summary['sleep_ratings'] else 0
        
        return summary
    
    def search_memory(self, keyword):
        """Search memory entries for keyword"""
        memory = self.load_memory()
        results = []
        
        for key, entry in memory.items():
            if key.startswith('baby_feedback_'):
                # Search in feedback content
                feedback_str = json.dumps(entry).lower()
                if keyword.lower() in feedback_str:
                    results.append({
                        'date': key.replace('baby_feedback_', ''),
                        'entry': entry
                    })
        
        return results
    
    def process_email_commands(self):
        """Process incoming email commands"""
        print("🔍 Processing email commands...")
        
        try:
            config = self.load_config()
            if not config:
                raise Exception("Email configuration not found")
            
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            mail.login(config['sender_email'], config['app_password'])
            mail.select('inbox')
            
            # Search for recent emails (last 24 hours)
            since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            search_criteria = f'(FROM "fvachaparambil@gmail.com" SINCE {since_date})'
            
            status, messages = mail.search(None, search_criteria)
            
            if status == 'OK':
                for email_id in messages[0]:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if status == 'OK':
                        email_message = email.message_from_bytes(msg_data[0][1])
                        subject = email_message['subject']
                        
                        # Extract email body
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = email_message.get_payload(decode=True).decode()
                        
                        # Process commands
                        response = self.process_command(body, subject)
                        
                        if response:
                            self.send_response_email(config, subject, response)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"❌ Error processing email commands: {e}")
    
    def process_command(self, body, subject):
        """Process individual command from email body"""
        lines = body.strip().split('\n')
        responses = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('>'):
                continue
                
            # Memory commands
            if line.startswith('memory today'):
                today = datetime.now().strftime('%Y-%m-%d')
                response = self.get_today_memory(today)
                responses.append(response)
                
            elif line.startswith('memory week'):
                response = self.get_week_memory()
                responses.append(response)
                
            elif line.startswith('memory month'):
                response = self.get_month_memory()
                responses.append(response)
                
            elif line.startswith('memory search'):
                keyword = line.replace('memory search', '').strip()
                if keyword:
                    response = self.search_memory_results(keyword)
                    responses.append(response)
                    
            elif line.startswith('patterns'):
                response = self.get_patterns_summary()
                responses.append(response)
                
            elif line.startswith('journal'):
                journal_note = line.replace('journal', '').strip()
                if journal_note:
                    response = self.add_journal_entry(journal_note)
                    responses.append(response)
                    
            elif line.startswith('feedback'):
                feedback_note = line.replace('feedback', '').strip()
                if feedback_note:
                    response = self.add_feedback_entry(feedback_note)
                    responses.append(response)
                    
            elif line.startswith('help'):
                response = self.get_help_info()
                responses.append(response)
        
        return '\n\n'.join(responses) if responses else None
    
    def get_today_memory(self, date):
        """Get today's memory entries"""
        memory = self.load_memory()
        key = f'baby_feedback_{date}'
        
        if key in memory:
            entry = memory[key]
            # Calculate days old for newborn
            entry_date = datetime.fromisoformat(entry['timestamp'])
            today = datetime.now()
            days_old = (today - entry_date).days
            
            age_display = f"{days_old} days old" if days_old > 0 else "Newborn"
            
            return f"""📅 Today's Memory ({date})
========================

👶 Baby's Day ({age_display}):
- Enjoyed: {', '.join(entry['feedback'].get('what_enjoyed', []))}
- Disliked: {', '.join(entry['feedback'].get('didnt_like', []))}
- Sleep Quality: {entry['feedback'].get('sleep_quality', 'N/A')}/10
- Feeding: {entry['feedback'].get('feeding_response', 'N/A')}

🎯 Developmental Notes:
{chr(10).join(f"- {note}" for note in entry['feedback'].get('developmental', []))}

📔 Parent Journal:
{chr(10).join(f"- {note}" for note in entry.get('journal_entries', []))}
"""
    
    def get_week_memory(self):
        """Get last 7 days memory summary"""
        summary = self.get_memory_summary(7)
        
        return f"""📊 Last 7 Days Summary
========================

📈 Statistics:
- Total Entries: {summary['total_entries']}
- Average Sleep: {summary['avg_sleep']:.1f}/10

👶 Most Enjoyed Activities:
{chr(10).join(f"- {activity}" for activity in summary['most_enjoyed'])}

😡 Common Dislikes:
{chr(10).join(f"- {activity}" for activity in summary['most_disliked'])}

🎯 Developmental Progress:
{chr(10).join(f"- {note}" for note in summary['developmental_notes'][:5])}
"""
    
    def get_month_memory(self):
        """Get last 30 days memory summary"""
        summary = self.get_memory_summary(30)
        
        return f"""📊 Last 30 Days Summary
==========================

📈 Statistics:
- Total Entries: {summary['total_entries']}
- Average Sleep: {summary['avg_sleep']:.1f}/10

👶 Top Enjoyed Activities:
{chr(10).join(f"- {activity}" for activity in summary['most_enjoyed'])}

😡 Top Dislikes:
{chr(10).join(f"- {activity}" for activity in summary['most_disliked'])}

🎯 Key Developmental Notes:
{chr(10).join(f"- {note}" for note in summary['developmental_notes'][:10])}
"""
    
    def search_memory_results(self, keyword):
        """Search memory and return results"""
        results = self.search_memory(keyword)
        
        if not results:
            return f"🔍 No results found for '{keyword}'"
        
        response = f"🔍 Search Results for '{keyword}':\n\n"
        for result in results[:10]:  # Limit to 10 results
            response += f"📅 {result['date']}:\n"
            feedback = result['entry']['feedback']
            response += f"  Enjoyed: {', '.join(feedback.get('what_enjoyed', []))}\n"
            response += f"  Sleep: {feedback.get('sleep_quality', 'N/A')}/10\n\n"
        
        return response
    
    def get_patterns_summary(self):
        """Get current patterns summary"""
        summary = self.get_memory_summary(7)
        
        return f"""📊 Current Baby Patterns
========================

🎯 Focus Areas:
- Most Enjoyed: {summary['most_enjoyed'][0] if summary['most_enjoyed'] else 'None yet'}
- Avoid: {summary['most_disliked'][0] if summary['most_disliked'] else 'None yet'}

😴 Sleep Patterns:
- Average Quality: {summary['avg_sleep']:.1f}/10
- Status: {'Good' if summary['avg_sleep'] >= 7 else 'Needs attention'}

📈 Recommendations:
- Continue: {summary['most_enjoyed'][0] if summary['most_enjoyed'] else 'Gentle activities'}
- Avoid: {summary['most_disliked'][0] if summary['most_disliked'] else 'Overstimulation'}
"""
    
    def add_journal_entry(self, note):
        """Add journal entry to today's memory"""
        today = datetime.now().strftime('%Y-%m-%d')
        memory = self.load_memory()
        key = f'baby_feedback_{today}'
        
        if key not in memory:
            memory[key] = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'Not specified',
                    'developmental': []
                },
                'parent_journal': []
            }
        
        # Add journal note
        if 'parent_journal' not in memory[key]:
            memory[key]['parent_journal'] = []
        
        memory[key]['parent_journal'].append({
            'note': note,
            'time': datetime.now().strftime('%H:%M')
        })
        
        self.save_memory(memory)
        return f"✅ Journal entry added: {note}"
    
    def add_feedback_entry(self, feedback_text):
        """Add feedback entry to today's memory"""
        today = datetime.now().strftime('%Y-%m-%d')
        memory = self.load_memory()
        key = f'baby_feedback_{today}'
        
        if key not in memory:
            memory[key] = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'Not specified',
                    'developmental': []
                }
            }
        
        # Parse simple feedback
        feedback = memory[key]['feedback']
        
        # Simple keyword matching
        if 'enjoyed' in feedback_text.lower() or 'liked' in feedback_text.lower():
            feedback['what_enjoyed'].append(feedback_text)
        elif 'disliked' in feedback_text.lower() or 'fussy' in feedback_text.lower():
            feedback['didnt_like'].append(feedback_text)
        
        self.save_memory(memory)
        return f"✅ Feedback added: {feedback_text}"
    
    def get_help_info(self):
        """Get help information"""
        return """📧 Available Email Commands:
============================

📊 Memory Retrieval:
- memory today - Get today's journal entries
- memory week - Get last 7 days summary  
- memory month - Get last 30 days summary
- memory search [keyword] - Search journal entries

📝 Quick Actions:
- feedback [observation] - Add quick feedback
- journal [note] - Add journal entry
- patterns - Get current patterns summary

ℹ️ Help:
- help - Show this help message

Examples:
- memory week
- memory search sleep
- feedback Baby loved tummy time
- journal Had a great day with lots of smiles
- patterns
"""
    
    def send_response_email(self, config, original_subject, response):
        """Send response email"""
        try:
            msg = email.message.EmailMessage()
            msg['From'] = config['sender_email']
            msg['To'] = config['recipient_email']
            msg['Subject'] = f"Re: {original_subject}"
            
            body = f"""🤖 ZeroClaw Baby Planner Response
=====================================

{response}

---
📧 Sent by ZeroClaw Baby Daily Planning System
📍 Server: agent1@10.0.0.231
🤖 AI-Powered Baby Journal & Memory System
"""
            
            msg.set_content(body)
            
            # Send email
            import smtplib
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(config['sender_email'], config['app_password'])
                server.send_message(msg)
            
            print(f"✅ Response sent to {config['recipient_email']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send response: {e}")
            return False

def main():
    processor = EmailCommandProcessor()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 email_command_processor.py process    # Process email commands")
        print("  python3 email_command_processor.py test      # Test email connection")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "process":
        processor.process_email_commands()
    elif command == "test":
        config = processor.load_config()
        if config:
            print("✅ Email configuration test successful!")
        else:
            print("❌ No email configuration found.")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
