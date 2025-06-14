# src/agents/leonardo_agent.py - Updated with much better prompts and models
"""
Leonardo Agent - AI Image Generation for Steve Connect
Updated with better prompts for specific, relevant images
"""

import os
import base64
import io
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

class LeonardoAgent:
    """
    AI image generation with much better, specific prompts
    """
    
    def __init__(self):
        self.hf_client = InferenceClient(
            token=os.getenv("HUGGINGFACE_API_KEY")
        )
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.7,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        # Better models for realistic images
        self.models = [
            "stabilityai/stable-diffusion-xl-base-1.0",
            "runwayml/stable-diffusion-v1-5",
            "SG161222/Realistic_Vision_V3.0_VAE"
        ]
    
    async def generate_marketing_image(self, 
                                     idea_context: Dict[str, Any], 
                                     user_prompt: str = "",
                                     image_type: str = "marketing") -> Dict[str, Any]:
        """
        Generate much better, specific images based on the app idea
        """
        try:
            app_category = idea_context.get("category", "technology")
            app_name = idea_context.get("name", "fitness tracker")
            app_description = idea_context.get("description", "")
            
            print(f"🎨 Generating specific {image_type} image for {app_name}")
            
            # Create much better, specific prompts
            enhanced_prompt = await self._create_smart_prompt(
                app_name, app_category, app_description, user_prompt, image_type
            )
            
            print(f"🖼️ Using enhanced prompt: {enhanced_prompt}")
            
            # Try generating with the enhanced prompt
            for model in self.models:
                try:
                    image = self.hf_client.text_to_image(
                        prompt=enhanced_prompt,
                        model=model
                    )
                    
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    image_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    return {
                        "success": True,
                        "image_data": image_base64,
                        "prompt_used": enhanced_prompt,
                        "model_used": model,
                        "image_type": image_type,
                        "metadata": idea_context
                    }
                    
                except Exception as e:
                    print(f"⚠️ Model {model} failed: {e}")
                    continue
            
            # If all AI models fail, create a much better designed image
            return self._create_realistic_mockup(app_name, app_category, app_description)
            
        except Exception as e:
            print(f"❌ Error generating image: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_smart_prompt(self, app_name: str, category: str, description: str, user_prompt: str, image_type: str) -> str:
        """
        Use AI to create much better, specific prompts
        """
        try:
            system_prompt = f"""
            Create a detailed, specific image prompt for a {image_type} image.
            
            App Details:
            - Name: {app_name}
            - Category: {category}
            - Description: {description}
            - User request: {user_prompt}
            
            Create a prompt that will generate a realistic, professional image showing:
            
            For FITNESS/HEALTHCARE apps:
            - Person using/wearing the fitness device
            - Modern gym or outdoor setting
            - Professional product photography style
            - Show the actual app interface on a phone/watch
            
            For FINANCE apps:
            - Professional business setting
            - Person using financial app on phone/laptop
            - Charts, graphs, financial elements
            - Modern office environment
            
            For EDUCATION apps:
            - Students using the app
            - Learning environment
            - Educational materials visible
            
            For ENTERTAINMENT apps:
            - People enjoying the app
            - Fun, engaging environment
            - Show app interface being used
            
            Make the prompt very specific about:
            - What people are doing
            - What devices/screens show
            - The environment/setting
            - Professional photography style
            - Realistic, not cartoon
            
            Return only the detailed prompt, nothing else.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Create specific prompt for {app_name} {category} app")
            ]
            
            response = await self.llm.ainvoke(messages)
            enhanced_prompt = response.content.strip()
            
            # Add quality enhancers
            quality_terms = ", professional photography, high resolution, realistic, detailed, modern"
            final_prompt = enhanced_prompt + quality_terms
            
            return final_prompt
            
        except Exception as e:
            print(f"Error creating smart prompt: {e}")
            # Fallback to category-specific prompts
            return self._get_category_specific_prompt(app_name, category, description)
    
    def _get_category_specific_prompt(self, app_name: str, category: str, description: str) -> str:
        """
        Fallback category-specific prompts that are much more detailed
        """
        prompts = {
            "healthcare": f"young athletic person wearing smartwatch fitness tracker, checking heart rate and calories on phone app, modern gym background, professional product photography, realistic detailed, smartphone screen showing {app_name} fitness app interface with charts and data",
            
            "finance": f"professional business person using {app_name} financial app on smartphone, modern office setting, charts and graphs visible on phone screen, budget tracking interface, clean professional photography, realistic detailed",
            
            "education": f"students using {app_name} learning app on tablet, modern classroom or library setting, educational interface visible on screen, people engaged in learning, professional photography, realistic detailed",
            
            "entertainment": f"people enjoying {app_name} entertainment app on phones, fun social setting, app interface visible on screens, engaged users, modern professional photography, realistic detailed",
            
            "travel": f"traveler using {app_name} travel app on phone, airport or destination background, map and travel booking interface on screen, professional travel photography, realistic detailed",
            
            "food": f"person using {app_name} food app in kitchen or restaurant, recipe or food delivery interface on phone screen, appetizing food visible, professional food photography, realistic detailed",
            
            "technology": f"tech professional using {app_name} app on modern devices, clean tech office environment, app interface clearly visible on screens, professional tech photography, realistic detailed"
        }
        
        return prompts.get(category, f"person using {app_name} mobile app on smartphone, modern professional setting, app interface visible on screen, professional photography, realistic detailed") + ", high quality, professional, modern design"
    
    def _create_realistic_mockup(self, app_name: str, category: str, description: str) -> Dict[str, Any]:
        """
        Create a realistic app mockup when AI generation fails
        """
        try:
            # Create a more realistic mockup showing actual app interface
            img = Image.new('RGB', (512, 512), color='#f8f9fa')
            draw = ImageDraw.Draw(img)
            
            # Draw phone mockup
            phone_width = 200
            phone_height = 350
            phone_x = (512 - phone_width) // 2
            phone_y = 80
            
            # Phone body
            draw.rounded_rectangle(
                [phone_x, phone_y, phone_x + phone_width, phone_y + phone_height],
                radius=25,
                fill='#2c3e50',
                outline='#34495e',
                width=3
            )
            
            # Screen
            screen_margin = 15
            draw.rounded_rectangle(
                [phone_x + screen_margin, phone_y + screen_margin, 
                 phone_x + phone_width - screen_margin, phone_y + phone_height - screen_margin],
                radius=15,
                fill='white'
            )
            
            # Category-specific UI elements
            if category == "healthcare":
                # Fitness app UI
                draw.text((phone_x + 30, phone_y + 40), app_name, fill='#2c3e50')
                draw.text((phone_x + 30, phone_y + 70), "💓 Heart Rate: 75 BPM", fill='#e74c3c')
                draw.text((phone_x + 30, phone_y + 100), "🔥 Calories: 1,247", fill='#f39c12')
                draw.text((phone_x + 30, phone_y + 130), "👟 Steps: 8,432", fill='#27ae60')
                
                # Progress bars
                draw.rectangle([phone_x + 30, phone_y + 160, phone_x + 150, phone_y + 170], fill='#3498db')
                draw.rectangle([phone_x + 30, phone_y + 180, phone_x + 120, phone_y + 190], fill='#e74c3c')
                
            elif category == "finance":
                draw.text((phone_x + 30, phone_y + 40), app_name, fill='#2c3e50')
                draw.text((phone_x + 30, phone_y + 70), "💰 Balance: $2,847", fill='#27ae60')
                draw.text((phone_x + 30, phone_y + 100), "📊 Spending: $439", fill='#e74c3c')
                draw.text((phone_x + 30, phone_y + 130), "💳 Budget: 67%", fill='#f39c12')
                
                # Chart mockup
                draw.rectangle([phone_x + 30, phone_y + 160, phone_x + 170, phone_y + 220], outline='#bdc3c7')
                draw.line([phone_x + 40, phone_y + 200, phone_x + 80, phone_y + 180, phone_x + 120, phone_y + 170, phone_x + 160, phone_y + 185], fill='#3498db', width=2)
            
            # Add background elements
            draw.text((50, 450), f"Professional {category} app mockup", fill='#7f8c8d')
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "image_data": image_base64,
                "prompt_used": f"Professional {category} app mockup for {app_name}",
                "model_used": "realistic_mockup",
                "image_type": "app_mockup"
            }
            
        except Exception as e:
            print(f"Mockup creation failed: {e}")
            return {"success": False, "error": str(e)}