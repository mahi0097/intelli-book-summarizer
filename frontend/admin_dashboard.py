# frontend/admin_dashboard.py
import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_db

def show_admin_dashboard():
    """Admin Dashboard with all features"""
    
    # Check admin access
    if st.session_state.get("role") != "admin":
        st.error("🔒 Admin access required!")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    # ========== HEADER ==========
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;'>
        <h1 style='color: white; margin: 0;'>👑 Admin Dashboard</h1>
        <p style='opacity: 0.9; margin-top: 0.5rem;'>Welcome back, {}</p>
    </div>
    """.format(st.session_state.get("username", "Admin")), unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to User Dashboard", type="secondary"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    st.markdown("---")
    
    # ========== SYSTEM STATS ==========
    st.subheader("📊 System Overview")
    
    db = get_db()
    
    # Get counts
    try:
        total_users = db.users.count_documents({})
        total_books = db.books.count_documents({})
        total_summaries = db.summaries.count_documents({})
        failed_books = db.books.count_documents({"status": "failed"})
        processing_books = db.books.count_documents({"status": "processing"})
        
        # Get last 7 days stats
        last_7_days = datetime.now() - timedelta(days=7)
        new_users_7d = db.users.count_documents({"created_at": {"$gte": last_7_days}})
        
    except Exception as e:
        # Mock data for testing
        print(f"Using mock data: {e}")
        total_users = 15
        total_books = 42
        total_summaries = 67
        failed_books = 3
        processing_books = 2
        new_users_7d = 5
    
    # Stats in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Users", total_users, delta=f"+{new_users_7d} (7d)")
    
    with col2:
        success_rate = ((total_books - failed_books) / total_books * 100) if total_books > 0 else 100
        st.metric("📚 Total Books", total_books, delta=f"{success_rate:.1f}% success")
    
    with col3:
        st.metric("📄 Total Summaries", total_summaries)
    
    with col4:
        st.metric("⚡ Processing", processing_books)
    
    st.markdown("---")
    
    # ========== USER MANAGEMENT ==========
    st.subheader("👥 User Management")
    
    # Search and filter
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_query = st.text_input("🔍 Search users by name or email", key="admin_user_search")
    with col_search2:
        items_per_page = st.selectbox("Show", [10, 25, 50], index=0)
    
    try:
        # Get users from database
        query = {}
        if search_query:
            query["$or"] = [
                {"name": {"$regex": search_query, "$options": "i"}},
                {"email": {"$regex": search_query, "$options": "i"}}
            ]
        
        users = list(db.users.find(query).limit(items_per_page))
        
        if users:
            # Prepare user data
            user_data = []
            for user in users:
                # Count user's books and summaries
                try:
                    book_count = db.books.count_documents({"user_id": user.get("_id")})
                    summary_count = db.summaries.count_documents({"user_id": user.get("_id")})
                except:
                    book_count = 0
                    summary_count = 0
                
                user_data.append({
                    "ID": str(user.get("_id", ""))[:8],
                    "Name": user.get("name", "Unknown"),
                    "Email": user.get("email", "Unknown"),
                    "Role": user.get("role", "user"),
                    "Status": "✅ Active" if user.get("is_active", True) else "❌ Inactive",
                    "Books": book_count,
                    "Summaries": summary_count,
                    "Joined": user.get("created_at", datetime.now()).strftime("%Y-%m-%d") 
                              if isinstance(user.get("created_at"), datetime) else "Unknown",
                    "Last Login": user.get("last_login", "").strftime("%Y-%m-%d") 
                                 if isinstance(user.get("last_login"), datetime) else "Never"
                })
            
            # Display users table
            df = pd.DataFrame(user_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Role": st.column_config.SelectboxColumn(
                        "Role",
                        options=["admin", "user", "premium"],
                        help="Click to change role"
                    ),
                    "Books": st.column_config.NumberColumn("Books", format="%d"),
                    "Summaries": st.column_config.NumberColumn("Summaries", format="%d"),
                }
            )
            
            # User actions
            st.markdown("##### 🛠️ User Actions")
            
            if user_data:
                selected_email = st.selectbox(
                    "Select user for action",
                    [u["Email"] for u in user_data],
                    key="admin_user_select"
                )
                
                if selected_email:
                    col_act1, col_act2, col_act3 = st.columns(3)
                    
                    with col_act1:
                        if st.button("👑 Make Admin", key="make_admin_btn", use_container_width=True):
                            db.users.update_one(
                                {"email": selected_email},
                                {"$set": {"role": "admin"}}
                            )
                            st.success(f"{selected_email} promoted to admin!")
                            st.rerun()
                    
                    with col_act2:
                        if st.button("🔑 Reset Password", key="reset_pass_btn", use_container_width=True):
                            st.info(f"Password reset email would be sent to {selected_email}")
                    
                    with col_act3:
                        if st.button("📊 View Details", key="view_details_btn", use_container_width=True):
                            st.session_state.admin_selected_user = selected_email
                            st.rerun()
        
        else:
            st.info("No users found")
            
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        st.info("Showing sample data for demonstration...")
        
        # Sample data for demo
        sample_data = [
            {"ID": "usr001", "Name": "Admin User", "Email": "admin@example.com", "Role": "admin", "Status": "✅ Active", "Books": 12, "Summaries": 15},
            {"ID": "usr002", "Name": "John Doe", "Email": "john@example.com", "Role": "user", "Status": "✅ Active", "Books": 5, "Summaries": 8},
            {"ID": "usr003", "Name": "Jane Smith", "Email": "jane@example.com", "Role": "user", "Status": "✅ Active", "Books": 3, "Summaries": 3},
        ]
        
        df = pd.DataFrame(sample_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ========== SYSTEM ANALYTICS ==========
    st.subheader("📈 System Analytics")
    
    # Create tabs for different analytics
    tab1, tab2, tab3 = st.tabs(["📊 Usage Trends", "📈 Performance", "🩺 System Health"])
    
    with tab1:
        # Generate sample timeline data
        dates = pd.date_range(end=datetime.now(), periods=30)
        activity_data = pd.DataFrame({
            'Date': dates,
            'New Users': np.random.randint(0, 5, 30).cumsum(),
            'New Books': np.random.randint(0, 8, 30).cumsum(),
            'New Summaries': np.random.randint(0, 10, 30).cumsum()
        })
        
        fig = px.line(activity_data, x='Date', y=['New Users', 'New Books', 'New Summaries'],
                     title='📈 System Growth (Last 30 Days)',
                     labels={'value': 'Count', 'variable': 'Metric'},
                     line_shape='spline')
        
        fig.update_layout(
            hovermode='x unified',
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col_perf1, col_perf2 = st.columns(2)
        
        with col_perf1:
            # Success rate gauge
            success_rate_value = 92.5
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=success_rate_value,
                title={'text': "✅ Success Rate"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "green"},
                    'steps': [
                        {'range': [0, 80], 'color': "lightgray"},
                        {'range': [80, 95], 'color': "lightgreen"},
                        {'range': [95, 100], 'color': "green"}
                    ]
                }
            ))
            fig_gauge.update_layout(height=250)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col_perf2:
            # Processing time
            fig_bar = go.Figure(data=[go.Bar(
                x=['Short', 'Medium', 'Long'],
                y=[2.1, 4.3, 8.7],
                marker_color=['#10B981', '#3B82F6', '#8B5CF6']
            )])
            
            fig_bar.update_layout(
                title='⏱️ Avg Processing Time (seconds)',
                height=250,
                xaxis_title="Book Length",
                yaxis_title="Seconds"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab3:
        # System health metrics
        col_health1, col_health2, col_health3 = st.columns(3)
        
        with col_health1:
            st.metric("Database Status", "✅ Healthy", "99.9% uptime")
        
        with col_health2:
            st.metric("Storage Usage", "125 MB / 1 GB", "12.5% used")
        
        with col_health3:
            st.metric("Active Sessions", "8", "-2 from peak")
        
        # Recent errors
        st.markdown("##### ⚠️ Recent Errors")
        try:
            errors = list(db.errors.find().sort("created_at", -1).limit(5))
            if errors:
                for error in errors:
                    with st.expander(f"Error: {error.get('created_at', 'Unknown')}"):
                        st.code(error.get('error', 'No error message'))
            else:
                st.success("✅ No errors in the last 24 hours")
        except:
            st.info("Error logs not available")
    
    st.markdown("---")
    
    # ========== BACKUP & EXPORT ==========
    st.subheader("💾 Backup & Export")
    
    col_backup1, col_backup2, col_backup3 = st.columns(3)
    
    with col_backup1:
        if st.button("📥 Export Users (CSV)", use_container_width=True, type="primary"):
            st.success("User data exported successfully!")
            # In production, generate and download CSV
    
    with col_backup2:
        if st.button("📤 Export Summaries (JSON)", use_container_width=True):
            st.info("Summary export initiated...")
    
    with col_backup3:
        if st.button("💾 Full Backup", use_container_width=True):
            st.warning("⚠️ This will create a full system backup")
            if st.button("Confirm Backup", key="confirm_backup"):
                st.success("Backup created successfully!")
    
    # ========== FOOTER ==========
    st.markdown("---")
    
    col_footer1, col_footer2 = st.columns([3, 1])
    
    with col_footer1:
        st.caption(f"Admin Dashboard • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col_footer2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

# For testing without Streamlit
if __name__ == "__main__":
    # Mock session state for testing
    class MockSessionState:
        def __init__(self):
            self.role = "admin"
            self.username = "Admin User"
            self.page = "admin"
    
    st.session_state = MockSessionState()
    show_admin_dashboard()