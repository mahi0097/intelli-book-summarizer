import difflib
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class SummaryComparer:
    """Utility class for comparing different summary versions"""
    
    @staticmethod
    def compare_texts(text1: str, text2: str) -> Dict:
        """
        Compare two texts and return detailed differences
        """
        # Split texts into words for word-level comparison
        words1 = text1.split()
        words2 = text2.split()
        
        # Use difflib for sequence matching
        matcher = difflib.SequenceMatcher(None, words1, words2)
        
        changes = []
        similarity = matcher.ratio()
        
        # Get opcodes (operations)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                old_text = ' '.join(words1[i1:i2])
                new_text = ' '.join(words2[j1:j2])
                changes.append({
                    'type': 'modified',
                    'position': i1,
                    'old_text': old_text,
                    'new_text': new_text,
                    'old_length': len(old_text.split()),
                    'new_length': len(new_text.split())
                })
            elif tag == 'delete':
                deleted_text = ' '.join(words1[i1:i2])
                changes.append({
                    'type': 'deleted',
                    'position': i1,
                    'text': deleted_text,
                    'length': len(deleted_text.split())
                })
            elif tag == 'insert':
                inserted_text = ' '.join(words2[j1:j2])
                changes.append({
                    'type': 'added',
                    'position': i1,
                    'text': inserted_text,
                    'length': len(inserted_text.split())
                })
            elif tag == 'equal':
                # No change
                pass
        
        # Calculate statistics
        stats = {
            'similarity_percentage': round(similarity * 100, 2),
            'total_changes': len(changes),
            'words_added': sum(c.get('length', 0) for c in changes if c['type'] == 'added'),
            'words_removed': sum(c.get('length', 0) for c in changes if c['type'] == 'deleted'),
            'words_modified': sum(c.get('old_length', 0) for c in changes if c['type'] == 'modified'),
            'text1_word_count': len(words1),
            'text2_word_count': len(words2),
            'text1_char_count': len(text1),
            'text2_char_count': len(text2)
        }
        
        return {
            'similarity': similarity,
            'stats': stats,
            'changes': changes,
            'timestamp': datetime.utcnow()
        }
    
    @staticmethod
    def generate_html_diff(text1: str, text2: str) -> str:
        """
        Generate HTML with highlighted differences
        """
        d = difflib.HtmlDiff(wrapcolumn=60)
        html_diff = d.make_file(
            text1.splitlines(), 
            text2.splitlines(),
            fromdesc="Version 1",
            todesc="Version 2",
            context=True,
            numlines=3
        )
        return html_diff
    
    @staticmethod
    def generate_side_by_side_html(text1: str, text2: str) -> str:
        """
        Generate side-by-side comparison HTML with inline highlighting
        """
        words1 = text1.split()
        words2 = text2.split()
        
        matcher = difflib.SequenceMatcher(None, words1, words2)
        
        left_html = []
        right_html = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Same text on both sides
                same_text = ' '.join(words1[i1:i2])
                left_html.append(f'<span class="text-unchanged">{same_text}</span>')
                right_html.append(f'<span class="text-unchanged">{same_text}</span>')
            elif tag == 'delete':
                # Deleted from left (exists in text1 but not text2)
                deleted_text = ' '.join(words1[i1:i2])
                left_html.append(f'<span class="text-deleted">{deleted_text}</span>')
                right_html.append('<span class="text-empty">---</span>')
            elif tag == 'insert':
                # Added to right (exists in text2 but not text1)
                inserted_text = ' '.join(words2[j1:j2])
                left_html.append('<span class="text-empty">---</span>')
                right_html.append(f'<span class="text-added">{inserted_text}</span>')
            elif tag == 'replace':
                # Modified text
                old_text = ' '.join(words1[i1:i2])
                new_text = ' '.join(words2[j1:j2])
                left_html.append(f'<span class="text-modified-old">{old_text}</span>')
                right_html.append(f'<span class="text-modified-new">{new_text}</span>')
        
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .comparison-container { 
                    display: flex; 
                    gap: 20px; 
                    margin-top: 20px;
                }
                .side { 
                    flex: 1; 
                    padding: 15px; 
                    border: 1px solid #ddd; 
                    border-radius: 5px;
                    background: #f9f9f9;
                    min-height: 300px;
                }
                .side-header { 
                    font-weight: bold; 
                    margin-bottom: 10px; 
                    padding-bottom: 5px;
                    border-bottom: 2px solid #007bff;
                }
                .text-unchanged { color: #333; }
                .text-added { 
                    background-color: #d4edda; 
                    color: #155724;
                    padding: 2px;
                    border-radius: 3px;
                }
                .text-deleted { 
                    background-color: #f8d7da; 
                    color: #721c24;
                    text-decoration: line-through;
                    padding: 2px;
                    border-radius: 3px;
                }
                .text-modified-old { 
                    background-color: #fff3cd; 
                    color: #856404;
                    padding: 2px;
                    border-radius: 3px;
                }
                .text-modified-new { 
                    background-color: #cce5ff; 
                    color: #004085;
                    padding: 2px;
                    border-radius: 3px;
                }
                .text-empty { color: #999; font-style: italic; }
                .stats-panel {
                    background: #e9ecef;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .stat-item {
                    margin: 5px 0;
                }
            </style>
        </head>
        <body>
            <div class="stats-panel">
                <h3>Comparison Statistics</h3>
                <div class="stat-item">Text 1: {text1_words} words, {text1_chars} characters</div>
                <div class="stat-item">Text 2: {text2_words} words, {text2_chars} characters</div>
                <div class="stat-item">Similarity: {similarity}%</div>
            </div>
            
            <div class="comparison-container">
                <div class="side">
                    <div class="side-header">Version 1</div>
                    {left_content}
                </div>
                <div class="side">
                    <div class="side-header">Version 2</div>
                    {right_content}
                </div>
            </div>
            
            <div style="margin-top: 20px; font-size: 12px; color: #666;">
                <strong>Legend:</strong>
                <span style="background-color: #d4edda; padding: 2px 5px; margin: 0 5px;">Added</span>
                <span style="background-color: #f8d7da; padding: 2px 5px; margin: 0 5px;">Deleted</span>
                <span style="background-color: #fff3cd; padding: 2px 5px; margin: 0 5px;">Modified (Old)</span>
                <span style="background-color: #cce5ff; padding: 2px 5px; margin: 0 5px;">Modified (New)</span>
            </div>
        </body>
        </html>
        '''
        
        # Calculate similarity
        similarity = round(matcher.ratio() * 100, 2)
        
        # Format the HTML
        html_content = html_template.format(
            left_content=' '.join(left_html),
            right_content=' '.join(right_html),
            text1_words=len(words1),
            text2_words=len(words2),
            text1_chars=len(text1),
            text2_chars=len(text2),
            similarity=similarity
        )
        
        return html_content
    
    @staticmethod
    def get_summary_stats(summary_text: str) -> Dict:
        """
        Get detailed statistics for a summary
        """
        words = summary_text.split()
        sentences = re.split(r'[.!?]+', summary_text)
        paragraphs = summary_text.split('\n\n')
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'char_count': len(summary_text),
            'char_count_no_spaces': len(summary_text.replace(' ', '')),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0
        }