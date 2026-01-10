# backend/models/summarizer.py - FAST VERSION
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import time
import os
import re
from typing import Dict, List
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class FastSummarizer:
    """Ultra-fast summarizer with multiple optimizations"""
    
    # Models optimized for speed (smaller = faster)
    FAST_MODELS = {
        "distilbart": {
            "name": "sshleifer/distilbart-cnn-12-6",
            "max_input": 1024,
            "max_output": 128,
            "description": "⚡ Fastest - Distilled BART model",
            "chunk_chars": 2500
        },
        "t5_small": {
            "name": "t5-small", 
            "max_input": 512,
            "max_output": 150,
            "description": "🚀 Very Fast - Small T5 model",
            "chunk_chars": 1500
        },
        "bart_base": {
            "name": "facebook/bart-base",
            "max_input": 1024,
            "max_output": 142,
            "description": "⚡ Fast - Base BART model",
            "chunk_chars": 2500
        }
    }
    
    _instance = None
    
    def __new__(cls, model_key="distilbart"):  # Fastest by default
        if cls._instance is None:
            cls._instance = super(FastSummarizer, cls).__new__(cls)
            cls._instance._initialize_fast_model(model_key)
        return cls._instance
    
    def _initialize_fast_model(self, model_key):
        """Initialize fast model with optimizations"""
        try:
            model_config = self.FAST_MODELS.get(model_key, self.FAST_MODELS["distilbart"])
            model_name = model_config["name"]
            
            print(f"⚡ Loading FAST model: {model_name}")
            
            # Cache directory
            cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "book_summarizer")
            os.makedirs(cache_dir, exist_ok=True)
            
            self.model_name = model_name
            self.model_config = model_config
            self.max_input_tokens = model_config["max_input"]
            self.max_output_tokens = model_config["max_output"]
            self.chunk_chars = model_config["chunk_chars"]
            
            # FAST LOADING: Disable some checks for speed
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                use_fast=True,  # Fast tokenizer
                model_max_length=self.max_input_tokens
            )
            
            # Load model with optimizations
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                low_cpu_mem_usage=True  # Reduce memory usage
            )
            
            # Device optimization
            device = 0 if torch.cuda.is_available() else -1
            
            # Create pipeline with SPEED optimizations
            self.pipeline = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device,
                framework="pt",
                batch_size=1  # Process one at a time for stability
            )
            
            print(f"✅ FAST model loaded: {model_name}")
            print(f"   Speed: {model_config['description']}")
            print(f"   Max input: {self.max_input_tokens} tokens")
            
        except Exception as e:
            print(f"❌ Fast model failed: {e}")
            # Ultra-light fallback
            print("🔄 Using ultra-light extractive summarizer")
            self._use_extractive_fallback = True
    
    def create_quick_chunks(self, text: str) -> List[str]:
        """Create chunks quickly without heavy tokenization"""
        if not text:
            return []
        
        print(f"📊 Quick chunking: {len(text)} chars")
        
        # Simple character-based chunking (FAST)
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_chars
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Find a good break point (sentence or paragraph)
            break_points = [
                text.rfind('. ', start, end),
                text.rfind('? ', start, end),
                text.rfind('! ', start, end),
                text.rfind('\n\n', start, end)
            ]
            
            # Use the latest break point
            latest_break = max(bp for bp in break_points if bp > start)
            
            if latest_break > start and latest_break - start > self.chunk_chars * 0.5:
                end = latest_break + 1
            else:
                # Just use character limit
                end = start + self.chunk_chars
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        print(f"📦 Created {len(chunks)} quick chunks")
        return chunks
    
    def fast_summarize_chunk(self, text: str) -> str:
        """Ultra-fast chunk summarization with minimal processing"""
        if len(text) < 100:  # Too short
            return text
        
        try:
            # SPEED OPTIMIZATION: Use minimal parameters
            result = self.pipeline(
                text[:self.chunk_chars],  # Ensure within limits
                max_length=min(100, self.max_output_tokens),  # Short summaries = faster
                min_length=30,
                do_sample=False,  # Deterministic = faster
                num_beams=2,  # Fewer beams = faster
                early_stopping=True,
                truncation=True,
                no_repeat_ngram_size=2
            )
            
            if result and result[0]["summary_text"]:
                return result[0]["summary_text"].strip()
            
        except Exception as e:
            print(f"⚠️ Fast summarization failed: {e}")
        
        # FAST extractive fallback
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if sentences:
            # Take first 2 sentences
            return '. '.join(sentences[:2]) + '.'
        
        return text[:150] + "..."
    
    def parallel_summarize(self, chunks: List[str], max_workers: int = 2) -> List[str]:
        """Parallel processing for speed"""
        if not chunks or len(chunks) <= 3:
            # Sequential for small batches
            return [self.fast_summarize_chunk(chunk) for chunk in chunks]
        
        print(f"🚀 Parallel processing {len(chunks)} chunks with {max_workers} workers")
        
        summaries = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_chunk = {
                executor.submit(self.fast_summarize_chunk, chunk): i 
                for i, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                try:
                    summary = future.result(timeout=30)  # 30s timeout per chunk
                    if summary:
                        summaries.append(summary)
                except Exception as e:
                    chunk_idx = future_to_chunk[future]
                    print(f"❌ Chunk {chunk_idx} failed: {e}")
        
        return summaries
    
    def quick_combine(self, summaries: List[str]) -> str:
        """Quick combination without re-summarization"""
        if not summaries:
            return ""
        
        # Simply join with spaces
        combined = " ".join(summaries)
        
        # Remove obvious duplicates
        sentences = re.split(r'[.!?]+', combined)
        unique_sentences = []
        seen = set()
        
        for sent in sentences:
            clean = sent.strip().lower()
            if clean and clean not in seen and len(clean) > 20:
                seen.add(clean)
                unique_sentences.append(sent.strip())
        
        result = '. '.join(unique_sentences[:8])  # Limit to 8 sentences max
        if result and not result.endswith('.'):
            result += '.'
        
        return result
    
    def generate_quick_summary(self, text: str, use_parallel: bool = True) -> Dict:
        """
        Generate summary FAST with multiple optimizations
        """
        start_time = time.time()
        
        print(f"\n🚀 STARTING QUICK SUMMARIZATION")
        print(f"📖 Input: {len(text)} chars, ~{len(text.split())} words")
        
        # STEP 1: Quick chunking (FAST)
        chunk_start = time.time()
        chunks = self.create_quick_chunks(text)
        chunk_time = time.time() - chunk_start
        print(f"📦 Chunking: {len(chunks)} chunks in {chunk_time:.2f}s")
        
        if not chunks:
            return {
                "success": False,
                "error": "No text to summarize",
                "summary_text": "",
                "processing_time": 0
            }
        
        # STEP 2: Parallel summarization (VERY FAST)
        summary_start = time.time()
        
        if use_parallel and len(chunks) > 1:
            summaries = self.parallel_summarize(chunks)
        else:
            summaries = [self.fast_summarize_chunk(chunk) for chunk in chunks]
        
        summary_time = time.time() - summary_start
        print(f"⚡ Summarization: {len(summaries)} summaries in {summary_time:.2f}s")
        
        # STEP 3: Quick combination (FAST)
        combine_start = time.time()
        final_summary = self.quick_combine(summaries)
        combine_time = time.time() - combine_start
        
        total_time = time.time() - start_time
        
        print(f"\n✅ QUICK SUMMARY COMPLETE!")
        print(f"⏱️ Total time: {total_time:.2f}s")
        print(f"📊 Chunking: {chunk_time:.2f}s")
        print(f"📊 Summarization: {summary_time:.2f}s")
        print(f"📊 Combination: {combine_time:.2f}s")
        print(f"📄 Final: {len(final_summary.split())} words")
        
        return {
            "success": True,
            "summary_text": final_summary,
            "processing_time": total_time,
            "model_used": self.model_name,
            "num_chunks": len(chunks),
            "num_summaries": len(summaries),
            "original_words": len(text.split()),
            "summary_words": len(final_summary.split()),
            "speed_metrics": {
                "chunking_time": chunk_time,
                "summarization_time": summary_time,
                "combination_time": combine_time,
                "total_time": total_time,
                "words_per_second": len(text.split()) / total_time if total_time > 0 else 0
            }
        }


class UltraFastSummarizer:
    """
    ULTRA-FAST summarizer for very quick results
    Uses extractive methods when possible
    """
    
    def __init__(self):
        self.name = "UltraFastExtractive"
        print("⚡ ULTRA-FAST extractive summarizer initialized")
    
    def extract_key_sentences(self, text: str, num_sentences: int = 5) -> List[str]:
        """Extract key sentences using simple heuristics (VERY FAST)"""
        if not text:
            return []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= num_sentences:
            return sentences
        
        # Simple scoring: prefer sentences that:
        # 1. Are not too short or too long
        # 2. Contain important words
        # 3. Come from beginning and middle
        
        important_words = {'important', 'key', 'main', 'primary', 'significant', 
                          'conclusion', 'summary', 'result', 'find', 'show'}
        
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            
            # Position score (beginning and end are important)
            if i == 0:
                score += 3  # First sentence
            elif i == len(sentences) - 1:
                score += 2  # Last sentence
            elif i < 5:
                score += 1  # Early sentences
            
            # Length score (medium length preferred)
            words = len(sentence.split())
            if 8 <= words <= 25:
                score += 2
            elif 5 <= words <= 35:
                score += 1
            
            # Content score
            lower_sentence = sentence.lower()
            for word in important_words:
                if word in lower_sentence:
                    score += 1
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top N
        scored_sentences.sort(reverse=True)
        return [sentence for _, sentence in scored_sentences[:num_sentences]]
    
    def generate_ultra_fast_summary(self, text: str) -> Dict:
        """Generate summary in under 1 second"""
        start_time = time.time()
        
        print("⚡ Generating ULTRA-FAST extractive summary...")
        
        # Extract key sentences
        key_sentences = self.extract_key_sentences(text, num_sentences=5)
        
        # Combine
        summary = ' '.join(key_sentences)
        
        # Clean up
        summary = re.sub(r'\s+', ' ', summary).strip()
        if summary and not summary.endswith('.'):
            summary += '.'
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "summary_text": summary,
            "processing_time": processing_time,
            "model_used": "Extractive (No AI)",
            "method": "extractive_key_sentences",
            "original_words": len(text.split()),
            "summary_words": len(summary.split()),
            "speed": f"{processing_time:.3f}s"
        }


