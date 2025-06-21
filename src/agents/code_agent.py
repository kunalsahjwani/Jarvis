# src/agents/code_agent.py - Simplified without emojis
"""
Code Generation Agent - Powers Vibe Studio
Generates Streamlit applications based on user ideas and requirements
Uses Gemini Pro for high-quality code generation
"""

import os
import re
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

class CodeAgent:
    """
    AI agent for generating Streamlit application code
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        # Streamlit project structure template
        self.project_structure = {
            "app.py": "",
            "pages/": {},
            "utils/": {},
            "data/": {},
            "requirements.txt": "",
            "README.md": ""
        }
    
    async def generate_streamlit_app(self, 
                                   app_idea: Dict[str, Any], 
                                   user_requirements: str = "",
                                   complexity_level: str = "simple") -> Dict[str, Any]:
        """
        Generate a complete Streamlit app based on the idea from Ideation app
        """
        try:
            # Extract context from the app idea
            app_name = app_idea.get("name", "MyApp")
            app_category = app_idea.get("category", "productivity")
            app_description = app_idea.get("description", "A web application")
            
            print(f"Generating Streamlit app: {app_name} ({app_category})")
            
            # Generate main application file
            main_app = await self._generate_main_app(app_name, app_description, app_category, user_requirements)
            
            # Generate additional pages based on complexity
            additional_pages = {}
            if complexity_level in ["medium", "complex"]:
                additional_pages = await self._generate_additional_pages(app_idea, complexity_level)
            
            # Generate utility functions
            utils = await self._generate_utils(app_category, complexity_level)
            
            # Generate requirements.txt
            requirements = self._generate_requirements(app_category, complexity_level)
            
            # Compile the complete project
            project_files = {
                "app.py": main_app,
                "requirements.txt": requirements,
                "README.md": self._generate_readme(app_name, app_description),
                **additional_pages,
                **utils
            }
            
            return {
                "success": True,
                "app_name": app_name,
                "project_files": project_files,
                "app_structure": self._analyze_app_structure(project_files),
                "development_notes": self._generate_development_notes(app_idea, project_files),
                "next_steps": self._suggest_next_steps(app_category, complexity_level),
                "run_command": "streamlit run app.py"
            }
            
        except Exception as e:
            print(f"Error generating Streamlit app: {e}")
            return {
                "success": False,
                "error": str(e),
                "app_name": app_idea.get("name", "Unknown")
            }
    
    async def _generate_main_app(self, app_name: str, app_description: str, app_category: str, requirements: str) -> str:
        """
        Generate the main app.py file for the Streamlit app
        """
        try:
            # Get category-specific features
            category_features = self._get_category_features(app_category)
            
            system_prompt = f"""
            Generate a complete Streamlit application (app.py) for a {app_category} application.
            
            App Details:
            - Name: {app_name}
            - Category: {app_category}
            - Description: {app_description}
            - Additional Requirements: {requirements}
            
            Category-specific features to include:
            {category_features}
            
            Technical Requirements:
            1. Use modern Streamlit components (st.columns, st.tabs, st.container, etc.)
            2. Include proper page configuration with title and icon
            3. Add sidebar navigation if applicable
            4. Include sample data for demonstration
            5. Use appropriate charts/visualizations for the category
            6. Add proper error handling
            7. Include session state management where needed
            8. Use st.cache_data for performance
            9. Add helpful tooltips and descriptions
            10. Include a professional header and footer
            
            Generate clean, well-commented, production-ready code that demonstrates the app's core functionality.
            Make it interactive and engaging for users.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Create a complete Streamlit app for {app_name}")
            ]
            
            response = await self.llm.ainvoke(messages)
            return self._clean_code_response(response.content)
            
        except Exception as e:
            print(f"Error generating main app: {e}")
            return self._get_fallback_main_app(app_name, app_category)
    
    def _get_category_features(self, category: str) -> str:
        """
        Get specific features and components based on app category
        """
        category_features = {
            "digital_product": """
            - Product catalog with images and descriptions
            - Shopping cart functionality (simulated)
            - Product comparison tool
            - Customer reviews and ratings display
            - Price filtering and search
            """,
            "finance": """
            - Financial dashboard with key metrics
            - Interactive charts (line, bar, pie charts)
            - Budget tracking and expense categorization
            - Portfolio analysis with sample data
            - Financial calculators (compound interest, loan calculator)
            """,
            "services": """
            - Service listings with descriptions
            - Booking calendar interface
            - Service provider profiles
            - Customer feedback system
            - Pricing calculator for different services
            """,
            "healthcare": """
            - Health metrics tracking dashboard
            - Appointment scheduling interface
            - Medical history tracker
            - Health progress visualizations
            - BMI calculator and health tips
            """,
            "education": """
            - Course catalog and descriptions
            - Progress tracking dashboard
            - Interactive quizzes or assessments
            - Learning analytics and charts
            - Study planner and calendar
            """,
            "entertainment": """
            - Content recommendation engine
            - Media library browser
            - User rating and review system
            - Trending content dashboard
            - Personalized content feed
            """,
            "travel": """
            - Destination search and filtering
            - Travel itinerary planner
            - Budget calculator for trips
            - Photo gallery of destinations
            - Travel booking interface (simulated)
            """,
            "food": """
            - Recipe browser and search
            - Meal planning calendar
            - Nutrition calculator
            - Restaurant finder and reviews
            - Cooking timer and converter tools
            """,
            "technology": """
            - Tech product showcase
            - Feature comparison matrices
            - Performance benchmarks and charts
            - Technical specifications display
            - Product recommendation system
            """,
            "automotive": """
            - Vehicle database and search
            - Maintenance tracking system
            - Fuel efficiency calculator
            - Vehicle comparison tool
            - Service scheduling interface
            """
        }
        
        return category_features.get(category.lower(), """
        - Interactive dashboard with key metrics
        - Data visualization and charts
        - User input forms and calculations
        - Search and filtering capabilities
        - Progress tracking and analytics
        """)
    
    async def _generate_additional_pages(self, app_idea: Dict[str, Any], complexity: str) -> Dict[str, str]:
        """
        Generate additional pages for medium/complex apps
        """
        additional_files = {}
        app_category = app_idea.get("category", "productivity")
        
        try:
            if complexity == "medium":
                # Add analytics page
                additional_files["pages/Analytics.py"] = await self._generate_analytics_page(app_idea)
                
            elif complexity == "complex":
                # Add multiple pages
                additional_files["pages/Analytics.py"] = await self._generate_analytics_page(app_idea)
                additional_files["pages/Settings.py"] = await self._generate_settings_page(app_idea)
                additional_files["pages/Profile.py"] = await self._generate_profile_page(app_idea)
            
            return additional_files
            
        except Exception as e:
            print(f"Error generating additional pages: {e}")
            return {}
    
    async def _generate_analytics_page(self, app_idea: Dict[str, Any]) -> str:
        """
        Generate an analytics page
        """
        try:
            app_category = app_idea.get("category", "productivity")
            app_name = app_idea.get("name", "MyApp")
            
            system_prompt = f"""
            Generate a Streamlit analytics page for a {app_category} application called {app_name}.
            
            Include:
            1. Various chart types (line, bar, pie, area charts)
            2. Key performance indicators (KPIs)
            3. Interactive filters and date ranges
            4. Metrics cards with delta values
            5. Sample data appropriate for {app_category}
            6. Proper page configuration
            
            Use modern Streamlit components and make it visually appealing.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Create analytics page for {app_name}")
            ]
            
            response = await self.llm.ainvoke(messages)
            return self._clean_code_response(response.content)
            
        except Exception as e:
            print(f"Error generating analytics page: {e}")
            return self._get_fallback_analytics_page()
    
    async def _generate_settings_page(self, app_idea: Dict[str, Any]) -> str:
        """
        Generate a settings page
        """
        return """
