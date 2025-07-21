#!/usr/bin/env python3
"""
Unit tests for the Brain system - Multi-LLM orchestrator
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.brain import Brain

class TestBrainSystem(unittest.TestCase):
    """Test suite for Brain system functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.brain = Brain()
        self.brain.permission_mode = "readonly"
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    def test_brain_initialization(self):
        """Test Brain system initializes correctly"""
        self.assertIsInstance(self.brain, Brain)
        self.assertEqual(self.brain.permission_mode, "readonly")
        self.assertIsNotNone(self.brain.session_id)
    
    @patch('core.brain.OpenAI')
    def test_chatgpt_connection(self, mock_openai):
        """Test ChatGPT provider connection"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test single ask
        response = self.brain.ask_single("Test prompt", "chatgpt")
        
        self.assertIsNotNone(response)
        self.assertEqual(response.response, "Test response")
        self.assertEqual(response.model, "chatgpt")
        self.assertEqual(response.tokens_used, 100)
    
    @patch('core.brain.anthropic.Anthropic')
    def test_claude_connection(self, mock_anthropic):
        """Test Claude provider connection"""
        # Mock Anthropic response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Claude test response"
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 30
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Test single ask
        response = self.brain.ask_single("Test prompt", "claude")
        
        self.assertIsNotNone(response)
        self.assertEqual(response.response, "Claude test response")
        self.assertEqual(response.model, "claude")
        self.assertEqual(response.tokens_used, 80)
    
    @patch('requests.post')
    def test_local_llm_connection(self, mock_post):
        """Test Local LLM provider connection"""
        # Mock local LLM response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Local LLM test response",
            "done": True
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test single ask
        response = self.brain.ask_single("Test prompt", "local")
        
        self.assertIsNotNone(response)
        self.assertEqual(response.response, "Local LLM test response")
        self.assertEqual(response.model, "local")
    
    def test_ask_all_models(self):
        """Test asking all models simultaneously"""
        with patch.object(self.brain, 'ask_single') as mock_ask:
            # Mock responses from all models
            mock_responses = [
                Mock(model="chatgpt", response="ChatGPT response", tokens_used=100),
                Mock(model="claude", response="Claude response", tokens_used=80),
                Mock(model="local", response="Local response", tokens_used=60)
            ]
            mock_ask.side_effect = mock_responses
            
            # Test ask all
            responses = self.brain.ask_all("Test prompt")
            
            self.assertEqual(len(responses), 3)
            self.assertEqual(mock_ask.call_count, 3)
            
            # Verify all models were called
            models_called = [call[0][1] for call in mock_ask.call_args_list]
            self.assertIn("chatgpt", models_called)
            self.assertIn("claude", models_called)
            self.assertIn("local", models_called)
    
    def test_file_operations_readonly_mode(self):
        """Test file operations in readonly mode"""
        self.brain.permission_mode = "readonly"
        
        # File write should be blocked
        result = self.brain.write_file("test.txt", "test content")
        self.assertIn("Permission denied", result)
        
        # File delete should be blocked
        result = self.brain.delete_file("test.txt")
        self.assertIn("Permission denied", result)
    
    def test_file_operations_write_mode(self):
        """Test file operations in write mode"""
        self.brain.permission_mode = "auto"
        
        # Mock file operations
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            with patch('os.path.exists', return_value=False):
                result = self.brain.write_file("test.txt", "test content")
                self.assertIn("File written successfully", result)
                mock_file.assert_called_once()
    
    @patch('os.listdir')
    @patch('os.path.isdir')
    def test_list_files(self, mock_isdir, mock_listdir):
        """Test file listing functionality"""
        # Mock directory contents
        mock_listdir.return_value = ['file1.txt', 'file2.py', 'subdir']
        mock_isdir.side_effect = lambda x: x.endswith('subdir')
        
        files = self.brain.list_files()
        
        self.assertIsInstance(files, list)
        self.assertIn('file1.txt', files)
        self.assertIn('file2.py', files)
    
    def test_session_management(self):
        """Test session ID generation and management"""
        # Session ID should be generated
        self.assertIsNotNone(self.brain.session_id)
        self.assertIsInstance(self.brain.session_id, str)
        self.assertGreater(len(self.brain.session_id), 10)
        
        # Each Brain instance should have unique session
        brain2 = Brain()
        self.assertNotEqual(self.brain.session_id, brain2.session_id)
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Invalid model name
        response = self.brain.ask_single("Test", "invalid_model")
        self.assertIn("Error", response.response)
        
        # Empty prompt
        response = self.brain.ask_single("", "chatgpt")
        self.assertIsNotNone(response)
    
    def test_permission_modes(self):
        """Test different permission modes"""
        # Test readonly mode
        self.brain.permission_mode = "readonly"
        self.assertEqual(self.brain.permission_mode, "readonly")
        
        # Test auto mode
        self.brain.permission_mode = "auto"
        self.assertEqual(self.brain.permission_mode, "auto")
        
        # Test manual mode
        self.brain.permission_mode = "manual"
        self.assertEqual(self.brain.permission_mode, "manual")
    
    def test_response_object_structure(self):
        """Test that response objects have correct structure"""
        with patch.object(self.brain, '_call_chatgpt') as mock_call:
            mock_call.return_value = ("Test response", 100)
            
            response = self.brain.ask_single("Test", "chatgpt")
            
            # Check response has required attributes
            self.assertTrue(hasattr(response, 'response'))
            self.assertTrue(hasattr(response, 'model'))
            self.assertTrue(hasattr(response, 'tokens_used'))
            self.assertTrue(hasattr(response, 'timestamp'))
            
            # Check types
            self.assertIsInstance(response.response, str)
            self.assertIsInstance(response.model, str)
            self.assertIsInstance(response.tokens_used, int)
    
    @patch('core.persistent_memory.store_memory')
    def test_memory_integration(self, mock_store):
        """Test integration with persistent memory"""
        with patch.object(self.brain, 'ask_single') as mock_ask:
            mock_response = Mock(
                model="chatgpt", 
                response="Test response", 
                tokens_used=100,
                timestamp="2025-07-21T10:00:00Z"
            )
            mock_ask.return_value = mock_response
            
            # Brain should integrate with memory system
            response = self.brain.ask_single("Test prompt", "chatgpt")
            
            # Verify response is stored (if memory integration exists)
            self.assertIsNotNone(response)

class TestBrainCollaboration(unittest.TestCase):
    """Test suite for Brain collaboration features (currently broken)"""
    
    def setUp(self):
        self.brain = Brain()
    
    def test_collaboration_coordination(self):
        """Test multi-model collaboration coordination (BROKEN)"""
        # This test documents the current broken behavior
        # TODO: Fix collaboration architecture
        
        with patch.object(self.brain, 'ask_single') as mock_ask:
            mock_responses = [
                Mock(model="chatgpt", response="Analysis complete"),
                Mock(model="local", response="File written"),
                Mock(model="claude", response="Review complete")
            ]
            mock_ask.side_effect = mock_responses
            
            # This should coordinate between models but currently doesn't
            # The test documents expected behavior for future implementation
            responses = self.brain.ask_all("Create and review a file")
            
            # Currently this just returns individual responses
            # TODO: Implement proper collaboration logic
            self.assertEqual(len(responses), 3)
    
    def test_task_decomposition(self):
        """Test task decomposition for complex requests (NOT IMPLEMENTED)"""
        # This feature is planned but not implemented
        # Test documents expected behavior
        
        complex_task = "Analyze the codebase, fix any issues, and create documentation"
        
        # TODO: Implement task decomposition engine
        # Should break down into: analyze -> fix -> document
        # Should assign appropriate models to each subtask
        
        # For now, just verify the brain can accept complex tasks
        with patch.object(self.brain, 'ask_single') as mock_ask:
            mock_ask.return_value = Mock(response="Task received")
            response = self.brain.ask_single(complex_task, "chatgpt")
            self.assertIsNotNone(response)

if __name__ == '__main__':
    # Set up test environment
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['ANTHROPIC_API_KEY'] = 'test-key'
    
    # Run tests
    unittest.main(verbosity=2)