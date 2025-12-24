import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import heapq
from typing import List, Dict, Tuple
import json

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class SummaryRefiner:
    """
    Comprehensive post-processing and refinement of generated summaries
    """
    
    def __init__(self, language='english'):
        self.language = language
        self.stop_words = set(stopwords.words(language))
    
    def remove_duplicate_sentences(self, summary: str, similarity_threshold: float = 0.8) -> str:
        """
        Remove duplicate or highly similar sentences from summary
        """
        if not summary:
            return ""
        
        sentences = sent_tokenize(summary)
        if len(sentences) <= 1:
            return summary
        
        unique_sentences = []
        seen_hashes = set()
        
        for sentence in sentences:
            # Create a simple hash based on cleaned content
            cleaned = self._clean_text(sentence)
            words = set(word_tokenize(cleaned.lower()))
            
            # Calculate similarity with already seen sentences
            is_duplicate = False
            for seen_sentence in unique_sentences:
                seen_cleaned = self._clean_text(seen_sentence)
                seen_words = set(word_tokenize(seen_cleaned.lower()))
                
                # Calculate Jaccard similarity
                intersection = len(words.intersection(seen_words))
                union = len(words.union(seen_words))
                similarity = intersection / union if union > 0 else 0
                
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sentences.append(sentence)
                # Store a normalized version for comparison
                normalized = ' '.join(sorted(words))
                seen_hashes.add(hash(normalized))
        
        return ' '.join(unique_sentences)
    
    def reorder_sentences_logically(self, summary: str) -> str:
        """
        Reorder sentences to improve logical flow
        """
        if not summary:
            return ""
        
        sentences = sent_tokenize(summary)
        if len(sentences) <= 2:
            return summary
        
        # Score each sentence based on various factors
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = self._calculate_sentence_score(sentence, i, sentences)
            scored_sentences.append((score, sentence))
        
        # Sort by score (higher = should come first)
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Reconstruct summary
        return ' '.join([s[1] for s in scored_sentences])
    
    def _calculate_sentence_score(self, sentence: str, index: int, all_sentences: List[str]) -> float:
        """Calculate importance score for sentence ordering"""
        score = 0.0
        
        # Position bias (first sentences often important)
        if index == 0:
            score += 2.0
        elif index == len(all_sentences) - 1:
            score += 1.0  # Concluding sentences
        
        # Length factor (very short or very long sentences might be less ideal for start)
        words = word_tokenize(sentence)
        if 8 <= len(words) <= 20:
            score += 1.0
        
        # Indicator words
        opening_indicators = ['however', 'furthermore', 'additionally', 'moreover', 'in conclusion']
        closing_indicators = ['therefore', 'thus', 'consequently', 'in summary', 'finally']
        
        first_word = words[0].lower() if words else ""
        if first_word in opening_indicators:
            score -= 1.0  # These often shouldn't start the summary
        if any(indicator in sentence.lower() for indicator in closing_indicators):
            score += 0.5  # These might indicate concluding statements
        
        return score
    
    def enforce_length_constraints(self, summary: str, 
                                   target_word_count: int = None,
                                   target_char_count: int = None,
                                   mode: str = 'trim') -> str:
        """
        Adjust summary to meet specific length constraints
        Modes: 'trim', 'expand', 'smart_trim'
        """
        if not summary:
            return ""
        
        sentences = sent_tokenize(summary)
        current_word_count = len(word_tokenize(summary))
        current_char_count = len(summary)
        
        # If no target specified or already within limits
        if (not target_word_count and not target_char_count) or \
           (target_word_count and current_word_count <= target_word_count) or \
           (target_char_count and current_char_count <= target_char_count):
            return summary
        
        if mode == 'trim':
            return self._trim_summary(summary, target_word_count, target_char_count)
        elif mode == 'smart_trim':
            return self._smart_trim_summary(summary, target_word_count, target_char_count)
        elif mode == 'expand':
            return self._expand_summary(summary, target_word_count, target_char_count)
        else:
            return summary
    
    def _trim_summary(self, summary: str, target_words: int = None, target_chars: int = None) -> str:
        """Simple trimming from the end"""
        sentences = sent_tokenize(summary)
        result = []
        current_words = 0
        
        for sentence in sentences:
            sentence_words = len(word_tokenize(sentence))
            if target_words and (current_words + sentence_words) > target_words:
                # Add partial sentence if we have space
                if target_words - current_words >= 3:  # At least 3 words
                    words = word_tokenize(sentence)
                    partial = ' '.join(words[:target_words - current_words]) + '...'
                    result.append(partial)
                break
            
            result.append(sentence)
            current_words += sentence_words
            
            if target_chars and len(' '.join(result)) > target_chars:
                result.pop()
                break
        
        return ' '.join(result)
    
    def _smart_trim_summary(self, summary: str, target_words: int = None, target_chars: int = None) -> str:
        """Trim based on sentence importance"""
        sentences = sent_tokenize(summary)
        
        # Score each sentence
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            importance = self._calculate_sentence_importance(sentence, i, len(sentences))
            scored_sentences.append((importance, sentence))
        
        # Sort by importance (descending)
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Select most important sentences until length limit
        selected = []
        current_words = 0
        
        for importance, sentence in scored_sentences:
            sentence_words = len(word_tokenize(sentence))
            if target_words and (current_words + sentence_words) > target_words:
                continue
            
            selected.append(sentence)
            current_words += sentence_words
            
            if target_chars and len(' '.join(selected)) > target_chars:
                selected.pop()
                break
        
        # Reorder selected sentences to original order
        selected_in_order = [s for s in sentences if s in selected]
        return ' '.join(selected_in_order)
    
    def _calculate_sentence_importance(self, sentence: str, position: int, total_sentences: int) -> float:
        """Calculate importance score for trimming decisions"""
        score = 0.0
        words = word_tokenize(sentence.lower())
        
        # Position importance (first and last sentences often important)
        if position == 0:
            score += 2.0
        if position == total_sentences - 1:
            score += 1.5
        
        # Length factor (medium length sentences often contain core information)
        if 6 <= len(words) <= 25:
            score += 1.0
        
        # Keyword indicators
        important_indicators = ['important', 'key', 'main', 'primary', 'essential', 
                               'critical', 'significant', 'crucial', 'major']
        for indicator in important_indicators:
            if indicator in sentence.lower():
                score += 1.5
                break
        
        # Question indicators (questions might be less important in summaries)
        if sentence.strip().endswith('?'):
            score -= 0.5
        
        return score
    
    def _expand_summary(self, summary: str, target_words: int = None, target_chars: int = None) -> str:
        """
        For Task 12 - placeholder for expansion logic
        In practice, this would involve retrieving additional content from source
        """
        # This is a complex task that would require access to original text
        # For now, we'll return the summary as-is
        return summary
    
    def format_enhancements(self, summary: str) -> str:
        """
        Apply formatting enhancements to summary
        """
        if not summary:
            return ""
        
        # 1. Capitalize first letter
        summary = summary.strip()
        if summary:
            summary = summary[0].upper() + summary[1:]
        
        # 2. Ensure ends with punctuation
        if summary and summary[-1] not in '.!?':
            summary += '.'
        
        # 3. Fix multiple spaces
        summary = re.sub(r'\s+', ' ', summary)
        
        # 4. Fix capitalization after punctuation
        sentences = sent_tokenize(summary)
        formatted_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Capitalize first letter of each sentence
                if len(sentence) > 1:
                    sentence = sentence[0].upper() + sentence[1:]
                formatted_sentences.append(sentence)
        
        # 5. Join with proper spacing
        result = ' '.join(formatted_sentences)
        
        # 6. Fix common punctuation issues
        result = re.sub(r'\s+([,.!?])', r'\1', result)  # Remove space before punctuation
        result = re.sub(r'([,.!?])([A-Za-z])', r'\1 \2', result)  # Add space after punctuation
        
        return result
    
    def extract_keywords(self, summary: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords from summary
        """
        if not summary:
            return []
        
        # Tokenize and clean
        words = word_tokenize(summary.lower())
        words = [w for w in words if w.isalnum() and w not in self.stop_words]
        
        # Count frequencies
        word_freq = Counter(words)
        
        # Get most common
        keywords = [word for word, freq in word_freq.most_common(top_n)]
        
        return keywords
    
    def identify_themes(self, summary: str, max_themes: int = 3) -> List[Dict]:
        """
        Identify main themes/topics in summary
        """
        if not summary:
            return []
        
        sentences = sent_tokenize(summary)
        all_words = []
        
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            words = [w for w in words if w.isalnum() and w not in self.stop_words and len(w) > 3]
            all_words.extend(words)
        
        # Simple theme identification based on word co-occurrence
        word_freq = Counter(all_words)
        themes = []
        
        for word, freq in word_freq.most_common(max_themes * 2):
            if freq >= 2:  # Word appears at least twice
                themes.append({
                    'theme': word.capitalize(),
                    'frequency': freq,
                    'related_words': self._find_related_words(word, all_words)
                })
        
        return themes[:max_themes]
    
    def _find_related_words(self, keyword: str, all_words: List[str], window_size: int = 3) -> List[str]:
        """Find words that frequently appear near the keyword"""
        # Simplified implementation
        related = []
        for i, word in enumerate(all_words):
            if word == keyword:
                # Get words in window around keyword
                start = max(0, i - window_size)
                end = min(len(all_words), i + window_size + 1)
                context = all_words[start:end]
                related.extend([w for w in context if w != keyword])
        
        # Count and return most frequent
        return [word for word, freq in Counter(related).most_common(3)]
    
    def _clean_text(self, text: str) -> str:
        """Clean text for comparison"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.strip()
    
    def refine_summary(self, summary: str, refinement_options: Dict = None) -> Dict:
        """
        Main method to apply all refinements
        """
        if refinement_options is None:
            refinement_options = {}
        
        original = summary
        refined = summary
        
        # Apply refinements based on options
        if refinement_options.get('remove_duplicates', True):
            refined = self.remove_duplicate_sentences(refined)
        
        if refinement_options.get('reorder_sentences', True):
            refined = self.reorder_sentences_logically(refined)
        
        if refinement_options.get('format_enhancements', True):
            refined = self.format_enhancements(refined)
        
        # Apply length constraints if specified
        target_words = refinement_options.get('target_word_count')
        target_chars = refinement_options.get('target_char_count')
        if target_words or target_chars:
            mode = refinement_options.get('length_constraint_mode', 'smart_trim')
            refined = self.enforce_length_constraints(
                refined, target_words, target_chars, mode
            )
        
        # Extract additional information
        keywords = self.extract_keywords(refined, refinement_options.get('keyword_count', 5))
        themes = self.identify_themes(refined, refinement_options.get('theme_count', 3))
        
        return {
            'original_summary': original,
            'refined_summary': refined,
            'keywords': keywords,
            'themes': themes,
            'stats': {
                'original_word_count': len(word_tokenize(original)),
                'refined_word_count': len(word_tokenize(refined)),
                'original_char_count': len(original),
                'refined_char_count': len(refined),
                'sentences_removed': len(sent_tokenize(original)) - len(sent_tokenize(refined))
            }
        }