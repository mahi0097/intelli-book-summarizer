# routes/summary_routes.py
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from utils.database import (
    get_book_summary_versions,
    get_summary_by_id,
    set_active_summary_version,
    delete_summary,
    restore_summary,
    update_summary_metadata
)
from utils.summary_comparison import SummaryComparer

summary_bp = Blueprint('summary', __name__)

@summary_bp.route('/api/summaries/<book_id>/versions', methods=['GET'])
def get_versions(book_id):
    """Get all summary versions for a book"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        versions = get_book_summary_versions(book_id, user_id)
        
        return jsonify({
            "success": True,
            "book_id": book_id,
            "versions": versions,
            "total_versions": len(versions)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@summary_bp.route('/api/summaries/compare', methods=['POST'])
def compare_summaries():
    """Compare two summary versions"""
    try:
        data = request.json
        summary1_id = data.get('summary1_id')
        summary2_id = data.get('summary2_id')
        
        if not summary1_id or not summary2_id:
            return jsonify({"error": "Both summary IDs are required"}), 400
        
        # Get both summaries
        summary1 = get_summary_by_id(summary1_id)
        summary2 = get_summary_by_id(summary2_id)
        
        if not summary1 or not summary2:
            return jsonify({"error": "One or both summaries not found"}), 404
        
        # Compare the texts
        comparison_result = SummaryComparer.compare_texts(
            summary1.get('summary_text', ''),
            summary2.get('summary_text', '')
        )
        
        # Generate HTML for side-by-side view
        html_comparison = SummaryComparer.generate_side_by_side_html(
            summary1.get('summary_text', ''),
            summary2.get('summary_text', '')
        )
        
        return jsonify({
            "success": True,
            "comparison": comparison_result,
            "html_comparison": html_comparison,
            "summary1": {
                "id": summary1_id,
                "version": summary1.get('version'),
                "created_at": summary1.get('created_at')
            },
            "summary2": {
                "id": summary2_id,
                "version": summary2.get('version'),
                "created_at": summary2.get('created_at')
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@summary_bp.route('/api/summaries/<summary_id>/favorite', methods=['POST'])
def toggle_favorite(summary_id):
    """Toggle favorite status for a summary"""
    try:
        data = request.json
        user_id = data.get('user_id')
        is_favorite = data.get('is_favorite', True)
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        success = update_summary_metadata(
            summary_id=summary_id,
            user_id=user_id,
            updates={"is_favorite": is_favorite}
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Summary {'added to' if is_favorite else 'removed from'} favorites",
                "is_favorite": is_favorite
            })
        else:
            return jsonify({"error": "Failed to update favorite status"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@summary_bp.route('/api/summaries/<summary_id>/default', methods=['POST'])
def set_as_default(summary_id):
    """Set a summary as default for its book"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        # Get the summary to find its book_id
        summary = get_summary_by_id(summary_id)
        if not summary:
            return jsonify({"error": "Summary not found"}), 404
        
        book_id = summary.get('book_id')
        version = summary.get('version')
        
        # Set as active version
        success = set_active_summary_version(book_id, user_id, version)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Summary set as default",
                "book_id": book_id,
                "summary_id": summary_id
            })
        else:
            return jsonify({"error": "Failed to set as default"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@summary_bp.route('/api/summaries/<summary_id>/restore', methods=['POST'])
def restore_version(summary_id):
    """Restore a deleted summary version"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        success = restore_summary(summary_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Summary restored successfully"
            })
        else:
            return jsonify({"error": "Failed to restore summary"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@summary_bp.route('/api/summaries/<summary_id>', methods=['DELETE'])
def delete_version(summary_id):
    """Delete a summary version (soft delete)"""
    try:
        user_id = request.args.get('user_id')
        permanent = request.args.get('permanent', 'false').lower() == 'true'
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        success = delete_summary(summary_id, user_id, permanent=permanent)
        
        if success:
            message = "Summary permanently deleted" if permanent else "Summary moved to archive"
            return jsonify({
                "success": True,
                "message": message
            })
        else:
            return jsonify({"error": "Failed to delete summary"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500