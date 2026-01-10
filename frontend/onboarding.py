# frontend/onboarding.py
import streamlit as st
from typing import Dict, List, Optional
import time

class OnboardingManager:
    """Manager for user onboarding and tutorials"""
    
    def __init__(self):
        self.tutorials = {
            "first_time": {
                "title": "👋 Welcome to Book Summarizer Pro!",
                "steps": [
                    {
                        "title": "📚 Upload Your First Book",
                        "content": "Start by uploading a PDF, DOCX, or TXT file from the Upload page.",
                        "target_page": "upload",
                        "icon": "📤"
                    },
                    {
                        "title": "🤖 Generate AI Summary",
                        "content": "Choose your preferred summary length and style, then let AI work its magic.",
                        "target_page": "generate_summary",
                        "icon": "✨"
                    },
                    {
                        "title": "📊 View Your Dashboard",
                        "content": "Track your reading progress and view all your summaries in one place.",
                        "target_page": "dashboard",
                        "icon": "📈"
                    },
                    {
                        "title": "🔄 Version History",
                        "content": "Compare different versions of your summaries and revert if needed.",
                        "target_page": "history",
                        "icon": "🕰️"
                    }
                ]
            },
            "upload_guide": {
                "title": "📤 How to Upload Books",
                "steps": [
                    {
                        "title": "Supported Formats",
                        "content": "We support PDF, DOCX, DOC, TXT, and RTF files up to 10MB.",
                        "icon": "📁"
                    },
                    {
                        "title": "File Preparation",
                        "content": "Ensure your file is not password protected and has readable text content.",
                        "icon": "🔍"
                    },
                    {
                        "title": "Metadata (Optional)",
                        "content": "Add author and chapter information to help organize your library.",
                        "icon": "🏷️"
                    }
                ]
            },
            "summary_guide": {
                "title": "✨ Getting the Best Summaries",
                "steps": [
                    {
                        "title": "Choose Length Wisely",
                        "content": "• Short: Key points only\n• Medium: Balanced summary\n• Long: Detailed overview",
                        "icon": "📏"
                    },
                    {
                        "title": "Select Your Style",
                        "content": "• Paragraph: Flowing narrative\n• Bullets: Clear point-by-point",
                        "icon": "🎨"
                    },
                    {
                        "title": "Processing Time",
                        "content": "Longer books may take 30-60 seconds. Be patient for best results!",
                        "icon": "⏱️"
                    }
                ]
            }
        }
    
    def show_first_time_onboarding(self):
        """Show first-time user onboarding"""
        if st.session_state.get("onboarding_completed", False):
            return
        
        # Show welcome modal
        with st.expander("🎉 Welcome to Book Summarizer Pro!", expanded=True):
            st.markdown("""
            ### You're all set! Here's how to get started:
            
            1. **📤 Upload a book** (PDF, DOCX, or TXT)
            2. **🤖 Generate AI summaries** with your preferred settings
            3. **📊 Track your progress** on the dashboard
            4. **📚 Build your digital library**
            
            Need help? Click the 💡 button anytime for tips!
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Start Tutorial", use_container_width=True):
                    st.session_state.show_tutorial = True
                    st.session_state.current_tutorial = "first_time"
                    st.rerun()
            with col2:
                if st.button("Skip & Explore", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.rerun()
    
    def show_tutorial(self, tutorial_key: str):
        """Show interactive tutorial"""
        if tutorial_key not in self.tutorials:
            return
        
        tutorial = self.tutorials[tutorial_key]
        current_step = st.session_state.get(f"tutorial_step_{tutorial_key}", 0)
        
        # Create tutorial container
        tutorial_container = st.container()
        
        with tutorial_container:
            # Tutorial header
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 1rem;
            ">
                <h2 style="color: white; margin: 0;">{tutorial['title']}</h2>
                <p style="opacity: 0.9; margin-top: 0.5rem;">
                    Step {current_step + 1} of {len(tutorial['steps'])}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Current step content
            if current_step < len(tutorial['steps']):
                step = tutorial['steps'][current_step]
                
                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 8px;
                    border-left: 4px solid #3B82F6;
                    margin-bottom: 1.5rem;
                ">
                    <h3 style="color: #1E40AF; margin-top: 0;">
                        {step['icon']} {step['title']}
                    </h3>
                    <p style="font-size: 1.1rem; line-height: 1.6;">
                        {step['content']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Navigation buttons
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if current_step > 0:
                    if st.button("◀ Previous", key=f"prev_{tutorial_key}"):
                        st.session_state[f"tutorial_step_{tutorial_key}"] = current_step - 1
                        st.rerun()
            
            with col2:
                # Progress dots
                progress_html = "<div style='text-align: center;'>"
                for i in range(len(tutorial['steps'])):
                    if i == current_step:
                        progress_html += "🔵"
                    else:
                        progress_html += "⚪"
                progress_html += "</div>"
                st.markdown(progress_html, unsafe_allow_html=True)
            
            with col3:
                if current_step < len(tutorial['steps']) - 1:
                    if st.button("Next ▶", key=f"next_{tutorial_key}", type="primary"):
                        st.session_state[f"tutorial_step_{tutorial_key}"] = current_step + 1
                        st.rerun()
                else:
                    if st.button("Finish Tutorial 🎉", key=f"finish_{tutorial_key}", type="primary"):
                        self.complete_tutorial(tutorial_key)
                        st.rerun()
    
    def complete_tutorial(self, tutorial_key: str):
        """Mark tutorial as completed"""
        st.session_state[f"{tutorial_key}_completed"] = True
        st.session_state.show_tutorial = False
        
        if tutorial_key == "first_time":
            st.session_state.onboarding_completed = True
        
        st.success("✅ Tutorial completed! You're ready to go!")
        time.sleep(1)
    
    def show_contextual_tip(self, context: str, page: str):
        """Show contextual tips based on user activity"""
        tips = {
            "upload": {
                "title": "💡 Upload Tip",
                "content": "For best results, use files with clear text (not scanned PDFs).",
                "icon": "📤"
            },
            "summary": {
                "title": "💡 Summary Tip",
                "content": "Try different summary lengths to find what works best for your content.",
                "icon": "✨"
            },
            "dashboard": {
                "title": "💡 Dashboard Tip",
                "content": "Click on any book card to view details and manage your summaries.",
                "icon": "📊"
            },
            "history": {
                "title": "💡 Version Tip",
                "content": "You can compare different summary versions side by side.",
                "icon": "🔄"
            }
        }
        
        if context in tips and not st.session_state.get(f"tip_seen_{context}", False):
            tip = tips[context]
            
            with st.expander(tip["title"], expanded=True):
                st.markdown(f"{tip['icon']} **{tip['content']}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Got it!", key=f"gotit_{context}"):
                        st.session_state[f"tip_seen_{context}"] = True
                        st.rerun()
                with col2:
                    if st.button("Show more tips", key=f"more_{context}"):
                        st.session_state.show_tips = True
                        st.rerun()
    
    def create_quick_tour_button(self):
        """Create a floating help button"""
        help_html = """
        <style>
            .help-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            }
            .help-button button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                transition: all 0.3s;
            }
            .help-button button:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 16px rgba(0,0,0,0.3);
            }
        </style>
        
        <div class="help-button">
            <button onclick="showHelp()">💡</button>
        </div>
        
        <script>
            function showHelp() {
                // This would trigger a Streamlit callback
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'show_help'}, '*');
            }
        </script>
        """
        
        st.markdown(help_html, unsafe_allow_html=True)
        
        # Check if help button was clicked
        if st.session_state.get("show_help", False):
            self.show_help_center()
            st.session_state.show_help = False
    
    def show_help_center(self):
        """Show help center with all tutorials"""
        with st.sidebar.expander("🆘 Help Center", expanded=True):
            st.markdown("### Need help? Choose a topic:")
            
            topics = [
                {"title": "🚀 Getting Started", "key": "first_time", "icon": "🚀"},
                {"title": "📤 Uploading Books", "key": "upload_guide", "icon": "📤"},
                {"title": "✨ Generating Summaries", "key": "summary_guide", "icon": "✨"},
                {"title": "📊 Using Dashboard", "key": "dashboard_guide", "icon": "📊"},
                {"title": "🔄 Version Management", "key": "version_guide", "icon": "🔄"},
            ]
            
            for topic in topics:
                if st.button(f"{topic['icon']} {topic['title']}", 
                           key=f"help_{topic['key']}", 
                           use_container_width=True):
                    st.session_state.current_tutorial = topic['key']
                    st.session_state.show_tutorial = True
                    st.rerun()
    
    def show_walkthrough(self, page: str):
        """Show page-specific walkthrough"""
        walkthroughs = {
            "upload": [
                "Click 'Browse files' or drag and drop your book",
                "Select your file (PDF, DOCX, or TXT)",
                "Add optional author and chapter information",
                "Click 'Upload & Extract' to begin processing"
            ],
            "generate_summary": [
                "Select your book from the list",
                "Choose summary length (Short, Medium, Long)",
                "Select style (Paragraph or Bullets)",
                "Click 'Generate Summary' and wait for AI magic!"
            ],
            "dashboard": [
                "View your reading statistics at a glance",
                "See recent books and summaries",
                "Click any card for detailed view",
                "Use filters to organize your content"
            ]
        }
        
        if page in walkthroughs and not st.session_state.get(f"walkthrough_seen_{page}", False):
            with st.expander("👣 Step-by-Step Guide", expanded=True):
                st.markdown(f"### How to use the {page.replace('_', ' ').title()} page:")
                
                for i, step in enumerate(walkthroughs[page], 1):
                    st.markdown(f"**{i}. {step}**")
                
                if st.button("✅ I understand", key=f"walkthrough_ok_{page}"):
                    st.session_state[f"walkthrough_seen_{page}"] = True
                    st.rerun()

# Global onboarding manager instance
onboarding_manager = OnboardingManager()

# Convenience functions
def show_onboarding():
    """Show onboarding (convenience function)"""
    onboarding_manager.show_first_time_onboarding()

def show_contextual_tip(context: str, page: str):
    """Show contextual tip (convenience function)"""
    onboarding_manager.show_contextual_tip(context, page)

def show_help_button():
    """Show help button (convenience function)"""
    onboarding_manager.create_quick_tour_button()