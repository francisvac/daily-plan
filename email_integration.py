#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Email Integration (Refactored)
Sends daily baby plans via Gmail SMTP with improved architecture
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import EMAIL_SERVER_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES
from base_classes import EmailBasedComponent
from logger import get_logger, log_error, log_success, log_warning

class BabyPlanEmailer(EmailBasedComponent):
    """Refactored email integration with improved error handling"""
    
    def __init__(self):
        super().__init__("email_integration")
    
    def setup_config(self) -> bool:
        """Interactive setup for email configuration"""
        print("📧 Gmail Email Setup for Baby Plans")
        print("=====================================")
        print("")
        print("To send emails via Gmail, you'll need:")
        print("1. A Gmail address")
        print("2. An App Password (not your regular password)")
        print("   Get one at: https://myaccount.google.com/apppasswords")
        print("")
        
        try:
            config = {
                "sender_email": input("Your Gmail address: ").strip(),
                "app_password": input("Gmail App Password: ").strip(),
                "recipient_email": input("Recipient email (where to send plans): ").strip()
            }
            
            # Validate configuration
            if not all(config.values()):
                log_warning(self.component_name, "All email configuration fields are required")
                return False
            
            # Test the configuration
            print("\nTesting email configuration...")
            if self._test_connection(config):
                # Save configuration
                self._config = config
                if self._save_config():
                    print("✅ Configuration saved successfully!")
                    return True
                else:
                    print("❌ Failed to save configuration")
                    return False
            else:
                print("❌ Configuration test failed. Please check your settings.")
                return False
                
        except KeyboardInterrupt:
            print("\nSetup cancelled")
            return False
        except Exception as e:
            log_error(self.component_name, e, "during email setup")
            return False
    
    def _test_connection(self, config: Dict[str, Any]) -> bool:
        """Test email configuration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = config['sender_email']
            msg['To'] = config['recipient_email']
            msg['Subject'] = "🧪 ZeroClaw Baby Planner - Test Email"
            
            body = """
This is a test email from your ZeroClaw Baby Daily Planning System.

If you receive this, your email configuration is working correctly!

👶 Baby Daily Planner
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Send test email
            with smtplib.SMTP_SSL(
                EMAIL_SERVER_CONFIG["smtp_server"], 
                EMAIL_SERVER_CONFIG["smtp_port"]
            ) as server:
                server.login(config['sender_email'], config['app_password'])
                server.send_message(msg)
            
            log_success(self.component_name, "Test email sent successfully")
            return True
            
        except Exception as e:
            log_error(self.component_name, e, "testing email configuration")
            return False
    
    def send_plan_email(self, date: str, plan_content: str) -> bool:
        """Send daily baby plan via email"""
        if not self.is_configured():
            log_warning(self.component_name, ERROR_MESSAGES["config_not_found"])
            return False
        
        try:
            # Create message
            msg = self._create_email_message(
                recipient=self.get_config("recipient_email"),
                subject=f"👶 Baby Daily Plan - {date}",
                body=self._format_plan_email_body(date, plan_content)
            )
            
            # Send email
            if self._send_email(msg):
                log_success(self.component_name, f"Baby plan for {date} sent to {self.get_config('recipient_email')}")
                return True
            else:
                return False
                
        except Exception as e:
            log_error(self.component_name, e, f"sending plan email for {date}")
            return False
    
    def send_feedback_reminder(self, date: str) -> bool:
        """Send reminder to add feedback"""
        if not self.is_configured():
            return False
        
        try:
            msg = self._create_email_message(
                recipient=self.get_config("recipient_email"),
                subject=f"📝 Reminder: Add Baby Feedback for {date}",
                body=self._format_reminder_email_body(date)
            )
            
            return self._send_email(msg)
            
        except Exception as e:
            log_error(self.component_name, e, f"sending feedback reminder for {date}")
            return False
    
    def send_command_response(self, original_subject: str, response: str) -> bool:
        """Send response to email command"""
        if not self.is_configured():
            return False
        
        try:
            msg = self._create_email_message(
                recipient=self.get_config("recipient_email"),
                subject=f"Re: {original_subject}",
                body=self._format_command_response_body(response)
            )
            
            return self._send_email(msg)
            
        except Exception as e:
            log_error(self.component_name, e, "sending command response")
            return False
    
    def _create_email_message(self, recipient: str, subject: str, body: str) -> MIMEMultipart:
        """Create email message"""
        msg = MIMEMultipart()
        msg['From'] = self.get_config("sender_email")
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        return msg
    
    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email via SMTP"""
        try:
            with smtplib.SMTP_SSL(
                EMAIL_SERVER_CONFIG["smtp_server"], 
                EMAIL_SERVER_CONFIG["smtp_port"]
            ) as server:
                server.login(
                    self.get_config("sender_email"), 
                    self.get_config("app_password")
                )
                server.send_message(msg)
            return True
            
        except Exception as e:
            log_error(self.component_name, e, "sending email via SMTP")
            return False
    
    def _format_plan_email_body(self, date: str, plan_content: str) -> str:
        """Format plan email body"""
        return f"""👶 ZeroClaw Baby Daily Plan - {date}
