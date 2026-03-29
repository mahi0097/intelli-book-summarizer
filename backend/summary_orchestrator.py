import asyncio
import time
from bson import ObjectId
from datetime import datetime
from backend.models.summarizer import FastSummarizer
from utils.database import (
    get_book_by_id,
    save_summary,
    update_book_status,
    update_progress,
    log_error,
    db
)
from utils.formatters import convert_to_bullets, convert_to_executive_summary
from utils.stats import calculate_summary_stats
from backend.preprocessing import preprocess_for_summarization


class SimpleSummarizer:
    """Cheap fallback used only when the transformer model is unavailable."""

    def summarize_chunk(self, text, min_length=60, max_length=150, summary_options=None):
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        target_sentences = 3 if min_length <= 80 else 5
        if len(sentences) >= target_sentences:
            return '. '.join(sentences[:target_sentences]) + '.'

        words = text.split()
        summary = " ".join(words[:max(max_length, min_length, 100)])
        if summary and summary[-1] not in ".!?":
            summary += "."
        return summary

    def combine_summaries(self, summaries):
        return ' '.join(summaries)

    def post_process_summary(self, summary):
        return summary.strip()


def get_length_profile(length: str):
    profiles = {
        "very short": {"min_length": 35, "max_length": 80, "combine_min": 45, "combine_max": 90},
        "short": {"min_length": 70, "max_length": 130, "combine_min": 80, "combine_max": 150},
        "medium": {"min_length": 130, "max_length": 220, "combine_min": 150, "combine_max": 260},
        "long": {"min_length": 220, "max_length": 360, "combine_min": 240, "combine_max": 420},
        "detailed": {"min_length": 320, "max_length": 520, "combine_min": 350, "combine_max": 600},
    }
    return profiles.get(length or "medium", profiles["medium"])


def finalize_summary_text(summary_text: str, summary_options: dict) -> str:
    clean = (summary_text or "").strip()
    if not clean:
        return ""

    style = summary_options.get("style")
    if style == "bullet_points":
        return convert_to_bullets(clean)
    if style == "executive_summary":
        return convert_to_executive_summary(clean)
    return clean


def ensure_summary_shorter_than_source(summary_text: str, source_text: str) -> str:
    """Guarantee the final summary is shorter than the source when feasible."""
    clean_summary = (summary_text or "").strip()
    clean_source = (source_text or "").strip()
    if not clean_summary or not clean_source:
        return clean_summary

    source_words = clean_source.split()
    summary_words = clean_summary.split()
    if len(summary_words) < len(source_words):
        return clean_summary

    source_sentences = [s.strip() for s in clean_source.replace("\n", " ").split(".") if s.strip()]
    summary_sentences = [s.strip() for s in clean_summary.replace("\n", " ").split(".") if s.strip()]

    if len(summary_sentences) > 1:
        shortened = ". ".join(summary_sentences[:-1]).strip()
        if shortened and shortened[-1] not in ".!?":
            shortened += "."
        if shortened and len(shortened.split()) < len(source_words):
            return shortened

    max_words = max(10, len(source_words) - 1)
    shortened = " ".join(summary_words[:max_words]).strip()
    shortened = shortened.rstrip(",;:-")
    if shortened and shortened[-1] not in ".!?":
        shortened += "."

    if len(shortened.split()) >= len(source_words) and len(source_sentences) > 1:
        shortened = ". ".join(source_sentences[:-1]).strip()
        if shortened and shortened[-1] not in ".!?":
            shortened += "."

    return shortened or clean_summary


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

        # STEP 2: Initialize summarizer once and build chunks from the same instance
        update_progress(book_id, "Loading AI model...", 35)

        try:
            summarizer = FastSummarizer()
        except Exception as e:
            print(f"Primary model failed: {e}")
            summarizer = SimpleSummarizer()

        processed = preprocess_for_summarization(raw_text, chunk_size=800)
        if processed.get("success") and processed.get("chunks"):
            chunks = processed["chunks"]
            raw_text = processed.get("cleaned_text", raw_text)
        else:
            raw_word_count = len(raw_text.split())
            if summary_options.get("source") == "pasted_text" and raw_word_count <= 1200:
                chunks = [raw_text]
            else:
                chunks = summarizer.smart_chunk_text(raw_text)

        total_chunks = len(chunks)
        update_progress(book_id, f"Prepared {total_chunks} smart chunks", 40)
        
        # Configure length
        length = summary_options.get("length", "medium")
        length_profile = get_length_profile(length)
        length_params = {
            "min_length": length_profile["min_length"],
            "max_length": length_profile["max_length"],
        }
        
        # STEP 4: Chunk summarization
        chunk_summaries = []
        start_loop = time.time()
        progress_interval = max(1, total_chunks // 10) if total_chunks else 1

        for i, chunk_text in enumerate(chunks):
            elapsed = time.time() - start_loop
            avg_time = elapsed / (i + 1)
            remaining = avg_time * (total_chunks - i - 1)

            percent = 40 + int(((i + 1) / total_chunks) * 45)

            if i == 0 or i == total_chunks - 1 or (i + 1) % progress_interval == 0:
                update_progress(
                    book_id,
                    f"Summarizing {i+1}/{total_chunks} • ETA {int(remaining)}s",
                    percent
                )

            summary = await asyncio.to_thread(
                summarizer.summarize_chunk,
                chunk_text,
                length_params["min_length"],
                length_params["max_length"],
                summary_options,
            )

            if summary:
                chunk_summaries.append(summary)


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
        combined = " ".join(chunk_summaries).strip()

        combine_threshold = max(length_profile["combine_max"] + 40, int(length_profile["combine_max"] * 1.3))
        should_recombine = total_chunks > 1 or len(combined.split()) > combine_threshold

        if should_recombine:
            final_summary = await asyncio.to_thread(
                summarizer.summarize_chunk,
                combined,
                length_profile["combine_min"],
                length_profile["combine_max"],
                summary_options,
            )
        else:
            final_summary = combined

        final_word_count = len(final_summary.split()) if final_summary else 0
        min_expected_words = max(40, int(length_params["min_length"] * 0.6))
        if final_word_count < min_expected_words:
            fallback_summary = await asyncio.to_thread(
                summarizer.extractive_fallback if hasattr(summarizer, "extractive_fallback") else SimpleSummarizer().summarize_chunk,
                raw_text,
                length_params["min_length"],
                length_params["max_length"],
                summary_options,
            )
            if fallback_summary and len(fallback_summary.split()) > final_word_count:
                final_summary = fallback_summary

        if final_summary and hasattr(summarizer, "refine_summary"):
            refined_summary = await asyncio.to_thread(
                summarizer.refine_summary,
                final_summary,
                length_profile["combine_min"] if should_recombine else length_params["min_length"],
                length_profile["combine_max"] if should_recombine else length_params["max_length"],
                summary_options,
            )
            if refined_summary:
                final_summary = refined_summary

        # STEP 7: Style formatting
        try:
            final_summary = finalize_summary_text(final_summary, summary_options)
        except Exception:
            pass

        # STEP 8: Final cleanup
        final_summary = final_summary.strip()
        if not final_summary or len(final_summary) < 20:
            final_summary = "Summary generated: " + raw_text[:200] + "..." if len(raw_text) > 200 else raw_text

        final_summary = ensure_summary_shorter_than_source(final_summary, raw_text)
        
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
