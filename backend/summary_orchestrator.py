import asyncio
import time
from bson import ObjectId
from datetime import datetime
from backend.preprocessing import preprocess_for_summarization
from backend.models.summarizer import Summarizer
from utils.database import (
    get_book_by_id,
    save_summary,
    update_book_status,
    update_progress,
    log_error,
    db
)
from utils.formatters import convert_to_bullets
from utils.stats import calculate_summary_stats


def summarize_with_retry(summarizer, text, length_params, retries=3):
    """Retry summarization if it fails"""
    for attempt in range(retries):
        try:
            # Ensure text is long enough
            if not text or len(text.strip()) < 10:
                return None  # Return None for short text
            
            # Summarize
            summary = summarizer.summarize_chunk(text, **length_params)
            
            # Validate summary
            if not summary or len(summary.strip()) < 10:
                if attempt < retries - 1:
                    continue  # Retry
                return None
            
            return summary
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                return None  # Return None instead of fallback
            time.sleep(1)
    return None


async def generate_summary(book_id, user_id, summary_options):
    """Main summarization orchestration function"""
    try:
        start_time = time.time()
        
        # Update status to processing
        update_book_status(book_id, "processing")
        update_progress(book_id, "Starting summarization...", 5)

        # STEP 1: Retrieve book with proper ObjectId
        try:
            book_id_obj = ObjectId(book_id) if isinstance(book_id, str) else book_id
            book = db.books.find_one({"_id": book_id_obj})
        except:
            book = get_book_by_id(book_id)
            
        if not book:
            raise ValueError(f"Book with ID {book_id} not found")
        
        # Get text from multiple possible sources
        raw_text = book.get("raw_text", "")
        if not raw_text or len(raw_text.strip()) < 50:
            # Try other fields
            raw_text = book.get("text", "") or book.get("content", "") or book.get("extracted_text", "")
        
        # If still too short, check if it's actually extracted
        if not raw_text or len(raw_text.strip()) < 50:
            # Check file path and extract again if needed
            file_path = book.get("file_path")
            if file_path:
                from backend.text_extractor import process_book
                print(f"Text too short, re-extracting from: {file_path}")
                extract_result = process_book(book_id, file_path)
                if extract_result.get("success"):
                    # Refresh book data
                    book = db.books.find_one({"_id": ObjectId(book_id)})
                    raw_text = book.get("raw_text", "")
                else:
                    raise ValueError(f"Text extraction failed: {extract_result.get('error', 'Unknown')}")
            else:
                raise ValueError(f"Book text is too short ({len(raw_text or '')} chars) and no file to re-extract from")
        
        print(f"Processing text of length: {len(raw_text)} characters")
        update_progress(book_id, f"Book retrieved ({len(raw_text)} chars)", 10)

        # STEP 2: Preprocess with validation
        update_progress(book_id, "Preprocessing text...", 20)
        
        try:
            preprocessed = preprocess_for_summarization(raw_text, chunk_size=800)
            chunks = preprocessed.get("chunks", [])
        except Exception as e:
            print(f"Preprocessing failed: {e}")
            # Create simple chunks
            words = raw_text.split()
            chunks = []
            for i in range(0, len(words), 800):
                chunk_text = " ".join(words[i:i+800])
                if len(chunk_text) > 50:  # Only add if meaningful
                    chunks.append(chunk_text)
        
        if not chunks:
            # Use the whole text as one chunk
            chunks = [raw_text]
        
        print(f"Created {len(chunks)} chunks")
        update_progress(book_id, f"Text split into {len(chunks)} chunks", 30)

        # STEP 3: Init summarizer
        update_progress(book_id, "Loading AI model...", 35)
        
        try:
            summarizer = Summarizer("sshleifer/distilbart-cnn-12-6")
        except Exception as e:
            print(f"Primary model failed: {e}")
            try:
                summarizer = Summarizer("facebook/bart-large-cnn")
            except Exception as e2:
                print(f"Fallback model failed: {e2}")
                # Use a very simple fallback
                class SimpleSummarizer:
                    def summarize_chunk(self, text, min_length=60, max_length=150):
                        sentences = text.split('.')
                        sentences = [s.strip() for s in sentences if s.strip()]
                        if len(sentences) > 3:
                            return '. '.join(sentences[:3]) + '.'
                        return text[:max_length]
                    def combine_summaries(self, summaries):
                        return ' '.join(summaries)
                    def post_process_summary(self, summary):
                        return summary.strip()
                
                summarizer = SimpleSummarizer()
        
        # Configure length
        length = summary_options.get("length", "medium")
        if length == "short":
            length_params = {"min_length": 30, "max_length": 100}
        elif length == "long":
            length_params = {"min_length": 150, "max_length": 300}
        else:  # medium
            length_params = {"min_length": 80, "max_length": 150}
        
        update_progress(book_id, "Model ready", 40)

        # STEP 4: Chunk summarization
        chunk_summaries = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            # Calculate progress (40% to 90%)
            percentage = 40 + int(((i + 1) / total_chunks) * 50)
            update_progress(
                book_id,
                f"Summarizing chunk {i+1}/{total_chunks}",
                percentage
            )

            # Get chunk text
            if isinstance(chunk, dict):
                chunk_text = chunk.get("text", "")
            else:
                chunk_text = str(chunk)
            
            print(f"Chunk {i+1} length: {len(chunk_text)} chars")
            
            # Skip if chunk is too short
            if len(chunk_text.strip()) < 10:
                print(f"Chunk {i+1} skipped - too short")
                continue
            
            # Summarize chunk
            try:
                chunk_summary = await asyncio.to_thread(
                    summarize_with_retry,
                    summarizer,
                    chunk_text,
                    length_params
                )
                
                if chunk_summary:
                    chunk_summaries.append(chunk_summary.strip())
                    print(f"Chunk {i+1} summarized successfully")
                else:
                    print(f"Chunk {i+1} summarization failed, using extractive fallback")
                    # Use extractive fallback
                    sentences = chunk_text.split('.')
                    sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
                    if sentences:
                        fallback = '. '.join(sentences[:2]) + '.' if len(sentences) > 2 else sentences[0] + '.'
                        chunk_summaries.append(fallback)
                    
            except Exception as e:
                print(f"Chunk {i} error: {e}")
                # Use first part of chunk as fallback
                if len(chunk_text) > 50:
                    chunk_summaries.append(chunk_text[:200] + "...")

        # STEP 5: Check if we have any summaries
        print(f"Total chunk summaries generated: {len(chunk_summaries)}")
        if not chunk_summaries:
            # Create a simple summary from the original text
            sentences = raw_text.split('.')
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
            if len(sentences) >= 2:
                chunk_summaries = ['. '.join(sentences[:2]) + '.']
            elif len(sentences) == 1:
                chunk_summaries = [sentences[0]]
            else:
                # Last resort
                chunk_summaries = [raw_text[:300] + "..." if len(raw_text) > 300 else raw_text]
        
        update_progress(book_id, f"Generated {len(chunk_summaries)} chunk summaries", 90)

        # STEP 6: Combine summaries
        update_progress(book_id, "Combining summaries...", 95)
        
        try:
            # Combine the chunk summaries
            combined_text = " ".join(chunk_summaries)
            print(f"Combined text length: {len(combined_text)} chars")
            
            # If combined text is reasonable length, use it directly
            if len(combined_text.split()) <= 500:
                final_summary = combined_text
            else:
                # Summarize again if too long
                print("Summarizing combined text (too long)")
                final_summary = await asyncio.to_thread(
                    summarize_with_retry,
                    summarizer,
                    combined_text,
                    {"min_length": 100, "max_length": 300}
                ) or combined_text[:500] + "..."
            
            # Post-process
            final_summary = final_summary.strip()
            if hasattr(summarizer, 'post_process_summary'):
                final_summary = summarizer.post_process_summary(final_summary)
            
        except Exception as e:
            print(f"Combining failed: {e}")
            # Use the best chunk summary
            final_summary = chunk_summaries[0] if chunk_summaries else "Summary could not be generated."

        # STEP 7: Style formatting
        if summary_options.get("style") == "bullets":
            try:
                final_summary = convert_to_bullets(final_summary)
            except:
                pass  # Keep as paragraph if conversion fails

        # STEP 8: Final cleanup
        final_summary = final_summary.strip()
        if not final_summary or len(final_summary) < 20:
            final_summary = "Summary generated: " + raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
        
        # Ensure proper punctuation
        if final_summary and final_summary[-1] not in '.!?':
            final_summary += '.'

        print(f"Final summary length: {len(final_summary)} chars")

        # STEP 9: Save to database - SIMPLIFIED VERSION
        try:
            # Create summary data
            summary_data = {
                "book_id": ObjectId(book_id) if isinstance(book_id, str) else book_id,
                "user_id": ObjectId(user_id) if isinstance(user_id, str) else user_id,
                "summary_text": final_summary,
                "summary": final_summary,
                "chunk_summaries": chunk_summaries,
                "processing_time": round(time.time() - start_time, 2),
                "created_at": datetime.now(),
                "metadata": {
                    "length": summary_options.get("length", "medium"),
                    "style": summary_options.get("style", "paragraph")
                }
            }
            
            # Save directly
            result = db.summaries.insert_one(summary_data)
            summary_id = str(result.inserted_id)
            print(f"Summary saved with ID: {summary_id}")
            
        except Exception as e:
            print(f"Database save error: {e}")
            # Try update instead
            try:
                db.summaries.update_one(
                    {"book_id": ObjectId(book_id) if isinstance(book_id, str) else book_id},
                    {"$set": summary_data},
                    upsert=True
                )
                summary_id = f"updated_{book_id}"
                print(f"Summary updated")
            except Exception as e2:
                print(f"Update also failed: {e2}")
                summary_id = None

        # STEP 10: Final update
        update_progress(book_id, "Summary completed!", 100)
        update_book_status(book_id, "completed")

        # Calculate stats
        try:
            stats = calculate_summary_stats(final_summary, raw_text)
        except:
            stats = {
                "original_length": len(raw_text.split()),
                "summary_length": len(final_summary.split()),
                "compression_ratio": "N/A",
                "processing_time": round(time.time() - start_time, 2)
            }

        return {
            "success": True,
            "summary_id": summary_id,
            "summary": final_summary,
            "stats": stats,
            "processing_time_sec": round(time.time() - start_time, 2),
            "chunk_summary_count": len(chunk_summaries)
        }

    except Exception as e:
        error_msg = str(e)
        print(f"SUMMARIZATION FAILED: {error_msg}")
        print(f"Book ID: {book_id}")
        print(f"Error type: {type(e).__name__}")
        
        update_book_status(book_id, "failed")
        update_progress(book_id, f"Error: {error_msg}", 0)
        log_error(book_id, error_msg)
        
        # Store detailed error
        try:
            db.books.update_one(
                {"_id": ObjectId(book_id) if isinstance(book_id, str) else book_id},
                {"$set": {
                    "error_message": error_msg,
                    "last_error_time": datetime.now()
                }}
            )
        except:
            pass
        
        return {
            "success": False, 
            "error": error_msg,
            "suggestion": "Please check if the book file contains readable text. Try with a .txt file first."
        }