# Main summarizer class that chooses based on speed vs quality
class SmartFastSummarizer:
    """Smart summarizer that balances speed and quality"""
    
    def __init__(self, mode: str = "balanced"):
        """
        mode: "fastest" | "fast" | "balanced" | "quality"
        """
        self.mode = mode
        print(f"🤖 SmartFastSummarizer initialized in '{mode}' mode")
        
        if mode == "fastest":
            self.summarizer = UltraFastSummarizer()
            self.method = "extractive"
        elif mode == "fast":
            self.summarizer = FastSummarizer("distilbart")
            self.method = "distilbart_fast"
        elif mode == "balanced":
            self.summarizer = FastSummarizer("bart_base")
            self.method = "bart_balanced"
        else:  # quality
            from .summarizer_quality import QualitySummarizer
            self.summarizer = QualitySummarizer()
            self.method = "bart_quality"
    
    def summarize(self, text: str, **kwargs) -> Dict:
        """Main summarization method"""
        print(f"\n🎯 Mode: {self.mode} | Method: {self.method}")
        
        if self.method == "extractive":
            return self.summarizer.generate_ultra_fast_summary(text)
        elif "fast" in self.method:
            return self.summarizer.generate_quick_summary(text, use_parallel=True)
        else:
            # Use quality summarizer
            return self.summarizer.generate_summary(text, **kwargs)


