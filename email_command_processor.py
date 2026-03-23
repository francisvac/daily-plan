#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Email Command Processor (Refactored)
Processes email commands for memory retrieval and journal management
"""

import imaplib
import email
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import EMAIL_SERVER_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES, EMAIL_COMMANDS
from base_classes import EmailBasedComponent, memory_manager
from logger import get_logger, log_error, log_success, log_warning

class EmailCommandProcessor(EmailBasedComponent):
    """Refactored email command processor with improved architecture"""
    
    def __init__(self):
        super().__init__("command_processor")
        self.processed_emails_file = Path.home() / "daily-plans" / "processed_emails.json"
        self._processed_emails = self._load_processed_emails()
    
    def _load_processed_emails(self) -> set:
        """Load set of processed email IDs"""
        try:
            if self.processed_emails_file.exists():
                with open(self.processed_emails_file, 'r') as f:
                    return set(json.load(f))
        except Exception as e:
            log_error(self.component_name, e, "loading processed emails")
        return set()
    
    def _save_processed_email(self, email_id: str) -> bool:
        """Save email ID as processed"""
        try:
            self._processed_emails.add(email_id)
            with open(self.processed_emails_file, 'w') as f:
                json.dump(list(self._processed_emails), f)
            return True
        except Exception as e:
            log_error(self.component_name, e, "saving processed email")
            return False
    
    def process_email_commands(self) -> bool:
        """Process incoming email commands"""
        if not self.is_configured():
            log_warning(self.component_name, ERROR_MESSAGES["config_not_found"])
            return False
        
        try:
            # Connect to Gmail
            with self._connect_to_gmail() as mail:
                # Search for recent emails
                messages = self._search_recent_emails(mail)
                
                if not messages:
                    self.logger.info("No new email commands found")
                    return True
                
                processed_count = 0
                for email_id in messages:
                    if email_id.decode() not in self._processed_emails:
                        if self._process_single_email(mail, email_id):
                            processed_count += 1
                
                log_success(self.component_name, f"Processed {processed_count} email commands")
                return True
                
        except Exception as e:
            log_error(self.component_name, e, "processing email commands")
            return False
    
    def _connect_to_gmail(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(
                EMAIL_SERVER_CONFIG["imap_server"], 
                EMAIL_SERVER_CONFIG["imap_port"]
            )
            mail.login(
                self.get_config("sender_email"), 
                self.get_config("app_password")
            )
            mail.select('inbox')
            return mail
        except Exception as e:
            log_error(self.component_name, e, "connecting to Gmail")
            raise
    
    def _search_recent_emails(self, mail: imaplib.IMAP4_SSL) -> List[bytes]:
        """Search for recent emails"""
        try:
            # Search for emails from last 24 hours
            since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            search_criteria = f'(FROM "{self.get_config("recipient_email")}" SINCE {since_date})'
            
            status, messages = mail.search(None, search_criteria)
            
            if status == 'OK':
                return messages[0].split()
            else:
                self.logger.warning(f"Email search failed: {status}")
                return []
                
        except Exception as e:
            log_error(self.component_name, e, "searching emails")
            return []
    
    def _process_single_email(self, mail: imaplib.IMAP4_SSL, email_id: bytes) -> bool:
        """Process a single email"""
        try:
            # Fetch email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                return False
            
            # Parse email
            email_message = email.message_from_bytes(msg_data[0][1])
            subject = email_message['subject'] or ''
            body = self._extract_email_body(email_message)
            
            # Process commands
            response = self._process_commands_from_body(body, subject)
            
            if response:
                # Send response
                self._send_command_response(subject, response)
                
                # Mark as processed
                self._save_processed_email(email_id.decode())
                return True
            
            return False
            
        except Exception as e:
            log_error(self.component_name, e, f"processing email {email_id}")
            return False
    
    def _extract_email_body(self, email_message) -> str:
        """Extract email body"""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        return part.get_payload(decode=True).decode()
            else:
                return email_message.get_payload(decode=True).decode()
        except Exception as e:
            log_error(self.component_name, e, "extracting email body")
            return ""
    
    def _process_commands_from_body(self, body: str, subject: str) -> Optional[str]:
        """Process commands from email body"""
        lines = body.strip().split('\n')
        responses = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('>'):
                continue
            
            # Parse command
            command_parts = line.split(maxsplit=1)
            if not command_parts:
                continue
            
            command = command_parts[0].lower()
            args = command_parts[1] if len(command_parts) > 1 else ""
            
            # Process command
            response = self._execute_command(command, args)
            if response:
                responses.append(response)
        
        return '\n\n'.join(responses) if responses else None
    
    def _execute_command(self, command: str, args: str) -> Optional[str]:
        """Execute a single command"""
        try:
            if command == "memory":
                return self._handle_memory_command(args)
            elif command == "feedback":
                return self._handle_feedback_command(args)
            elif command == "journal":
                return self._handle_journal_command(args)
            elif command == "patterns":
                return self._handle_patterns_command()
            elif command == "help":
                return self._handle_help_command()
            else:
                return f"Unknown command: {command}. Type 'help' for available commands."
                
        except Exception as e:
            log_error(self.component_name, e, f"executing command: {command}")
            return f"Error executing command '{command}': {str(e)}"
    
    def _handle_memory_command(self, args: str) -> str:
        """Handle memory commands"""
        if not args:
            return "Please specify a memory command: today, week, month, or search [keyword]"
        
        args = args.lower().strip()
        
        if args == "today":
            return self._get_today_memory()
        elif args == "week":
            return self._get_week_memory()
        elif args == "month":
            return self._get_month_memory()
        elif args.startswith("search"):
            keyword = args.replace("search", "").strip()
            if keyword:
                return self._search_memory(keyword)
            else:
                return "Please provide a keyword to search: memory search [keyword]"
        else:
            return f"Unknown memory command: {args}. Use: today, week, month, or search [keyword]"
    
    def _handle_feedback_command(self, args: str) -> str:
        """Handle feedback command"""
        if not args:
            return "Please provide feedback: feedback [your observation]"
        
        # Add feedback to today's memory
        today = datetime.now().strftime('%Y-%m-%d')
        key = f'baby_feedback_{today}'
        
        existing_entry = memory_manager.get_entry(key) or {
            'timestamp': datetime.now().isoformat(),
            'feedback': {
                'what_enjoyed': [],
                'didnt_like': [],
                'sleep_quality': '5',
                'feeding_response': 'Not specified',
                'developmental': []
            },
            'journal_entries': []
        }
        
        # Parse simple feedback
        feedback = existing_entry['feedback']
        if any(word in args.lower() for word in ['enjoyed', 'liked', 'loved']):
            feedback['what_enjoyed'].append(args)
        elif any(word in args.lower() for word in ['disliked', 'fussy', 'upset']):
            feedback['didnt_like'].append(args)
        
        memory_manager.add_entry(key, existing_entry)
        return f"✅ Feedback added: {args}"
    
    def _handle_journal_command(self, args: str) -> str:
        """Handle journal command"""
        if not args:
            return "Please provide a journal entry: journal [your note]"
        
        # Add journal entry to today's memory
        today = datetime.now().strftime('%Y-%m-%d')
        key = f'baby_feedback_{today}'
        
        existing_entry = memory_manager.get_entry(key) or {
            'timestamp': datetime.now().isoformat(),
            'feedback': {
                'what_enjoyed': [],
                'didnt_like': [],
                'sleep_quality': '5',
                'feeding_response': 'Not specified',
                'developmental': []
            },
            'journal_entries': []
        }
        
        # Add journal entry
        existing_entry['journal_entries'].append({
            'note': args,
            'time': datetime.now().strftime('%H:%M')
        })
        
        memory_manager.add_entry(key, existing_entry)
        return f"✅ Journal entry added: {args}"
    
    def _handle_patterns_command(self) -> str:
        """Handle patterns command"""
        summary = memory_manager.get_summary(7)
        
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
    
    def _handle_help_command(self) -> str:
        """Handle help command"""
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
    
    def _get_today_memory(self) -> str:
        """Get today's memory entries"""
        today = datetime.now().strftime('%Y-%m-%d')
        key = f'baby_feedback_{today}'
        
        entry = memory_manager.get_entry(key)
        if not entry:
            return f"📅 No memory entries found for {today}"
        
        # Calculate days old
        from base_classes import patterns_manager
        patterns = patterns_manager.get_baby_patterns()
        birth_date_str = patterns.get("birth_date", "2025-03-17")
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        days_old = (datetime.now().date() - birth_date).days
        
        age_display = f"{days_old} days old" if days_old > 0 else "Newborn"
        
        feedback = entry.get('feedback', {})
        journal_entries = entry.get('journal_entries', [])
        
        return f"""📅 Today's Memory ({today})
========================

👶 Baby's Day ({age_display}):
- Enjoyed: {', '.join(feedback.get('what_enjoyed', []))}
- Disliked: {', '.join(feedback.get('didnt_like', []))}
- Sleep Quality: {feedback.get('sleep_quality', 'N/A')}/10
- Feeding: {feedback.get('feeding_response', 'N/A')}

🎯 Developmental Notes:
{chr(10).join(f"- {note}" for note in feedback.get('developmental', []))}

📔 Parent Journal:
{chr(10).join(f"- {entry['note']} ({entry.get('time', 'Unknown time')})" for entry in journal_entries)}
"""
    
    def _get_week_memory(self) -> str:
        """Get last 7 days memory summary"""
        summary = memory_manager.get_summary(7)
        
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
    
    def _get_month_memory(self) -> str:
        """Get last 30 days memory summary"""
        summary = memory_manager.get_summary(30)
        
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
    
    def _search_memory(self, keyword: str) -> str:
        """Search memory entries"""
        results = memory_manager.search_entries(keyword)
        
        if not results:
            return f"🔍 No results found for '{keyword}'"
        
        response = f"🔍 Search Results for '{keyword}':\n\n"
        for key, entry in results[:10]:  # Limit to 10 results
            response += f"📅 {key.replace('baby_feedback_', '')}:\n"
            feedback = entry.get('feedback', {})
            response += f"  Enjoyed: {', '.join(feedback.get('what_enjoyed', []))}\n"
            response += f"  Sleep: {feedback.get('sleep_quality', 'N/A')}/10\n\n"
        
        return response
    
    def _send_command_response(self, original_subject: str, response: str) -> bool:
        """Send response email"""
        try:
            from email_integration_refactored import BabyPlanEmailer
            emailer = BabyPlanEmailer()
            return emailer.send_command_response(original_subject, response)
        except ImportError:
            log_warning(self.component_name, "Email integration not available")
            return False
        except Exception as e:
            log_error(self.component_name, e, "sending command response")
            return False

def main():
    """Main entry point"""
    import sys
    
    processor = EmailCommandProcessor()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 email_command_processor.py process    # Process email commands")
        print("  python3 email_command_processor.py test      # Test email connection")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "process":
        success = processor.process_email_commands()
        sys.exit(0 if success else 1)
    elif command == "test":
        if processor.is_configured():
            print("✅ Email configuration test successful!")
        else:
            print("❌ No email configuration found.")
        sys.exit(0)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