==========================================

{plan_content}

---
Generated by ZeroClaw Baby Daily Planning System
📍 Server: agent1@10.0.0.231
🤖 AI-Powered Baby Activity Planning
"""
    
    def _format_reminder_email_body(self, date: str) -> str:
        """Format reminder email body"""
        return f"""📝 Baby Plan Feedback Reminder - {date}
=====================================

Don't forget to add feedback about today's baby activities!

Quick add feedback:
ssh agent1@10.0.0.231 "cd /home/agent1/daily-plans && ./daily-planner.sh feedback {date}"

Or use the remote manager:
./baby-planner-remote.sh feedback {date}

What to track:
✅ What baby enjoyed most
❌ What baby didn't like  
🎓 Sleep & feeding patterns
📝 Developmental observations

Your feedback helps the AI learn and improve tomorrow's plan!

👶 ZeroClaw Baby Daily Planner
"""
    
    def _format_command_response_body(self, response: str) -> str:
        """Format command response email body"""
        return f"""🤖 ZeroClaw Baby Planner Response
=====================================

{response}

---
📧 Sent by ZeroClaw Baby Daily Planning System
📍 Server: agent1@10.0.0.231
🤖 AI-Powered Baby Journal & Memory System
"""

class EmailTemplateManager:
    """Manages email templates and formatting"""
    
    @staticmethod
    def get_memory_summary_email(memory_data: Dict[str, Any]) -> str:
        """Format memory summary for email"""
        return f"""📊 Baby Memory Summary
=====================

📈 Statistics:
- Total Entries: {memory_data.get('total_entries', 0)}
- Average Sleep: {memory_data.get('avg_sleep', 0):.1f}/10

👶 Most Enjoyed Activities:
{chr(10).join(f"- {activity}" for activity in memory_data.get('most_enjoyed', []))}

😡 Common Dislikes:
{chr(10).join(f"- {activity}" for activity in memory_data.get('most_disliked', []))}

🎯 Developmental Progress:
{chr(10).join(f"- {note}" for note in memory_data.get('developmental_notes', []))}
"""
    
    @staticmethod
    def get_patterns_email(patterns: Dict[str, Any]) -> str:
        """Format patterns summary for email"""
        return f"""📊 Current Baby Patterns
========================

🎯 Focus Areas:
- Most Enjoyed: {patterns.get('most_enjoyed', 'None yet')}
- Avoid: {patterns.get('avoid', 'None yet')}

😴 Sleep Patterns:
- Average Quality: {patterns.get('avg_sleep', 0):.1f}/10
- Status: {'Good' if patterns.get('avg_sleep', 0) >= 7 else 'Needs attention'}

📈 Recommendations:
- Continue: {patterns.get('continue', 'Gentle activities')}
- Avoid: {patterns.get('avoid', 'Overstimulation')}
"""

def main():
    """Main entry point for email integration"""
    import sys
    
    emailer = BabyPlanEmailer()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 email_integration.py setup                    # Setup email configuration")
        print("  python3 email_integration.py send <date>              # Send plan for date")
        print("  python3 email_integration.py reminder <date>         # Send feedback reminder")
        print("  python3 email_integration.py test                     # Test email configuration")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        success = emailer.setup_config()
        sys.exit(0 if success else 1)
    
    elif command == "send":
        if len(sys.argv) < 3:
            print("Please provide a date: YYYY-MM-DD")
            sys.exit(1)
        
        date = sys.argv[2]
        plan_file = Path.home() / "daily-plans" / f"{date}-plan.md"
        
        if not plan_file.exists():
            print(f"No plan found for {date}")
            sys.exit(1)
        
        with open(plan_file, 'r') as f:
            plan_content = f.read()
        
        success = emailer.send_plan_email(date, plan_content)
        sys.exit(0 if success else 1)
    
    elif command == "reminder":
        if len(sys.argv) < 3:
            print("Please provide a date: YYYY-MM-DD")
            sys.exit(1)
        
        date = sys.argv[2]
        success = emailer.send_feedback_reminder(date)
        sys.exit(0 if success else 1)
    
    elif command == "test":
        if emailer.is_configured():
            if emailer._test_connection(emailer._config):
                print("✅ Email configuration test passed!")
            else:
                print("❌ Email configuration test failed!")
        else:
            print("❌ No email configuration found. Run setup first.")
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