import streamlit as st

st.set_page_config(page_title="Settings", page_icon="⚙️")

st.title("Settings")

st.sidebar.success("Navigate between pages using the sidebar.")

# App Settings
st.header("Application Settings")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Display")
    theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
    language = st.selectbox("Language", ["English", "Spanish", "French"])
    
with col2:
    st.subheader("Notifications")
    email_notifications = st.checkbox("Email Notifications", value=True)
    push_notifications = st.checkbox("Push Notifications", value=False)

# Data Settings
st.header("Data & Privacy")
data_retention = st.slider("Data Retention (days)", 30, 365, 90)
analytics_consent = st.checkbox("Allow Analytics", value=True)

# Export/Import
st.header("Data Management")
if st.button("Export Data"):
    st.success("Data exported successfully!")

if st.button("Reset Settings"):
    st.warning("Settings have been reset to defaults.")

st.info("Settings are automatically saved.")
"""
    
    async def _generate_profile_page(self, app_idea: Dict[str, Any]) -> str:
        """
        Generate a profile page
        """
        return """
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Profile", page_icon="👤")

st.title("User Profile")

st.sidebar.success("Navigate between pages using the sidebar.")

# Profile Information
col1, col2 = st.columns([1, 2])

with col1:
    st.image("https://via.placeholder.com/150", caption="Profile Picture")
    if st.button("Change Picture"):
        st.info("Picture upload functionality would go here")

