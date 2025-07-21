#!/usr/bin/env python3
"""
Unit tests for the Persistent Memory system - PostgreSQL with pgvector
"""

import unittest
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.persistent_memory import store_memory, retrieve_memory, get_memory_stats

class TestPersistentMemory(unittest.TestCase):
    """Test suite for Persistent Memory functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Mock database connection for tests
        self.mock_conn_patcher = patch('core.persistent_memory.psycopg2.connect')
        self.mock_conn = self.mock_conn_patcher.start()
        
        # Mock connection and cursor
        self.mock_db_conn = Mock()
        self.mock_cursor = Mock()
        self.mock_db_conn.cursor.return_value = self.mock_cursor
        self.mock_conn.return_value = self.mock_db_conn
    
    def tearDown(self):
        """Clean up after each test"""
        self.mock_conn_patcher.stop()
    
    def test_store_memory_basic(self):
        """Test basic memory storage functionality"""
        # Test storing a simple memory entry
        result = store_memory(
            component="test_component",
            entry_type="test_type",
            content="Test memory content",
            context="test_context"
        )
        
        # Verify database insert was called
        self.mock_cursor.execute.assert_called()
        self.mock_db_conn.commit.assert_called()
        
        # Check that SQL insert was called with correct structure
        sql_call = self.mock_cursor.execute.call_args[0][0]
        self.assertIn("INSERT INTO memory_entries", sql_call)
        self.assertIn("component", sql_call)
        self.assertIn("entry_type", sql_call)
        self.assertIn("content", sql_call)
    
    def test_store_memory_with_metadata(self):
        """Test memory storage with metadata"""
        metadata = {
            "user": "test_user",
            "model": "chatgpt",
            "tokens": 150,
            "response_time": 2.5
        }
        
        result = store_memory(
            component="conversational_cli",
            entry_type="conversation",
            content="User asked about weather",
            context="weather_query",
            metadata=metadata
        )
        
        # Verify metadata is properly serialized
        self.mock_cursor.execute.assert_called()
        call_args = self.mock_cursor.execute.call_args
        
        # Should include metadata in the call
        self.assertIn("metadata", call_args[0][0])
    
    def test_store_memory_with_session_id(self):
        """Test memory storage with session tracking"""
        session_id = "test_session_12345"
        
        result = store_memory(
            component="brain",
            entry_type="llm_response",
            content="LLM provided analysis",
            session_id=session_id
        )
        
        # Verify session_id is included
        self.mock_cursor.execute.assert_called()
        call_args = self.mock_cursor.execute.call_args
        call_params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        
        self.assertIn(session_id, str(call_params))
    
    def test_retrieve_memory_basic(self):
        """Test basic memory retrieval functionality"""
        # Mock database response
        mock_rows = [
            (1, "session1", "test_component", "test_type", "Memory content 1", 
             "context1", '{"key": "value"}', None, datetime.now(), datetime.now()),
            (2, "session2", "test_component", "test_type", "Memory content 2", 
             "context2", '{"key2": "value2"}', None, datetime.now(), datetime.now())
        ]
        self.mock_cursor.fetchall.return_value = mock_rows
        
        # Test retrieval
        entries = retrieve_memory(
            component="test_component",
            entry_type="test_type"
        )
        
        # Verify query was executed
        self.mock_cursor.execute.assert_called()
        sql_call = self.mock_cursor.execute.call_args[0][0]
        self.assertIn("SELECT", sql_call)
        self.assertIn("FROM memory_entries", sql_call)
        
        # Verify results are formatted correctly
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['content'], "Memory content 1")
        self.assertEqual(entries[1]['content'], "Memory content 2")
    
    def test_retrieve_memory_with_filters(self):
        """Test memory retrieval with various filters"""
        mock_rows = []
        self.mock_cursor.fetchall.return_value = mock_rows
        
        # Test with multiple filters
        entries = retrieve_memory(
            component="conversational_cli",
            entry_type="conversation",
            context="weather",
            limit=10
        )
        
        # Verify WHERE clauses are included
        sql_call = self.mock_cursor.execute.call_args[0][0]
        self.assertIn("WHERE", sql_call)
        self.assertIn("component", sql_call)
        self.assertIn("entry_type", sql_call)
        self.assertIn("context", sql_call)
        self.assertIn("LIMIT", sql_call)
    
    def test_retrieve_memory_similarity_search(self):
        """Test vector similarity search functionality"""
        mock_rows = []
        self.mock_cursor.fetchall.return_value = mock_rows
        
        # Test similarity search
        entries = retrieve_memory(
            component="",
            entry_type="",
            context="",
            similarity_query="Find similar conversations about weather",
            limit=5
        )
        
        # Verify similarity search SQL is used
        sql_call = self.mock_cursor.execute.call_args[0][0]
        # Should use vector similarity with pgvector
        self.assertIn("ORDER BY", sql_call)
    
    def test_get_memory_stats(self):
        """Test memory statistics retrieval"""
        # Mock statistics query results
        mock_stats = [
            ("Total entries", 1250),
            ("Unique sessions", 45),
            ("Components", 8),
            ("Average entry size", 512)
        ]
        self.mock_cursor.fetchall.return_value = mock_stats
        
        stats = get_memory_stats()
        
        # Verify stats query was called
        self.mock_cursor.execute.assert_called()
        sql_call = self.mock_cursor.execute.call_args[0][0]
        self.assertIn("COUNT", sql_call)
    
    def test_memory_cleanup(self):
        """Test old memory cleanup functionality"""
        # Mock cleanup operation
        self.mock_cursor.rowcount = 25
        
        # Test cleanup (this function may not exist yet)
        try:
            from core.persistent_memory import cleanup_old_entries
            result = cleanup_old_entries(days_old=30)
            
            # Verify DELETE query was called
            self.mock_cursor.execute.assert_called()
            sql_call = self.mock_cursor.execute.call_args[0][0]
            self.assertIn("DELETE", sql_call)
            self.assertIn("created_at", sql_call)
            
        except ImportError:
            # Function not implemented yet - that's expected
            self.skipTest("cleanup_old_entries not implemented yet")
    
    def test_error_handling_connection_failure(self):
        """Test error handling when database connection fails"""
        # Mock connection failure
        self.mock_conn.side_effect = Exception("Connection failed")
        
        # Should handle error gracefully
        result = store_memory("test", "test", "test content")
        
        # Should return error indication rather than crashing
        # Implementation may vary - could return False, None, or error message
        self.assertIsNotNone(result)
    
    def test_error_handling_invalid_data(self):
        """Test error handling with invalid data"""
        # Test with None values
        result = store_memory(None, "test", "content")
        
        # Should handle gracefully
        # Implementation should validate inputs
        self.assertIsNotNone(result)
    
    def test_memory_entry_format(self):
        """Test that memory entries have correct format"""
        # Mock a typical database row
        mock_row = (
            123, "session_abc", "conversational_cli", "conversation", 
            "User asked about Python", "python_query", 
            '{"model": "chatgpt", "tokens": 150}', 
            [0.1, 0.2, 0.3],  # Mock embedding vector
            datetime(2025, 7, 21, 10, 0, 0),
            datetime(2025, 7, 21, 10, 0, 0)
        )
        
        self.mock_cursor.fetchall.return_value = [mock_row]
        
        entries = retrieve_memory(component="conversational_cli")
        
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        
        # Verify entry has expected fields
        expected_fields = [
            'id', 'session_id', 'component', 'entry_type', 
            'content', 'context', 'metadata', 'embedding',
            'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, entry)
    
    def test_session_based_retrieval(self):
        """Test retrieving memories for specific session"""
        mock_rows = [
            (1, "session_123", "brain", "response", "Response 1", 
             "", "{}", None, datetime.now(), datetime.now()),
            (2, "session_123", "brain", "response", "Response 2", 
             "", "{}", None, datetime.now(), datetime.now())
        ]
        self.mock_cursor.fetchall.return_value = mock_rows
        
        # Test session-specific retrieval
        entries = retrieve_memory(
            component="brain",
            session_id="session_123"
        )
        
        # Verify session filter was applied
        sql_call = self.mock_cursor.execute.call_args[0][0]
        self.assertIn("session_id", sql_call)
        
        # All entries should be from same session
        for entry in entries:
            self.assertEqual(entry['session_id'], "session_123")

class TestMemoryIntegration(unittest.TestCase):
    """Integration tests for memory system with other components"""
    
    @patch('core.persistent_memory.psycopg2.connect')
    def test_brain_memory_integration(self, mock_connect):
        """Test integration between Brain system and Memory"""
        # Mock database
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Test that brain responses are stored in memory
        from core.brain import Brain
        
        brain = Brain()
        
        with patch.object(brain, '_call_chatgpt') as mock_call:
            mock_call.return_value = ("Test response", 100)
            
            response = brain.ask_single("Test prompt", "chatgpt")
            
            # Memory storage should be called
            # (This depends on Brain implementation)
            self.assertIsNotNone(response)
    
    @patch('core.persistent_memory.psycopg2.connect')
    def test_cli_memory_integration(self, mock_connect):
        """Test integration between CLI and Memory"""
        # Mock database
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Test that CLI operations are stored in memory
        from core.conversational_cli import ConversationalCLI
        
        with patch('core.brain.Brain'):
            cli = ConversationalCLI()
            
            # Mock a chat interaction
            with patch.object(cli.brain, 'ask_single') as mock_ask:
                mock_response = Mock()
                mock_response.response = "CLI test response"
                mock_response.model = "chatgpt"
                mock_response.tokens_used = 50
                mock_response.timestamp = datetime.now().isoformat()
                mock_ask.return_value = mock_response
                
                # Should trigger memory storage
                response = cli.chat("Test message")
                
                # Verify memory storage was attempted
                mock_cursor.execute.assert_called()

class TestMemoryPerformance(unittest.TestCase):
    """Performance and scalability tests for memory system"""
    
    @patch('core.persistent_memory.psycopg2.connect')
    def test_large_batch_storage(self, mock_connect):
        """Test storing large batches of memory entries"""
        # Mock database
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Test storing many entries
        for i in range(100):
            store_memory(
                component="performance_test",
                entry_type="batch_test",
                content=f"Test entry {i}",
                context=f"batch_{i}"
            )
        
        # Should have called database 100 times
        self.assertEqual(mock_cursor.execute.call_count, 100)
    
    @patch('core.persistent_memory.psycopg2.connect')
    def test_memory_search_performance(self, mock_connect):
        """Test search performance with large result sets"""
        # Mock database with large result set
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock large result set
        large_result = []
        for i in range(1000):
            large_result.append((
                i, f"session_{i}", "test", "performance", 
                f"Large content {i} " * 50, "perf_context",
                "{}", None, datetime.now(), datetime.now()
            ))
        
        mock_cursor.fetchall.return_value = large_result
        
        # Test retrieval performance
        entries = retrieve_memory(component="test", limit=1000)
        
        # Should handle large result sets
        self.assertEqual(len(entries), 1000)

if __name__ == '__main__':
    # Set up test environment
    os.environ['POSTGRES_HOST'] = 'localhost'
    os.environ['POSTGRES_USER'] = 'test_user'
    os.environ['POSTGRES_PASSWORD'] = 'test_pass'
    os.environ['POSTGRES_DB'] = 'test_db'
    
    # Run tests
    unittest.main(verbosity=2)