#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Email Diagnostic Tool
Comprehensive diagnostic tool for email sending and receiving issues
"""

import json
import imaplib
import smtplib
import ssl
import sys
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import ZeroClaw components
try:
    from config import EMAIL_SERVER_CONFIG, EMAIL_CONFIG_FILE
    from base_classes import EmailBasedComponent
    from email_integration import BabyPlanEmailer
    from email_command_processor import EmailCommandProcessor
    from logger import get_logger
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the daily-plans directory")
    sys.exit(1)

class DiagnosticResult:
    """Single diagnostic test result"""
    def __init__(self, test_name: str, success: bool, message: str, details: str = ""):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.details = details
        self.timestamp = datetime.now().isoformat()
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.test_name}: {self.message}"

class DiagnosticResults:
    """Collection of diagnostic results"""
    def __init__(self):
        self.results: List[DiagnosticResult] = []
        self.start_time = datetime.now()
    
    def add_result(self, result: DiagnosticResult):
        self.results.append(result)
    
    def print_summary(self):
        print("\n" + "="*50)
        print("🔍 ZeroClaw Email Diagnostic Results")
        print("="*50)
        
        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        
        for result in self.results:
            print(result)
            if result.details:
                print(f"   Details: {result.details}")
        
        print(f"\n📊 Summary: {passed}/{total} tests passed")
        
        # Show issues and recommendations
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            print("\n📋 Issues Found:")
            for i, result in enumerate(failed_results, 1):
                print(f"{i}. {result.message}")
            
            print("\n🔧 Recommended Actions:")
            self._print_recommendations(failed_results)
        else:
            print("\n🎉 All tests passed! Email system is working correctly.")
    
    def _print_recommendations(self, failed_results: List[DiagnosticResult]):
        recommendations = []
        
        for result in failed_results:
            if "Configuration" in result.test_name:
                recommendations.extend([
                    "1. Create email configuration file",
                    "   Run: python3 email_diagnostic.py setup-wizard",
                    "2. Check file permissions on email_config.json"
                ])
            elif "Authentication" in result.test_name:
                recommendations.extend([
                    "1. Generate new Gmail App Password",
                    "   Visit: https://myaccount.google.com/apppasswords",
                    "2. Enable 2-factor authentication on Gmail account",
                    "3. Use App Password (not regular password)"
                ])
            elif "SMTP" in result.test_name:
                recommendations.extend([
                    "1. Check network connectivity to smtp.gmail.com:465",
                    "2. Verify firewall allows SMTP connections",
                    "3. Confirm Gmail account allows less secure apps"
                ])
            elif "IMAP" in result.test_name:
                recommendations.extend([
                    "1. Check network connectivity to imap.gmail.com:993",
                    "2. Enable IMAP in Gmail settings",
                    "3. Verify Gmail account allows IMAP access"
                ])
            elif "Sending" in result.test_name:
                recommendations.extend([
                    "1. Verify recipient email address is correct",
                    "2. Check Gmail sending limits",
                    "3. Confirm email content formatting"
                ])
            elif "Receiving" in result.test_name:
                recommendations.extend([
                    "1. Check emails are being sent to correct address",
                    "2. Verify email search criteria (last 24 hours)",
                    "3. Check processed_emails.json file"
                ])
        
        # Remove duplicates and print
        unique_recommendations = list(dict.fromkeys(recommendations))
        for rec in unique_recommendations[:10]:  # Limit to 10 recommendations
            print(rec)

class EmailDiagnostic:
    """Main diagnostic tool class"""
    
    def __init__(self):
        self.logger = get_logger("email_diagnostic")
        self.results = DiagnosticResults()
        self.config_file = EMAIL_CONFIG_FILE
    
    def check_configuration(self) -> DiagnosticResult:
        """Check email configuration file"""
        try:
            if not self.config_file.exists():
                return DiagnosticResult(
                    "Configuration File",
                    False,
                    "Configuration file not found",
                    f"Expected at: {self.config_file}"
                )
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            required_fields = ["sender_email", "app_password", "recipient_email"]
            missing_fields = [field for field in required_fields if field not in config or not config[field]]
            
            if missing_fields:
                return DiagnosticResult(
                    "Configuration File",
                    False,
                    f"Missing required fields: {', '.join(missing_fields)}",
                    "Run setup wizard to create complete configuration"
                )
            
            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            for field in ["sender_email", "recipient_email"]:
                if not re.match(email_pattern, config[field]):
                    return DiagnosticResult(
                        "Configuration File",
                        False,
                        f"Invalid email format in {field}",
                        f"Email should match pattern: {email_pattern}"
                    )
            
            return DiagnosticResult(
                "Configuration File",
                True,
                "Configuration file is valid",
                f"Found {len(config)} configuration fields"
            )
            
        except json.JSONDecodeError as e:
            return DiagnosticResult(
                "Configuration File",
                False,
                "Invalid JSON format",
                f"JSON error: {str(e)}"
            )
        except Exception as e:
            return DiagnosticResult(
                "Configuration File",
                False,
                "Error reading configuration",
                f"Error: {str(e)}"
            )
    
    def test_smtp_authentication(self) -> DiagnosticResult:
        """Test Gmail SMTP authentication"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            server = smtplib.SMTP_SSL(
                EMAIL_SERVER_CONFIG["smtp_server"], 
                EMAIL_SERVER_CONFIG["smtp_port"]
            )
            server.login(config["sender_email"], config["app_password"])
            server.quit()
            
            return DiagnosticResult(
                "SMTP Authentication",
                True,
                "Gmail SMTP authentication successful",
                "Connected to smtp.gmail.com:465"
            )
            
        except smtplib.SMTPAuthenticationError as e:
            return DiagnosticResult(
                "SMTP Authentication",
                False,
                "Authentication failed",
                "Check email and app password. Generate new App Password if needed."
            )
        except smtplib.SMTPException as e:
            return DiagnosticResult(
                "SMTP Authentication",
                False,
                "SMTP connection failed",
                f"SMTP error: {str(e)}"
            )
        except Exception as e:
            return DiagnosticResult(
                "SMTP Authentication",
                False,
                "Connection error",
                f"Error: {str(e)}"
            )
    
    def test_imap_authentication(self) -> DiagnosticResult:
        """Test Gmail IMAP authentication"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            mail = imaplib.IMAP4_SSL(
                EMAIL_SERVER_CONFIG["imap_server"], 
                EMAIL_SERVER_CONFIG["imap_port"]
            )
            mail.login(config["sender_email"], config["app_password"])
            mail.select('inbox')
            mail.logout()
            
            return DiagnosticResult(
                "IMAP Authentication",
                True,
                "Gmail IMAP authentication successful",
                "Connected to imap.gmail.com:993"
            )
            
        except imaplib.IMAP4.error as e:
            return DiagnosticResult(
                "IMAP Authentication",
                False,
                "IMAP connection failed",
                f"IMAP error: {str(e)}. Check if IMAP is enabled in Gmail."
            )
        except Exception as e:
            return DiagnosticResult(
                "IMAP Authentication",
                False,
                "Connection error",
                f"Error: {str(e)}"
            )
    
    def test_email_sending(self) -> DiagnosticResult:
        """Test email sending functionality"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Create test email
            msg = MIMEMultipart()
            msg['From'] = config['sender_email']
            msg['To'] = config['recipient_email']
            msg['Subject'] = "🧪 ZeroClaw Email Diagnostic Test"
            
            body = f"""
This is a test email from ZeroClaw Email Diagnostic Tool.

Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Purpose: Verify email sending functionality

If you receive this email, the sending system is working correctly!
👶 ZeroClaw Baby Planner
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP_SSL(
                EMAIL_SERVER_CONFIG["smtp_server"], 
                EMAIL_SERVER_CONFIG["smtp_port"]
            ) as server:
                server.login(config['sender_email'], config['app_password'])
                server.send_message(msg)
            
            return DiagnosticResult(
                "Email Sending",
                True,
                "Test email sent successfully",
                f"Sent to: {config['recipient_email']}"
            )
            
        except Exception as e:
            return DiagnosticResult(
                "Email Sending",
                False,
                "Failed to send test email",
                f"Error: {str(e)}"
            )
    
    def test_email_receiving(self) -> DiagnosticResult:
        """Test email receiving functionality"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            processor = EmailCommandProcessor()
            
            # Check if we can connect and search
            with processor._connect_to_gmail() as mail:
                # Search for recent emails
                messages = processor._search_recent_emails(mail)
                
                if messages is None:
                    return DiagnosticResult(
                        "Email Receiving",
                        False,
                        "Failed to search emails",
                        "IMAP search returned None"
                    )
                
                return DiagnosticResult(
                    "Email Receiving",
                    True,
                    f"Found {len(messages)} recent emails",
                    f"Searching for emails from: {config['recipient_email']}"
                )
                
        except Exception as e:
            return DiagnosticResult(
                "Email Receiving",
                False,
                "Failed to test email receiving",
                f"Error: {str(e)}"
            )
    
    def run_full_diagnostic(self) -> DiagnosticResults:
        """Run complete diagnostic suite"""
        print("🔍 Starting ZeroClaw Email Diagnostic...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        # Test configuration
        config_result = self.check_configuration()
        self.results.add_result(config_result)
        
        if not config_result.success:
            # If config fails, we can't continue with other tests
            self.results.print_summary()
            return self.results
        
        # Test SMTP authentication
        smtp_result = self.test_smtp_authentication()
        self.results.add_result(smtp_result)
        
        # Test IMAP authentication  
        imap_result = self.test_imap_authentication()
        self.results.add_result(imap_result)
        
        # Test email sending (if SMTP auth worked)
        if smtp_result.success:
            sending_result = self.test_email_sending()
            self.results.add_result(sending_result)
        
        # Test email receiving (if IMAP auth worked)
        if imap_result.success:
            receiving_result = self.test_email_receiving()
            self.results.add_result(receiving_result)
        
        return self.results
    
    def setup_wizard(self):
        """Interactive setup wizard for email configuration"""
        print("📧 ZeroClaw Email Setup Wizard")
        print("="*40)
        print("")
        print("This wizard will help you configure Gmail for ZeroClaw.")
        print("You'll need:")
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
                print("❌ All fields are required. Setup cancelled.")
                return False
            
            # Test the configuration
            print("\nTesting configuration...")
            
            # Save temporary config for testing
            temp_config_file = self.config_file.with_suffix('.tmp.json')
            with open(temp_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Temporarily use this config
            original_config_file = self.config_file
            self.config_file = temp_config_file
            
            # Test authentication
            smtp_result = self.test_smtp_authentication()
            imap_result = self.test_imap_authentication()
            
            # Restore original config file path
            self.config_file = original_config_file
            
            if smtp_result.success and imap_result.success:
                # Save the actual configuration
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                # Clean up temp file
                temp_config_file.unlink()
                
                print("✅ Configuration saved successfully!")
                print(f"   Configuration file: {self.config_file}")
                return True
            else:
                print("❌ Configuration test failed:")
                if not smtp_result.success:
                    print(f"   SMTP: {smtp_result.message}")
                if not imap_result.success:
                    print(f"   IMAP: {imap_result.message}")
                
                # Clean up temp file
                if temp_config_file.exists():
                    temp_config_file.unlink()
                
                return False
                
        except KeyboardInterrupt:
            print("\nSetup cancelled")
            return False
        except Exception as e:
            print(f"❌ Setup error: {e}")
            return False

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "full-test"
    
    diagnostic = EmailDiagnostic()
    
    if command == "setup-wizard":
        diagnostic.setup_wizard()
    elif command == "check-config":
        result = diagnostic.check_configuration()
        diagnostic.results.add_result(result)
        diagnostic.results.print_summary()
    elif command == "test-sending":
        config_result = diagnostic.check_configuration()
        diagnostic.results.add_result(config_result)
        
        if config_result.success:
            sending_result = diagnostic.test_email_sending()
            diagnostic.results.add_result(sending_result)
        
        diagnostic.results.print_summary()
    elif command == "test-receiving":
        config_result = diagnostic.check_configuration()
        diagnostic.results.add_result(config_result)
        
        if config_result.success:
            receiving_result = diagnostic.test_email_receiving()
            diagnostic.results.add_result(receiving_result)
        
        diagnostic.results.print_summary()
    elif command == "full-test":
        diagnostic.run_full_diagnostic()
        diagnostic.results.print_summary()
    else:
        print("Usage:")
        print("  python3 email_diagnostic.py [command]")
        print("")
        print("Commands:")
        print("  setup-wizard   - Interactive configuration setup")
        print("  check-config   - Validate email configuration only")
        print("  test-sending   - Test email sending functionality")
        print("  test-receiving - Test email receiving functionality")
        print("  full-test      - Complete diagnostic suite (default)")
        print("")
        print("Examples:")
        print("  python3 email_diagnostic.py")
        print("  python3 email_diagnostic.py setup-wizard")
        print("  python3 email_diagnostic.py test-sending")

if __name__ == "__main__":
    main()
