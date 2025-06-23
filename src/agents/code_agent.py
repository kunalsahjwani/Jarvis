# To use the fine tuned model, just uncomment the fine tuned model code below. I have finetuned Qwen 2.5 coder for generating streamlit code

"""
Code Generation Agent with dual strategy:
1. Primary: Google Gemini (fast, reliable)
2. Fallback: Your fine-tuned model (specialized) - Currently commented out
3. Fail cleanly if both fail
4. SIMPLIFIED: Always generates simple, focused apps
"""

import os
import re
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
# from transformers import AutoTokenizer, AutoModelForCausalLM  # Commented out - uncomment to use fine-tuned model
# from peft import PeftModel  # Commented out - uncomment to use fine-tuned model
# import torch  # Commented out - uncomment to use fine-tuned model
from dotenv import load_dotenv

load_dotenv()

class CodeAgent:
    """
    AI agent with Gemini primary + fine-tuned model fallback
    Always generates simple, focused Streamlit apps
    """
    
    def __init__(self):
        print("🤖 Initializing Code Agent with dual strategy...")
        
        # Initialize Gemini (primary)
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.2,
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                convert_system_message_to_human=True
            )
            print("✅ Gemini initialized (primary)")
            self.gemini_available = True
        except Exception as e:
            print(f"⚠️ Gemini initialization failed: {e}")
            self.gemini_available = False
        
        # Initialize your fine-tuned model (fallback) - COMMENTED OUT FOR GPU REASONS
        # Uncomment the code below to enable fine-tuned model fallback
        self.finetuned_model = None
        self.finetuned_tokenizer = None
        self.finetuned_available = False  # Set to False when commented out
        
        # try:
        #     print("🔧 Loading your fine-tuned model (fallback)...")
        #     self.finetuned_tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-1.5B-Instruct")
        #     if self.finetuned_tokenizer.pad_token is None:
        #         self.finetuned_tokenizer.pad_token = self.finetuned_tokenizer.eos_token
        #         
        #     base_model = AutoModelForCausalLM.from_pretrained(
        #         "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        #         torch_dtype=torch.float32
        #     )
        #     
        #     self.finetuned_model = PeftModel.from_pretrained(base_model, "kunalsahjwani/qwen-streamlit-coder")
        #     print("✅ Your fine-tuned model loaded (fallback)")
        #     self.finetuned_available = True
        # except Exception as e:
        #     print(f"⚠️ Fine-tuned model loading failed: {e}")
        #     self.finetuned_available = False
        
        self.project_structure = {
            "app.py": "",
            "requirements.txt": "",
            "README.md": ""
        }
    
    async def generate_streamlit_app(self, 
                                   app_idea: Dict[str, Any], 
                                   user_requirements: str = "") -> Dict[str, Any]:
        """
        Generate simple, focused Streamlit app with fallback strategy
        """
        try:
            app_name = app_idea.get("name", "MyApp")
            app_category = app_idea.get("category", "productivity")
            app_description = app_idea.get("description", "A web application")
            
            print(f"💻 GENERATING: {app_name} ({app_category}) - Simple functionality")
            
            # Try Gemini first
            main_app = None
            model_used = None
            
            if self.gemini_available:
                try:
                    print("🚀 Trying Gemini (primary)...")
                    main_app = await self._generate_with_gemini(app_name, app_description, app_category, user_requirements)
                    model_used = "gemini-2.0-flash"
                    print("✅ Gemini generation successful!")
                except Exception as e:
                    print(f"⚠️ Gemini failed: {e}")
                    print("🔄 Falling back to your fine-tuned model...")
            
            # Fallback to your fine-tuned model
            if main_app is None and self.finetuned_available:
                try:
                    print("🤖 Using your fine-tuned model (fallback)...")
                    main_app = await self._generate_with_finetuned(app_name, app_description, app_category, user_requirements)
                    model_used = "kunalsahjwani/qwen-streamlit-coder"
                    print("✅ Fine-tuned model generation successful!")
                except Exception as e:
                    print(f"❌ Fine-tuned model also failed: {e}")
            
            # Fail cleanly if both models fail
            if main_app is None:
                print("❌ Both Gemini and fine-tuned model failed")
                return {
                    "success": False,
                    "error": "Both Gemini and fine-tuned model failed to generate code",
                    "app_name": app_name,
                    "gemini_available": self.gemini_available,
                    "finetuned_available": self.finetuned_available
                }
            
            # Simple project structure - no additional pages
            project_files = {
                "app.py": main_app,
                "requirements.txt": self._generate_requirements(app_category),
                "README.md": self._generate_readme(app_name, app_description, model_used)
            }
            
            return {
                "success": True,
                "app_name": app_name,
                "project_files": project_files,
                "app_structure": self._analyze_app_structure(project_files),
                "development_notes": self._generate_development_notes(app_idea, project_files, model_used),
                "next_steps": self._suggest_next_steps(app_category),
                "model_used": model_used,
                "run_command": "streamlit run app.py"
            }
            
        except Exception as e:
            print(f"Error generating app: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_with_gemini(self, app_name: str, app_description: str, app_category: str, requirements: str) -> str:
        """
        Generate using Gemini (primary method) - Simple apps only
        """
        category_features = self._get_category_features(app_category)
        
        system_prompt = f"""
        Generate a complete, simple Streamlit application (app.py) for a {app_category} application.
        
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
        
        IMPORTANT: Generate a single-page app with focused functionality.
        Make it clean, well-commented, and production-ready.
        Focus on core features rather than complexity.
        DO NOT include any emojis in the generated code - use plain text only.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create a simple, focused Streamlit app for {app_name}")
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_with_finetuned(self, app_name: str, app_description: str, app_category: str, requirements: str) -> str:
        """
        Generate using your fine-tuned model (fallback method) - COMMENTED OUT
        Uncomment this method to enable fine-tuned model generation
        """
        # COMMENTED OUT - Uncomment to use fine-tuned model
        # prompt = f"""Create a simple Streamlit app for {app_description} (NO EMOJIS in code):
        # 
        # ```python
        # import streamlit as st
        # import pandas as pd
        # 
        # st.title("{app_name}")
        # st.sidebar.header("Controls")
        # 
        # # App functionality"""
        # 
        # inputs = self.finetuned_tokenizer(prompt, return_tensors="pt")
        # 
        # with torch.no_grad():
        #     output = self.finetuned_model.generate(
        #         **inputs,
        #         max_new_tokens=400,
        #         temperature=0.3,
        #         do_sample=True,
        #         pad_token_id=self.finetuned_tokenizer.eos_token_id
        #     )
        # 
        # response = self.finetuned_tokenizer.decode(output[0], skip_special_tokens=True)
        # return response
        
        # Placeholder return when commented out
        raise Exception("Fine-tuned model is currently disabled. Uncomment the code above to enable it.")
    
    def _get_category_features(self, category: str) -> str:
        """Get simple, focused features based on app category"""
        features = {
            "finance": "- Financial dashboard with key metrics\n- Simple budget tracking\n- Basic financial calculator\n- Interactive charts",
            "healthcare": "- Health metrics display\n- Simple progress tracking\n- BMI calculator\n- Basic health visualizations",
            "education": "- Simple course browser\n- Basic progress tracking\n- Interactive quiz component\n- Learning dashboard",
            "entertainment": "- Content display interface\n- Simple rating system\n- Basic recommendations\n- User-friendly navigation",
            "travel": "- Destination browser\n- Simple trip information\n- Basic budget calculator\n- Photo gallery",
            "food": "- Recipe browser\n- Simple meal planner\n- Basic nutrition info\n- Cooking timer",
            "productivity": "- Task management interface\n- Simple progress tracking\n- Basic analytics\n- User-friendly dashboard"
        }
        
        return features.get(category.lower(), "- Simple interactive dashboard\n- Basic data visualization\n- User input forms\n- Core functionality")
    
    def _generate_requirements(self, app_category: str) -> str:
        """Generate simple requirements.txt based on app needs"""
        base_requirements = [
            "streamlit>=1.28.0",
            "pandas>=1.5.0",
            "numpy>=1.24.0",
            "plotly>=5.15.0"
        ]
        
        category_requirements = {
            "finance": ["yfinance"],
            "healthcare": ["scikit-learn"],
            "education": ["matplotlib"],
            "entertainment": ["requests"],
            "travel": ["folium"],
            "food": ["requests"]
        }
        
        all_requirements = base_requirements + category_requirements.get(app_category, [])
        return "\n".join(all_requirements)
    
    def _generate_development_notes(self, app_idea: Dict[str, Any], project_files: Dict[str, str], model_used: str) -> List[str]:
        """Generate development notes and recommendations"""
        notes = [
            f"✅ Generated by: {model_used}",
            f"📱 App: {app_idea.get('name', 'your app')} ({app_idea.get('category', 'general')})",
            f"📁 Files: {len(project_files)}",
            "🎯 Simple, focused functionality",
            "🔧 Run 'pip install -r requirements.txt' to install dependencies",
            "🚀 Run 'streamlit run app.py' to start the app",
            "🌐 App will open in your browser at http://localhost:8501",
            "💡 Customize the app by editing app.py",
            "📊 Add your own data sources and APIs"
        ]
        
        return notes
    
    def _suggest_next_steps(self, app_category: str) -> List[str]:
        """Suggest next development steps for simple apps"""
        base_steps = [
            "1. Test the app locally with 'streamlit run app.py'",
            "2. Customize the UI colors and themes",
            "3. Replace sample data with real data sources",
            "4. Add your own branding and styling"
        ]
        
        category_steps = {
            "finance": ["5. Connect to financial APIs", "6. Add real-time data updates"],
            "healthcare": ["5. Ensure data privacy compliance", "6. Add data validation"],
            "education": ["5. Add user progress tracking", "6. Implement content management"],
            "entertainment": ["5. Add content recommendation", "6. Implement user ratings"]
        }
        
        steps = base_steps + category_steps.get(app_category, ["5. Add category-specific features"])
        steps.append("6. Deploy to Streamlit Cloud")
        
        return steps
    
    def _generate_readme(self, app_name: str, app_description: str, model_used: str) -> str:
        """Generate README with model info"""
        return f"""# {app_name}

{app_description}

## Generated by Steve Connect
- **Primary Model**: Google Gemini 2.0 Flash
- **Fallback Model**: kunalsahjwani/qwen-streamlit-coder  
- **Model Used**: {model_used}
- **App Type**: Simple, focused functionality

## Installation
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features
- Simple, focused functionality
- Interactive web interface
- Real-time data visualization
- Modern UI components
- Responsive design

## Customization
- Edit app.py to modify functionality
- Update requirements.txt for additional dependencies
- Customize styling and themes
- Add your own data sources

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
            "app_type": "simple",
            "has_requirements": "requirements.txt" in project_files,
            "has_readme": "README.md" in project_files
        }