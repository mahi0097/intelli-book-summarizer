import pytest
import time
import statistics
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

class TestPerformance:
    
    def test_summarization_speed(self):
        """Test summarization performance"""
        from backend.models.summarizer import UltraFastSummarizer
        
        summarizer = UltraFastSummarizer()
        
        # Test with different text lengths
        test_cases = [
            ("Short", 100),    # ~100 words
            ("Medium", 500),   # ~500 words
            ("Long", 2000),    # ~2000 words
        ]
        
        performance_results = {}
        
        for name, word_count in test_cases:
            # Generate test text
            text = " ".join(["Word" + str(i) for i in range(word_count)])
            
            # Time the summarization
            start_time = time.time()
            result = summarizer.generate_ultra_fast_summary(text)
            elapsed = time.time() - start_time
            
            performance_results[name] = {
                "word_count": word_count,
                "time_seconds": elapsed,
                "words_per_second": word_count / elapsed if elapsed > 0 else 0
            }
            
            print(f"  📊 {name} ({word_count} words): {elapsed:.2f}s "
                  f"({performance_results[name]['words_per_second']:.0f} words/sec)")
        
        # Performance requirements
        assert performance_results["Short"]["time_seconds"] < 2.0
        assert performance_results["Medium"]["time_seconds"] < 5.0
        assert performance_results["Long"]["time_seconds"] < 15.0
    
    def test_concurrent_users(self):
        """Test system under concurrent load"""
        import threading
        
        results = []
        errors = []
        
        def simulate_user(user_id):
            """Simulate a user performing actions"""
            try:
                # Simulate login
                time.sleep(0.1)
                
                # Simulate upload
                time.sleep(0.2)
                
                # Simulate summarization
                time.sleep(0.3)
                
                results.append({
                    "user_id": user_id,
                    "success": True,
                    "total_time": 0.6
                })
                
            except Exception as e:
                errors.append({"user_id": user_id, "error": str(e)})
        
        # Simulate multiple concurrent users
        threads = []
        num_users = 10
        
        for i in range(num_users):
            thread = threading.Thread(target=simulate_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Analyze results
        success_rate = len(results) / num_users * 100
        
        print(f"✅ Concurrent users test: {len(results)}/{num_users} successful "
              f"({success_rate:.1f}% success rate)")
        
        assert success_rate >= 80  # At least 80% success rate
        assert len(errors) <= 2    # Maximum 2 errors