with col2:
    st.subheader("Personal Information")
    
    name = st.text_input("Full Name", value="John Doe")
    email = st.text_input("Email", value="john.doe@example.com")
    phone = st.text_input("Phone", value="+1 (555) 123-4567")
    bio = st.text_area("Bio", value="Welcome to my profile!")

# Activity Summary
st.header("Activity Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Sessions", "47", "+5")
with col2:
    st.metric("Time Spent", "23.5h", "+2.1h")
with col3:
    st.metric("Projects", "12", "+1")
with col4:
    st.metric("Achievements", "8", "+1")

# Recent Activity
st.header("Recent Activity")

activity_data = {
    "Date": ["2024-01-15", "2024-01-14", "2024-01-13"],
    "Activity": ["Created new project", "Updated profile", "Completed tutorial"],
    "Duration": ["45 min", "10 min", "30 min"]
}

st.dataframe(pd.DataFrame(activity_data), use_container_width=True)

if st.button("Save Profile"):
    st.success("Profile updated successfully!")
"""
    
    async def _generate_utils(self, app_category: str, complexity: str) -> Dict[str, str]:
        """
        Generate utility functions
        """
        utils = {}
        
        if complexity in ["medium", "complex"]:
            utils["utils/helpers.py"] = """
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

@st.cache_data
def load_sample_data():
    \"\"\"Load sample data for the application\"\"\"
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    data = {
        'date': dates,
        'value': np.random.randint(10, 100, 100),
        'category': np.random.choice(['A', 'B', 'C'], 100),
        'score': np.random.uniform(0, 1, 100)
    }
    return pd.DataFrame(data)