# Legacy class for backward compatibility (FAST VERSION)
class Summarizer(FastSummarizer):
    """Legacy class - now defaults to FAST mode"""
    
    def __new__(cls, model_name="sshleifer/distilbart-cnn-12-6"):
        """Default to fast model"""
        return FastSummarizer("distilbart")


# Utility functions for speed testing
def benchmark_summary_speed(text: str) -> Dict:
    """Benchmark different summarization speeds"""
    print("🧪 Benchmarking summarization speeds...")
    
    results = {}
    
    # Test ultra-fast
    print("\n1. Testing ULTRA-FAST (extractive)...")
    ultra_fast = UltraFastSummarizer()
    result = ultra_fast.generate_ultra_fast_summary(text)
    results["ultra_fast"] = result
    print(f"   Time: {result['processing_time']:.3f}s | Words: {result['summary_words']}")
    
    # Test fast
    print("\n2. Testing FAST (distilbart)...")
    fast = FastSummarizer("distilbart")
    result = fast.generate_quick_summary(text[:5000])  # Limit text for speed test
    results["fast"] = result
    print(f"   Time: {result['processing_time']:.3f}s | Words: {result['summary_words']}")
    
    # Test balanced
    print("\n3. Testing BALANCED (bart-base)...")
    balanced = FastSummarizer("bart_base")
    result = balanced.generate_quick_summary(text[:5000])
    results["balanced"] = result
    print(f"   Time: {result['processing_time']:.3f}s | Words: {result['summary_words']}")
    
    return results


# Test function
if __name__ == "__main__":
    sample_text = """
    Artificial intelligence is transforming how businesses operate. 
    Companies are using AI to automate repetitive tasks, analyze customer data, 
    and make better decisions. Machine learning algorithms can process vast 
    amounts of information quickly and accurately.
    
    One major application is in customer service. Chatbots powered by AI can 
    handle common queries 24/7, freeing human agents for more complex issues. 
    These systems learn from each interaction, improving over time.
    
    Another area is data analysis. AI can identify patterns in sales data, 
    predict market trends, and optimize inventory. This helps businesses 
    reduce costs and increase efficiency.
    
    However, implementing AI requires careful planning. Companies need to 
    ensure data quality, address privacy concerns, and train employees. 
    The technology should complement human workers, not replace them entirely.
    
    Looking ahead, AI will continue to evolve. New developments in natural 
    language processing and computer vision will create even more applications. 
    Businesses that adopt AI strategically will gain a competitive advantage.
    """
    
    print("🚀 Testing summarization speeds...")
    print(f"Sample text: {len(sample_text.split())} words\n")
    
    # Benchmark
    results = benchmark_summary_speed(sample_text)
    
    print("\n📊 SUMMARY OF RESULTS:")
    print("-" * 50)
    for mode, result in results.items():
        if result["success"]:
            print(f"\n{mode.upper()}:")
            print(f"  Time: {result['processing_time']:.2f}s")
            print(f"  Words: {result['summary_words']}")
            print(f"  Speed: {result.get('speed', 'N/A')}")
            print(f"  Model: {result['model_used']}")
            print(f"  Preview: {result['summary_text'][:100]}...")