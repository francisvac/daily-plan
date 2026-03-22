#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - EmailCommandProcessor Unit Tests
Comprehensive testing of email command processing and feedback handling
"""

import email
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest

from email_command_processor import EmailCommandProcessor


class TestEmailCommandProcessor:
    """Test suite for EmailCommandProcessor class"""

    def test_processor_initialization(self, mock_base_dir):
        """Test EmailCommandProcessor initializes correctly"""
        processed_file = mock_base_dir / "processed_emails.json"
        
        with patch("email_command_processor.EmailCommandProcessor") as mock_processor_class:
            # Create instance with mocked file path
            processor_instance = EmailCommandProcessor.__new__(EmailCommandProcessor)
            processor_instance.component_name = "command_processor"
            processor_instance.processed_emails_file = processed_file
            processor_instance._processed_emails = set()
            
            assert processor_instance.component_name == "command_processor"
            assert hasattr(processor_instance, '_processed_emails')
            assert isinstance(processor_instance._processed_emails, set)

    def test_load_processed_emails_empty(self, mock_base_dir):
        """Test loading processed emails when file doesn't exist"""
        processed_file = mock_base_dir / "processed_emails.json"
        
        # Create processor instance manually
        processor = EmailCommandProcessor.__new__(EmailCommandProcessor)
        processor.component_name = "command_processor"
        processor.processed_emails_file = processed_file
        processor._processed_emails = set()
        
        # Load emails (file doesn't exist)
        processor._load_processed_emails()
        assert processor._processed_emails == set()

    def test_load_processed_emails_existing(self, mock_base_dir):
        """Test loading existing processed emails"""
        processed_file = mock_base_dir / "processed_emails.json"
        test_emails = ["email1@example.com", "email2@example.com"]
        processed_file.write_text('["email1@example.com", "email2@example.com"]')
        
        # Create processor instance manually
        processor = EmailCommandProcessor.__new__(EmailCommandProcessor)
        processor.component_name = "command_processor"
        processor.processed_emails_file = processed_file
        processor._processed_emails = set()
        
        # Load existing emails
        processor._load_processed_emails()
        assert processor._processed_emails == set(test_emails)

    def test_save_processed_email(self, mock_base_dir):
        """Test saving processed email ID"""
        processed_file = mock_base_dir / "processed_emails.json"
        
        with patch("base_classes.PROCESSED_EMAILS_FILE", processed_file):
            processor = EmailCommandProcessor()
            
            email_id = "test_email_123"
            result = processor._save_processed_email(email_id)
            
            assert result is True
            assert email_id in processor._processed_emails
            
            # Verify file was saved
            if processed_file.exists():
                saved_emails = set(processed_file.read_text().strip('[]').replace('"', '').split(','))
                assert email_id in saved_emails

    def test_parse_email_command_memory(self, processor_with_mocks):
        """Test parsing memory command"""
        processor = processor_with_mocks
        
        # Test memory command with args
        args = "week"
        result = processor._parse_email_command("memory", args)
        
        assert result["command"] == "memory"
        assert result["args"] == "week"

    def test_parse_email_command_feedback(self, processor_with_mocks):
        """Test parsing feedback command"""
        processor = processor_with_mocks
        
        args = "Baby loved tummy time today"
        result = processor._parse_email_command("feedback", args)
        
        assert result["command"] == "feedback"
        assert result["args"] == "Baby loved tummy time today"

    def test_parse_email_command_journal(self, processor_with_mocks):
        """Test parsing journal command"""
        processor = processor_with_mocks
        
        args = "Had a great morning with smiles"
        result = processor._parse_email_command("journal", args)
        
        assert result["command"] == "journal"
        assert result["args"] == "Had a great morning with smiles"

    def test_parse_email_command_patterns(self, processor_with_mocks):
        """Test parsing patterns command"""
        processor = processor_with_mocks
        
        result = processor._parse_email_command("patterns", "")
        
        assert result["command"] == "patterns"
        assert result["args"] == ""

    def test_parse_email_command_unknown(self, processor_with_mocks):
        """Test parsing unknown command"""
        processor = processor_with_mocks
        
        result = processor._parse_email_command("unknown", "args")
        
        assert result["command"] == "unknown"
        assert result["args"] == "args"

    def test_handle_memory_command_today(self, processor_with_mocks, memory_manager):
        """Test handling memory today command"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'get_entries_in_date_range') as mock_get_entries:
            mock_get_entries.return_value = []
            
            result = processor._handle_memory_command("today")
            
            assert "Today's Memory" in result
            mock_get_entries.assert_called_once()

    def test_handle_memory_command_week(self, processor_with_mocks, memory_manager):
        """Test handling memory week command"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'get_entries_in_date_range') as mock_get_entries:
            mock_get_entries.return_value = []
            
            result = processor._handle_memory_command("week")
            
            assert "This Week's Memory" in result
            mock_get_entries.assert_called_once()

    def test_handle_memory_command_month(self, processor_with_mocks, memory_manager):
        """Test handling memory month command"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'get_entries_in_date_range') as mock_get_entries:
            mock_get_entries.return_value = []
            
            result = processor._handle_memory_command("month")
            
            assert "This Month's Memory" in result
            mock_get_entries.assert_called_once()

    def test_handle_memory_command_search(self, processor_with_mocks, memory_manager):
        """Test handling memory search command"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'search_entries') as mock_search:
            mock_search.return_value = []
            
            result = processor._handle_memory_command("search tummy")
            
            assert "Search Results" in result
            mock_search.assert_called_once_with("tummy")

    def test_handle_memory_command_invalid(self, processor_with_mocks):
        """Test handling invalid memory command"""
        processor = processor_with_mocks
        
        result = processor._handle_memory_command("invalid_command")
        
        assert "Unknown memory command" in result

    def test_handle_feedback_command_enjoyed(self, processor_with_mocks, memory_manager):
        """Test handling feedback with enjoyed activity"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'add_entry') as mock_add, \
             patch.object(memory_manager, 'get_entry') as mock_get:
            
            mock_get.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'normal',
                    'developmental': []
                },
                'journal_entries': []
            }
            
            result = processor._handle_feedback_command("Baby really enjoyed tummy time today")
            
            assert "✅ Feedback added" in result
            mock_add.assert_called_once()

    def test_handle_feedback_command_disliked(self, processor_with_mocks, memory_manager):
        """Test handling feedback with disliked activity"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'add_entry') as mock_add, \
             patch.object(memory_manager, 'get_entry') as mock_get:
            
            mock_get.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'normal',
                    'developmental': []
                },
                'journal_entries': []
            }
            
            result = processor._handle_feedback_command("Baby was fussy during loud noises")
            
            assert "✅ Feedback added" in result
            mock_add.assert_called_once()

    def test_handle_feedback_command_empty(self, processor_with_mocks):
        """Test handling empty feedback command"""
        processor = processor_with_mocks
        
        result = processor._handle_feedback_command("")
        
        assert "Please provide feedback" in result

    def test_handle_journal_command(self, processor_with_mocks, memory_manager):
        """Test handling journal command"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'add_entry') as mock_add, \
             patch.object(memory_manager, 'get_entry') as mock_get:
            
            mock_get.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': [],
                    'didnt_like': [],
                    'sleep_quality': '5',
                    'feeding_response': 'normal',
                    'developmental': []
                },
                'journal_entries': []
            }
            
            result = processor._handle_journal_command("Great day with lots of smiles")
            
            assert "✅ Journal entry added" in result
            mock_add.assert_called_once()

    def test_handle_journal_command_empty(self, processor_with_mocks):
        """Test handling empty journal command"""
        processor = processor_with_mocks
        
        result = processor._handle_journal_command("")
        
        assert "Please provide a journal entry" in result

    def test_handle_patterns_command(self, processor_with_mocks, patterns_manager):
        """Test handling patterns command"""
        processor = processor_with_mocks
        
        with patch.object(patterns_manager, 'get_patterns') as mock_get_patterns, \
             patch.object(patterns_manager, 'get_baby_patterns') as mock_get_baby:
            
            mock_get_patterns.return_value = {"patterns": "test"}
            mock_get_baby.return_value = {"age_months": 2}
            
            result = processor._handle_patterns_command("")
            
            assert "Current Baby Patterns" in result
            mock_get_patterns.assert_called_once()
            mock_get_baby.assert_called_once()

    def test_execute_command_memory(self, processor_with_mocks):
        """Test executing memory command"""
        processor = processor_with_mocks
        
        with patch.object(processor, '_handle_memory_command') as mock_handle:
            mock_handle.return_value = "Memory result"
            
            result = processor._execute_command({"command": "memory", "args": "week"})
            
            assert result == "Memory result"
            mock_handle.assert_called_once_with("week")

    def test_execute_command_feedback(self, processor_with_mocks):
        """Test executing feedback command"""
        processor = processor_with_mocks
        
        with patch.object(processor, '_handle_feedback_command') as mock_handle:
            mock_handle.return_value = "Feedback result"
            
            result = processor._execute_command({"command": "feedback", "args": "test feedback"})
            
            assert result == "Feedback result"
            mock_handle.assert_called_once_with("test feedback")

    def test_execute_command_journal(self, processor_with_mocks):
        """Test executing journal command"""
        processor = processor_with_mocks
        
        with patch.object(processor, '_handle_journal_command') as mock_handle:
            mock_handle.return_value = "Journal result"
            
            result = processor._execute_command({"command": "journal", "args": "journal entry"})
            
            assert result == "Journal result"
            mock_handle.assert_called_once_with("journal entry")

    def test_execute_command_patterns(self, processor_with_mocks):
        """Test executing patterns command"""
        processor = processor_with_mocks
        
        with patch.object(processor, '_handle_patterns_command') as mock_handle:
            mock_handle.return_value = "Patterns result"
            
            result = processor._execute_command({"command": "patterns", "args": ""})
            
            assert result == "Patterns result"
            mock_handle.assert_called_once_with("")

    def test_execute_command_unknown(self, processor_with_mocks):
        """Test executing unknown command"""
        processor = processor_with_mocks
        
        result = processor._execute_command({"command": "unknown", "args": "args"})
        
        assert "Unknown command" in result

    def test_extract_commands_from_email_body(self, processor_with_mocks):
        """Test extracting commands from email body"""
        processor = processor_with_mocks
        
        email_body = """
        Here's my feedback for today:
        
        feedback Baby loved tummy time and enjoyed reading books
        
        Also, here's a journal entry:
        journal Had a wonderful morning with lots of smiles
        
        Can you show me this week's memory?
        memory week
        """
        
        commands = processor._extract_commands_from_email_body(email_body)
        
        assert len(commands) == 3
        assert commands[0]["command"] == "feedback"
        assert "tummy time" in commands[0]["args"]
        assert commands[1]["command"] == "journal"
        assert "wonderful morning" in commands[1]["args"]
        assert commands[2]["command"] == "memory"
        assert commands[2]["args"] == "week"

    def test_extract_commands_single_command(self, processor_with_mocks):
        """Test extracting single command from email"""
        processor = processor_with_mocks
        
        email_body = "patterns"
        
        commands = processor._extract_commands_from_email_body(email_body)
        
        assert len(commands) == 1
        assert commands[0]["command"] == "patterns"
        assert commands[0]["args"] == ""

    def test_extract_commands_no_commands(self, processor_with_mocks):
        """Test extracting commands from email with no commands"""
        processor = processor_with_mocks
        
        email_body = "This is just a regular email with no commands."
        
        commands = processor._extract_commands_from_email_body(email_body)
        
        assert len(commands) == 0

    def test_extract_commands_case_insensitive(self, processor_with_mocks):
        """Test that command extraction is case insensitive"""
        processor = processor_with_mocks
        
        email_body = """
        MEMORY week
        FEEDBACK Baby enjoyed tummy time
        PATTERNS
        """
        
        commands = processor._extract_commands_from_email_body(email_body)
        
        assert len(commands) == 3
        assert all(cmd["command"].lower() in ["memory", "feedback", "patterns"] for cmd in commands)

    def test_parse_email_message(self, processor_with_mocks):
        """Test parsing email message"""
        processor = processor_with_mocks
        
        # Create a mock email message
        msg = email.message.Message()
        msg['From'] = 'parent@example.com'
        msg['Subject'] = 'Baby Feedback'
        msg.set_payload('feedback Baby loved tummy time')
        
        result = processor._parse_email_message(msg)
        
        assert result['from'] == 'parent@example.com'
        assert result['subject'] == 'Baby Feedback'
        assert 'feedback Baby loved tummy time' in result['body']

    def test_get_today_memory(self, processor_with_mocks, memory_manager):
        """Test getting today's memory"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'get_entry') as mock_get:
            mock_get.return_value = {
                'timestamp': datetime.now().isoformat(),
                'feedback': {
                    'what_enjoyed': ['tummy time'],
                    'didnt_like': [],
                    'sleep_quality': '8',
                    'feeding_response': 'good',
                    'developmental': ['more alert']
                },
                'journal_entries': [
                    {'note': 'Great morning', 'time': '10:00 AM'}
                ]
            }
            
            result = processor._get_today_memory()
            
            assert "Today's Memory" in result
            assert "tummy time" in result
            assert "Great morning" in result

    def test_get_today_memory_empty(self, processor_with_mocks, memory_manager):
        """Test getting today's memory when no entry exists"""
        processor = processor_with_mocks
        
        with patch.object(memory_manager, 'get_entry') as mock_get:
            mock_get.return_value = None
            
            result = processor._get_today_memory()
            
            assert "No memory entries found" in result

    def test_get_help_message(self, processor_with_mocks):
        """Test getting help message"""
        processor = processor_with_mocks
        
        result = processor._get_help_message()
        
        assert "Available Commands" in result
        assert "memory" in result
        assert "feedback" in result
        assert "journal" in result
        assert "patterns" in result

    def test_is_email_processed(self, processor_with_mocks):
        """Test checking if email is already processed"""
        processor = processor_with_mocks
        
        # Add an email to processed set
        email_id = "test_email_123"
        processor._processed_emails.add(email_id)
        
        assert processor._is_email_processed(email_id) is True
        assert processor._is_email_processed("different_email") is False

    def test_process_single_email(self, processor_with_mocks):
        """Test processing a single email"""
        processor = processor_with_mocks
        
        with patch.object(processor, '_parse_email_message') as mock_parse, \
             patch.object(processor, '_extract_commands_from_email_body') as mock_extract, \
             patch.object(processor, '_execute_command') as mock_execute, \
             patch.object(processor, '_save_processed_email') as mock_save:
            
            mock_parse.return_value = {
                'from': 'parent@example.com',
                'subject': 'Test',
                'body': 'feedback test'
            }
            mock_extract.return_value = [{'command': 'feedback', 'args': 'test'}]
            mock_execute.return_value = 'Feedback processed'
            mock_save.return_value = True
            
            result = processor._process_single_email("email_123")
            
            assert result is not None
            mock_parse.assert_called_once()
            mock_extract.assert_called_once()
            mock_execute.assert_called_once()
            mock_save.assert_called_once_with("email_123")

    def test_process_single_email_already_processed(self, processor_with_mocks):
        """Test processing email that's already been processed"""
        processor = processor_with_mocks
        
        # Mark email as processed
        email_id = "already_processed_email"
        processor._processed_emails.add(email_id)
        
        result = processor._process_single_email(email_id)
        
        assert result is None

    def test_process_email_commands_integration(self, processor_with_mocks):
        """Test full email command processing integration"""
        processor = processor_with_mocks
        
        with patch.object(processor, '_connect_to_email') as mock_connect, \
             patch.object(processor, '_search_new_emails') as mock_search, \
             patch.object(processor, '_process_single_email') as mock_process:
            
            mock_connect.return_value = True
            mock_search.return_value = ['email1', 'email2']
            mock_process.return_value = 'Processed'
            
            result = processor.process_email_commands()
            
            assert result is True
            mock_connect.assert_called_once()
            mock_search.assert_called_once()
            assert mock_process.call_count == 2


@pytest.fixture
def processor_with_mocks(mock_base_dir, memory_manager, patterns_manager):
    """Create EmailCommandProcessor with mocked dependencies"""
    processed_file = mock_base_dir / "processed_emails.json"
    
    with patch("base_classes.PROCESSED_EMAILS_FILE", processed_file), \
         patch("base_classes.memory_manager", memory_manager), \
         patch("base_classes.patterns_manager", patterns_manager):
        
        processor = EmailCommandProcessor()
        return processor