def format_number(num):
    \"\"\"Format numbers for display\"\"\"
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def calculate_growth(current, previous):
    \"\"\"Calculate growth percentage\"\"\"
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100
"""
        
        return utils
    
    def _generate_requirements(self, app_category: str, complexity: str) -> str:
        """
        Generate requirements.txt based on app needs
        """
        base_requirements = [
            "streamlit>=1.28.0",
            "pandas>=1.5.0",
            "numpy>=1.24.0",
            "plotly>=5.15.0"
        ]
        
        category_requirements = {
            "finance": ["yfinance", "scipy"],
            "healthcare": ["scikit-learn", "matplotlib"],
            "education": ["matplotlib", "seaborn"],
            "entertainment": ["requests", "beautifulsoup4"],
            "travel": ["folium", "geopy"],
            "food": ["requests", "pillow"]
        }
        
        if complexity == "complex":
            base_requirements.extend(["sqlalchemy", "pymongo", "redis"])
        
        all_requirements = base_requirements + category_requirements.get(app_category, [])
        return "\n".join(all_requirements)
    
    def _generate_development_notes(self, app_idea: Dict[str, Any], project_files: Dict[str, str]) -> List[str]:
        """
        Generate development notes and recommendations
        """
        notes = [
            f"Generated Streamlit app for {app_idea.get('name', 'your app')}",
            f"App Category: {app_idea.get('category', 'general')}",
            f"Generated {len(project_files)} files",
            "Run 'pip install -r requirements.txt' to install dependencies",
            "Run 'streamlit run app.py' to start the app",
            "App will open in your browser at http://localhost:8501",
            "Customize the app by editing app.py",
            "Add your own data sources and APIs"
        ]
        
        return notes
    
    def _suggest_next_steps(self, app_category: str, complexity: str) -> List[str]:
        """
        Suggest next development steps
        """
        base_steps = [
            "1. Test the app locally with 'streamlit run app.py'",
            "2. Customize the UI colors and themes",
            "3. Replace sample data with real data sources",
            "4. Add authentication if needed"
        ]
        
        category_steps = {
            "finance": ["5. Connect to financial APIs", "6. Add real-time data updates"],
            "healthcare": ["5. Ensure data privacy compliance", "6. Add data validation"],
            "education": ["5. Add user progress tracking", "6. Implement content management"],
            "entertainment": ["5. Add content recommendation", "6. Implement user ratings"]
        }
        
        steps = base_steps + category_steps.get(app_category, ["5. Add app-specific features"])
        
        if complexity == "complex":
            steps.append("7. Deploy to Streamlit Cloud or Heroku")
            steps.append("8. Add database integration")
        
        return steps
    
    def _clean_code_response(self, code: str) -> str:
        """Clean the code response from the LLM"""
        code = re.sub(r'```python\n?', '', code)
        code = re.sub(r'```\n?', '', code)
        return code.strip()
    
    def _get_fallback_main_app(self, app_name: str, app_category: str) -> str:
        """Fallback main app if generation fails"""
        return f"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="{app_name}",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("{app_name}")
st.markdown("**{app_category.title()} Application**")

# Sidebar
st.sidebar.header("Navigation")
st.sidebar.success("Welcome to {app_name}!")

# Main content
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Users", "1,234", "+12%")
with col2:
    st.metric("Active Sessions", "567", "+5%")
with col3:
    st.metric("Revenue", "$12,345", "+8%")

# Sample chart
st.header("Analytics Dashboard")
sample_data = pd.DataFrame({{
    'Date': pd.date_range('2024-01-01', periods=30),
    'Value': np.random.randint(10, 100, 30)
}})

fig = px.line(sample_data, x='Date', y='Value', title='Sample Data Trend')
st.plotly_chart(fig, use_container_width=True)

# Interactive section
st.header("Interactive Features")
user_input = st.text_input("Enter your input:")
if user_input:
    st.success(f"You entered: {{user_input}}")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit | Generated by Steve Connect")
"""
    
    def _get_fallback_analytics_page(self) -> str:
        """Fallback analytics page"""
        return """
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Analytics", page_icon="📊")

st.title("Analytics Dashboard")

# Sample data
data = pd.DataFrame({
    'Date': pd.date_range('2024-01-01', periods=30),
    'Sales': np.random.randint(100, 1000, 30),
    'Users': np.random.randint(50, 500, 30)
})

# Charts
col1, col2 = st.columns(2)

with col1:
    fig1 = px.line(data, x='Date', y='Sales', title='Sales Trend')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(data, x='Date', y='Users', title='User Growth')
    st.plotly_chart(fig2, use_container_width=True)
"""
    
    def _generate_readme(self, app_name: str, app_description: str) -> str:
        """Generate README.md for the project"""
        return f"""
# {app_name}

{app_description}

## Getting Started

This is a Streamlit application generated by Steve Connect.

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation
1. Clone or download this project
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`
4. Open your browser to http://localhost:8501

### Features
- Interactive web interface
- Real-time data visualization
- Modern UI components
- Responsive design

## Generated by Steve Connect
This app was automatically generated based on your idea. Customize it to fit your specific needs!

## Deployment
Deploy to Streamlit Cloud:
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy with one click!
"""
    
    def _analyze_app_structure(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze the generated app structure"""
        return {
            "total_files": len(project_files),
            "python_files": len([f for f in project_files.keys() if f.endswith('.py')]),
            "pages": len([f for f in project_files.keys() if 'pages/' in f]),
            "utils": len([f for f in project_files.keys() if 'utils/' in f]),
            "has_requirements": "requirements.txt" in project_files,
            "has_readme": "README.md" in project_files
        }