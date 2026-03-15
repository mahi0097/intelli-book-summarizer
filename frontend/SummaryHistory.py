# frontend/SummaryHistory.py - UPDATED VERSION
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import sys
from bson import ObjectId

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.database import (
    db,
    get_book_summary_versions,
    get_summary_by_id,
    set_active_summary_version,
    update_summary_metadata,
    delete_summary,
    restore_summary,
    get_books_by_user,
    get_user_by_id
)
# ✅ Import sidebar CSS from navbar.py
from frontend.navbar import get_sidebar_css


def load_summary_history_css():
    # ✅ Inject sidebar CSS from navbar.py
    sidebar_css = get_sidebar_css()
    st.markdown(sidebar_css, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ===============================
       THEME VARIABLES
    =============================== */
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --bg-light: #f8fafc;
        --bg-dark: #0f172a;
        --card-light: #ffffff;
        --card-dark: #1e293b;
        --border-light: #e5e7eb;
        --border-dark: #334155;
        --success: #16a34a;
        --warning: #f59e0b;
        --danger: #dc2626;
    }

    /* ===============================
       PAGE BACKGROUND
    =============================== */
    .stApp {
        background: #eef6ff;
    }

    @media (prefers-color-scheme: dark) {
        .stApp {
            background: var(--bg-dark);
            color: #e5e7eb;
        }
    }

    /* ===============================
       HEADERS
    =============================== */
    h1, h2, h3 {
        color: #1e3a8a;
        font-weight: 700;
    }

    /* ===============================
       CARDS / SECTIONS
    =============================== */
    [data-testid="stMetric"],
    [data-testid="stExpander"],
    [data-testid="stDataFrame"] {
        background: var(--card-light);
        border-radius: 14px;
        border: 1px solid var(--border-light);
        padding: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.06);
        animation: fadeUp 0.4s ease;
    }

    @media (prefers-color-scheme: dark) {
        [data-testid="stMetric"],
        [data-testid="stExpander"],
        [data-testid="stDataFrame"] {
            background: var(--card-dark);
            border-color: var(--border-dark);
        }
    }

    /* Hover effect */
    [data-testid="stExpander"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 18px 40px rgba(37,99,235,0.25);
    }

    /* ===============================
       TABLE (DATAFRAME)
    =============================== */
    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
    }

    /* ===============================
       BUTTONS
    =============================== */
    .main .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white;
        border-radius: 12px;
        font-weight: 600;
        border: none;
        transition: all 0.25s ease;
    }

    .main .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(37,99,235,0.4);
    }

    /* Primary action */
    button[kind="primary"] {
        background: linear-gradient(135deg, #16a34a, #15803d) !important;
    }

    /* ===============================
       TEXT AREAS (SUMMARY VIEW)
    =============================== */
    textarea {
        border-radius: 12px !important;
        border: 1px solid var(--border-light) !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* ===============================
       DIVIDERS
    =============================== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #93c5fd, transparent);
        margin: 1.5rem 0;
    }

    /* ===============================
       ANIMATIONS
    =============================== */
    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(14px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """, unsafe_allow_html=True)


def summary_history_page():
    load_summary_history_css()

    """Display summary version history with management features"""
    st.title("📜 Summary Version History")

    # Check authentication
    if not st.session_state.get('logged_in', False):
        st.error("Please login to view summary history")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.rerun()
        return

    # Normalize user_id
    user_id = st.session_state.get("user_id")

    if not user_id:
        st.error("User session not found. Please login again.")
        st.session_state.page = "login"
        st.rerun()
        return

    if not isinstance(user_id, ObjectId):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            st.error("Invalid user ID format. Please login again.")
            st.session_state.page = "login"
            st.rerun()
            return

    try:
        user_books = get_books_by_user(user_id, limit=50)
    except Exception as e:
        st.error(f"Error loading books: {e}")
        user_books = []

    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])

    with filter_col1:
        if user_books:
            book_options = {}
            for book in user_books:
                book_id = str(book['_id'])
                book_title = book.get('title', 'Untitled')
                author = book.get('author', 'Unknown')
                display_text = f"{book_title} by {author}" if author != "Unknown" else book_title
                book_options[display_text] = book_id

            book_options["📚 All Books"] = "all"

            selected_book_label = st.selectbox("Select Book", options=list(book_options.keys()))
            selected_book_id = book_options[selected_book_label]
        else:
            st.info("No books found. Upload a book first.")
            selected_book_id = None

    with filter_col2:
        show_archived = st.checkbox("Show Archived", value=False)

    with filter_col3:
        show_favorites = st.checkbox("Favorites Only", value=False)

    if selected_book_id and selected_book_id != "all":
        try:
            versions = get_book_summary_versions(
                str(selected_book_id),
                str(user_id)
            )

            active_versions = [v for v in versions if v.get('is_active')]
            archived_versions = [v for v in versions if v.get('deleted_at')]
            favorite_versions = [v for v in versions if v.get('is_favorite')]

            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            with stat_col1:
                st.metric("Total Versions", len(versions))
            with stat_col2:
                st.metric("Active Versions", len(active_versions))
            with stat_col3:
                st.metric("Archived", len(archived_versions))
            with stat_col4:
                st.metric("Favorites", len(favorite_versions))
        except Exception as e:
            st.warning(f"Could not load stats: {e}")

    # Main content
    if not selected_book_id:
        return

    # Title
    if selected_book_id == "all":
        st.subheader("All Summary Versions")
    else:
        try:
            book_data = db.books.find_one({"_id": ObjectId(selected_book_id)})
            if book_data:
                title = book_data.get('title', 'Untitled')
                author = book_data.get('author', '')
                if author:
                    st.subheader(f"Summary Versions for: {title} by {author}")
                else:
                    st.subheader(f"Summary Versions for: {title}")
            else:
                st.subheader("Summary Versions")
        except:
            st.subheader("Summary Versions")

    # Load versions
    try:
        if selected_book_id == "all":
            user_books = get_books_by_user(user_id, limit=20)
            all_versions = []

            for book in user_books:
                book_id = str(book['_id'])
                versions = get_book_summary_versions(book_id, user_id)
                for version in versions:
                    version['book_title'] = book.get('title', 'Untitled')[:30]
                    version['book_author'] = book.get('author', 'Unknown')[:20]
                    all_versions.append(version)

            versions = all_versions
        else:
            versions = get_book_summary_versions(selected_book_id, user_id)
    except Exception as e:
        st.error(f"Error loading versions: {e}")
        st.info("Try uploading a book and generating summaries first.")
        return

    # Apply filters
    filtered_versions = []
    for version in versions:
        include = True

        if not show_archived and version.get('deleted_at'):
            include = False

        if show_favorites and not version.get('is_favorite'):
            include = False

        if include:
            filtered_versions.append(version)

    if not filtered_versions:
        st.info("No summary versions found with current filters.")

        if selected_book_id != "all" and not show_archived:
            if st.button("Generate First Summary for This Book"):
                st.session_state.current_book = selected_book_id
                st.session_state.page = "generate_summary"
                st.rerun()
        return

    # Display versions in a table
    st.write(f"**Found {len(filtered_versions)} version(s)**")

    version_data = []
    for version in filtered_versions:
        created_at = version.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        version_num = version.get('version', 1)

        version_data.append({
            "Version": f"v{version_num}",
            "Book": version.get('book_title', version.get('book_info', {}).get('title', 'Unknown'))[:25],
            "Created": created_at.strftime('%Y-%m-%d %H:%M'),
            "Words": version.get('word_count', 0),
            "Status": "✅ Active" if version.get('is_active') else
                      "📦 Archived" if version.get('deleted_at') else "💤 Inactive",
            "Favorite": "⭐" if version.get('is_favorite') else "",
            "Summary ID": str(version.get('_id', '')),
            "Book ID": str(version.get('book_id', ''))
        })

    if version_data:
        df = pd.DataFrame(version_data)

        st.dataframe(
            df,
            column_config={
                "Summary ID": st.column_config.TextColumn("ID", width="small"),
                "Book ID": st.column_config.TextColumn("Book ID", width="small"),
                "Favorite": st.column_config.TextColumn("Fav", width="small"),
                "Status": st.column_config.TextColumn("Status", width="medium"),
                "Version": st.column_config.TextColumn("Ver", width="small"),
                "Words": st.column_config.NumberColumn("Words", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )

    # Version actions section
    st.divider()
    st.subheader("📋 Version Actions")

    col1, col2 = st.columns(2)

    with col1:
        if version_data:
            version_options = {f"{row['Version']} - {row['Book'][:20]}... ({row['Created']})": row['Summary ID']
                               for row in version_data}
            selected_version = st.selectbox("Select Version", options=list(version_options.keys()))
            selected_version_id = version_options.get(selected_version)
        else:
            st.info("No versions available")
            selected_version_id = None

    with col2:
        action = st.selectbox(
            "Choose Action",
            [
                "View Summary Details",
                "Set as Default/Active",
                "Toggle Favorite Status",
                "Compare with Another Version",
                "Restore Version",
                "Move to Archive",
                "Permanently Delete"
            ]
        )

    # Action buttons
    if selected_version_id:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🚀 Execute Action", use_container_width=True, type="primary"):
                handle_version_action(selected_version_id, action, user_id, selected_book_id)

        with col2:
            if st.button("🔄 Refresh List", use_container_width=True):
                st.rerun()

        with col3:
            if action == "Compare with Another Version" and selected_version_id:
                compare_options = []
                if version_data:
                    compare_options = [v for k, v in version_options.items() if v != selected_version_id]

                if compare_options:
                    compare_version_id = st.selectbox(
                        "Compare With",
                        options=compare_options,
                        key="compare_select"
                    )

                    if st.button("🔍 Quick Compare", use_container_width=True):
                        compare_versions(selected_version_id, compare_version_id, user_id)

    # Batch operations
    st.divider()
    st.subheader("📦 Batch Operations")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗑️ Archive All Inactive", use_container_width=True):
            archive_all_inactive(selected_book_id if selected_book_id != "all" else None, user_id)

    with col2:
        if st.button("⭐ Export All Favorites", use_container_width=True):
            export_favorites(filtered_versions)

    with col3:
        if st.button("📊 Statistics Report", use_container_width=True):
            show_statistics_report(filtered_versions)

    # Export all versions
    st.divider()
    if st.button("📥 Export All Versions (JSON)", use_container_width=True):
        export_all_versions(filtered_versions)


def handle_version_action(version_id, action, user_id, book_id):
    """Handle different version actions"""
    try:
        if action == "View Summary Details":
            summary = get_summary_by_id(version_id, include_book_info=True)

            if summary:
                with st.expander("📄 Summary Details", expanded=True):
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.write("**Metadata:**")
                        st.write(f"Version: v{summary.get('version', 1)}")

                        created_at = summary.get('created_at')
                        if isinstance(created_at, str):
                            try:
                                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            except:
                                created_at = datetime.now()
                        elif not isinstance(created_at, datetime):
                            created_at = datetime.now()

                        st.write(f"Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"Words: {summary.get('word_count', 0)}")
                        st.write(f"Characters: {summary.get('char_count', 0)}")

                        status = "✅ Active" if summary.get('is_active') else "📦 Archived" if summary.get('deleted_at') else "💤 Inactive"
                        st.write(f"Status: {status}")
                        st.write(f"Favorite: {'⭐ Yes' if summary.get('is_favorite') else 'No'}")

                        if summary.get('book_info'):
                            st.write("**Book Info:**")
                            st.write(f"Title: {summary['book_info'].get('title', 'Unknown')}")
                            st.write(f"Author: {summary['book_info'].get('author', 'Unknown')}")

                    with col2:
                        st.write("**Summary Text:**")
                        summary_text = summary.get('summary_text', '')
                        st.text_area("", summary_text, height=300, disabled=True)

                        words = len(summary_text.split())
                        chars = len(summary_text)
                        st.caption(f"{words} words, {chars} characters")

                        if st.button("📋 Copy to Clipboard"):
                            st.code(summary_text)
                            st.success("Copied to clipboard!")
            else:
                st.error("Summary not found")

        elif action == "Set as Default/Active":
            summary = get_summary_by_id(version_id)
            if summary:
                book_id = str(summary.get('book_id'))
                version = summary.get('version', 1)

                if set_active_summary_version(book_id, user_id, version):
                    st.success("✅ Summary set as default version!")
                    st.rerun()
                else:
                    st.error("Failed to set as default")
            else:
                st.error("Summary not found")

        elif action == "Toggle Favorite Status":
            summary = get_summary_by_id(version_id)
            if summary:
                current_status = summary.get('is_favorite', False)

                if update_summary_metadata(version_id, user_id, {"is_favorite": not current_status}):
                    st.success("⭐ Favorite status updated!")
                    st.rerun()
                else:
                    st.error("Failed to update favorite status")
            else:
                st.error("Summary not found")

        elif action == "Restore Version":
            if restore_summary(version_id, user_id):
                st.success("🔄 Version restored!")
                st.rerun()
            else:
                st.error("Failed to restore version")

        elif action == "Move to Archive":
            if st.checkbox("Confirm archive this version?", key=f"archive_confirm_{version_id}"):
                if delete_summary(version_id, user_id, permanent=False):
                    st.success("📦 Version moved to archive!")
                    st.rerun()
                else:
                    st.error("Failed to archive version")

        elif action == "Permanently Delete":
            if st.checkbox("⚠️ **I understand this cannot be undone**", key=f"perm_delete_confirm_{version_id}"):
                if delete_summary(version_id, user_id, permanent=True):
                    st.success("🗑️ Version permanently deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete version")

        elif action == "Compare with Another Version":
            pass

    except Exception as e:
        st.error(f"Error performing action: {str(e)}")


def compare_versions(version1_id, version2_id, user_id):
    """Compare two versions"""
    try:
        summary1 = get_summary_by_id(version1_id)
        summary2 = get_summary_by_id(version2_id)

        if not summary1 or not summary2:
            st.error("One or both summaries not found")
            return

        if str(summary1.get('user_id')) != user_id or str(summary2.get('user_id')) != user_id:
            st.error("Unauthorized access to summaries")
            return

        with st.expander("🔍 Comparison Results", expanded=True):
            st.subheader("📊 Statistics")

            text1 = summary1.get('summary_text', '')
            text2 = summary2.get('summary_text', '')

            words1 = len(text1.split())
            words2 = len(text2.split())
            chars1 = len(text1)
            chars2 = len(text2)

            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, text1, text2).ratio()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                similarity_color = "green" if similarity > 0.8 else "orange" if similarity > 0.5 else "red"
                st.markdown(f"<h3 style='color: {similarity_color};'>{similarity*100:.1f}%</h3>", unsafe_allow_html=True)
                st.caption("Similarity")

            with col2:
                st.metric("Version 1 Words", words1, delta=words1-words2)

            with col3:
                st.metric("Version 2 Words", words2, delta=words2-words1)

            with col4:
                word_diff = abs(words1 - words2)
                st.metric("Difference", word_diff)

            st.divider()

            st.subheader("📝 Side-by-Side Comparison")

            col_a, col_b = st.columns(2)

            with col_a:
                st.write(f"**Version 1 (v{summary1.get('version', 1)})**")
                created1 = summary1.get('created_at')
                created_str = created1.strftime('%Y-%m-%d') if hasattr(created1, 'strftime') else str(created1)[:10]
                st.caption(f"Created: {created_str}")
                st.caption(f"Status: {'Active' if summary1.get('is_active') else 'Inactive'}")
                st.text_area("", text1, height=300, key="text1", disabled=True)

            with col_b:
                st.write(f"**Version 2 (v{summary2.get('version', 2)})**")
                created2 = summary2.get('created_at')
                created_str = created2.strftime('%Y-%m-%d') if hasattr(created2, 'strftime') else str(created2)[:10]
                st.caption(f"Created: {created_str}")
                st.caption(f"Status: {'Active' if summary2.get('is_active') else 'Inactive'}")
                st.text_area("", text2, height=300, key="text2", disabled=True)

            if st.checkbox("Show Detailed Differences", value=False):
                st.subheader("🔍 Detailed Differences")

                import difflib
                d = difflib.Differ()
                diff = list(d.compare(text1.splitlines(), text2.splitlines()))

                diff_html = ""
                for line in diff:
                    if line.startswith('+ '):
                        diff_html += f'<div style="background-color: #d4edda; padding: 2px; margin: 1px;">{line[2:]}</div>'
                    elif line.startswith('- '):
                        diff_html += f'<div style="background-color: #f8d7da; padding: 2px; margin: 1px;">{line[2:]}</div>'
                    elif line.startswith('? '):
                        continue
                    else:
                        diff_html += f'<div style="padding: 2px; margin: 1px;">{line[2:]}</div>'

                st.markdown(diff_html, unsafe_allow_html=True)

            st.divider()
            if st.button("📥 Download Comparison Report"):
                comparison_data = {
                    "version1": {
                        "id": version1_id,
                        "version": summary1.get('version', 1),
                        "word_count": words1,
                        "char_count": chars1,
                        "created_at": str(summary1.get('created_at')),
                        "is_active": summary1.get('is_active', False),
                        "is_favorite": summary1.get('is_favorite', False)
                    },
                    "version2": {
                        "id": version2_id,
                        "version": summary2.get('version', 1),
                        "word_count": words2,
                        "char_count": chars2,
                        "created_at": str(summary2.get('created_at')),
                        "is_active": summary2.get('is_active', False),
                        "is_favorite": summary2.get('is_favorite', False)
                    },
                    "comparison": {
                        "similarity_percentage": similarity * 100,
                        "word_difference": abs(words1 - words2),
                        "char_difference": abs(chars1 - chars2),
                        "comparison_date": str(datetime.now())
                    }
                }

                json_str = json.dumps(comparison_data, indent=2, default=str)
                st.download_button(
                    label="Download JSON Report",
                    data=json_str,
                    file_name=f"comparison_{version1_id[:8]}_vs_{version2_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

    except Exception as e:
        st.error(f"Error comparing versions: {str(e)}")


def archive_all_inactive(book_id, user_id):
    """Archive all inactive versions"""
    try:
        if book_id and book_id != "all":
            versions = get_book_summary_versions(book_id, user_id)
        else:
            user_books = get_books_by_user(user_id, limit=50)
            versions = []
            for book in user_books:
                try:
                    book_versions = get_book_summary_versions(str(book['_id']), user_id)
                    versions.extend(book_versions)
                except:
                    continue

        archived_count = 0
        for version in versions:
            try:
                if not version.get('is_active') and not version.get('deleted_at'):
                    if delete_summary(str(version['_id']), user_id, permanent=False):
                        archived_count += 1
            except:
                continue

        if archived_count > 0:
            st.success(f"✅ Archived {archived_count} inactive versions!")
        else:
            st.info("No inactive versions found to archive")

        st.rerun()

    except Exception as e:
        st.error(f"Error archiving versions: {str(e)}")


def export_favorites(versions):
    """Export all favorite versions"""
    try:
        favorite_versions = [v for v in versions if v.get('is_favorite')]

        if not favorite_versions:
            st.warning("No favorite versions found")
            return

        export_data = []
        for version in favorite_versions:
            try:
                summary = get_summary_by_id(str(version['_id']))
                if summary:
                    export_data.append({
                        "book_title": version.get('book_title', 'Unknown'),
                        "version": version.get('version', 1),
                        "created_at": str(version.get('created_at')),
                        "word_count": version.get('word_count', 0),
                        "summary_text": summary.get('summary_text', ''),
                        "is_active": version.get('is_active', False),
                        "tags": version.get('tags', [])
                    })
            except:
                continue

        json_str = json.dumps(export_data, indent=2, default=str)

        st.download_button(
            label="📥 Download Favorites JSON",
            data=json_str,
            file_name=f"favorite_summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

        st.success(f"Exported {len(export_data)} favorite versions!")

    except Exception as e:
        st.error(f"Error exporting favorites: {str(e)}")


def show_statistics_report(versions):
    """Show statistics report for versions"""
    try:
        if not versions:
            st.info("No versions to analyze")
            return

        total_versions = len(versions)
        active_versions = len([v for v in versions if v.get('is_active')])
        archived_versions = len([v for v in versions if v.get('deleted_at')])
        favorite_versions = len([v for v in versions if v.get('is_favorite')])

        word_counts = [v.get('word_count', 0) for v in versions]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        max_words = max(word_counts) if word_counts else 0
        min_words = min(word_counts) if word_counts else 0

        version_numbers = [v.get('version', 1) for v in versions]
        latest_version = max(version_numbers) if version_numbers else 1

        st.subheader("📊 Statistics Report")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Versions", total_versions)
            st.metric("Active Versions", active_versions)
            st.metric("Archived Versions", archived_versions)
            st.metric("Favorite Versions", favorite_versions)

        with col2:
            st.metric("Average Word Count", f"{avg_words:.0f}")
            st.metric("Max Word Count", max_words)
            st.metric("Min Word Count", min_words)
            st.metric("Latest Version", f"v{latest_version}")

        if len(versions) > 1:
            st.divider()
            st.subheader("📅 Version Timeline")

            timeline_data = []
            for version in versions:
                created = version.get('created_at')
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    except:
                        created = datetime.now()
                elif not isinstance(created, datetime):
                    created = datetime.now()

                timeline_data.append({
                    "Version": f"v{version.get('version', 1)}",
                    "Date": created,
                    "Words": version.get('word_count', 0),
                    "Status": "Active" if version.get('is_active') else "Archived" if version.get('deleted_at') else "Inactive"
                })

            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                timeline_df = timeline_df.sort_values('Date')
                st.dataframe(timeline_df, hide_index=True, use_container_width=True)

    except Exception as e:
        st.error(f"Error generating statistics: {str(e)}")


def export_all_versions(versions):
    """Export all versions as JSON"""
    try:
        if not versions:
            st.warning("No versions to export")
            return

        export_data = []
        for version in versions:
            try:
                summary = get_summary_by_id(str(version['_id']))
                if summary:
                    export_data.append({
                        "id": str(version['_id']),
                        "book_id": str(version.get('book_id', '')),
                        "book_title": version.get('book_title', 'Unknown'),
                        "version": version.get('version', 1),
                        "created_at": str(version.get('created_at')),
                        "updated_at": str(version.get('updated_at', '')),
                        "word_count": version.get('word_count', 0),
                        "char_count": version.get('char_count', 0),
                        "summary_text": summary.get('summary_text', ''),
                        "is_active": version.get('is_active', False),
                        "is_favorite": version.get('is_favorite', False),
                        "deleted_at": str(version.get('deleted_at', '')),
                        "tags": version.get('tags', []),
                        "summary_options": version.get('summary_options', {})
                    })
            except:
                continue

        json_str = json.dumps(export_data, indent=2, default=str)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"all_summary_versions_{timestamp}.json"

        st.download_button(
            label="📥 Download All Versions",
            data=json_str,
            file_name=filename,
            mime="application/json"
        )

        st.success(f"Exported {len(export_data)} versions!")

    except Exception as e:
        st.error(f"Error exporting versions: {str(e)}")


# For backward compatibility with app.py
def summary_history_page_wrapper():
    """Wrapper function for app.py to call without arguments"""
    return summary_history_page()


# For direct execution (testing)
if __name__ == "__main__":
    class MockSessionState:
        def __init__(self):
            self.logged_in = True
            self.user_id = "test_user_id"
            self.page = "history"

    import streamlit as st
    st.session_state = MockSessionState()
    summary_history_page()
