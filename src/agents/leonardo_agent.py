# src/agents/leonardo_agent.py - Enhanced with workflow integration and fixed image decoding
"""
Leonardo Agent - AI Image Generation for Steve Connect
Enhanced with better prompts and workflow integration
Fixed UTF-8 decoding error for image data
"""

import os
import base64
from typing import Dict, Any
from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

class LeonardoAgent:
   """
   AI image generation with workflow-aware prompts
   """
   
   def __init__(self):
       # Keep the working Google Gemini client
       api_key = os.getenv("GOOGLE_API_KEY")
       self.client = genai.Client(api_key=api_key)
       
       # Add LLM for smart prompt generation
       self.llm = ChatGoogleGenerativeAI(
           model="gemini-2.0-flash",
           temperature=0.7,
           google_api_key=os.getenv("GOOGLE_API_KEY"),
           convert_system_message_to_human=True
       )
       
       print("Leonardo Agent initialized with workflow integration")
   
   async def generate_marketing_image(self, 
                                    idea_context: Dict[str, Any], 
                                    user_prompt: str = "",
                                    image_type: str = "marketing") -> Dict[str, Any]:
       """
       Generate enhanced images based on app workflow context
       """
       try:
           app_category = idea_context.get("category", "technology")
           app_name = idea_context.get("name", "App")
           app_description = idea_context.get("description", "")
           
           print(f"🎨 Generating specific {image_type} image for {app_name}")
           
           # Create much better, specific prompts
           enhanced_prompt = await self._create_smart_prompt(
               app_name, app_category, app_description, user_prompt, image_type
           )
           
           print(f"🖼️ Using enhanced prompt: {enhanced_prompt}")
           
           response = self.client.models.generate_content(
               model="gemini-2.0-flash-preview-image-generation",
               contents=enhanced_prompt,
               config=types.GenerateContentConfig(
                   response_modalities=['TEXT', 'IMAGE']
               )
           )
           
           # Extract image - FIXED method
           for part in response.candidates[0].content.parts:
               if part.inline_data is not None:
                   # CORRECT: Convert raw bytes to base64 string
                   image_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                   
                   print(f"✅ Image generated successfully")
                   print(f"Base64 length: {len(image_base64)} characters")
                   
                   return {
                       "success": True,
                       "image_data": image_base64,
                       "prompt_used": enhanced_prompt,
                       "model_used": "gemini-2.0-flash-preview-image-generation",
                       "image_type": image_type,
                       "metadata": idea_context
                   }
           
           return {"success": False, "error": "No image generated"}
           
       except Exception as e:
           print(f"❌ Error generating image: {e}")
           return {"success": False, "error": str(e)}
   
   async def _create_smart_prompt(self, app_name: str, category: str, description: str, user_prompt: str, image_type: str) -> str:
       """
       Use AI to create much better, specific prompts
       """
       try:
           # SPECIAL CASE: If it's a logo, create logo-specific prompt
           if image_type.lower() == "logo":
               logo_prompt = f"""
               Create a modern, professional logo design for an app called "{app_name}" in the {category} category.
               
               Description: {description}
               
               Logo should be:
               - Clean, minimalist design
               - Modern and professional
               - Suitable for app icon
               - Simple geometric shapes or typography
               - Clear and recognizable
               - {category}-themed colors and elements
               - No people, just the logo design itself
               
               Style: flat design, vector-style, clean typography, professional branding
               """
               return logo_prompt + ", high quality logo design, app icon style, vector graphics"
           
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
           return self._get_category_specific_prompt(app_name, category, description, user_prompt, image_type)
   
   def _get_category_specific_prompt(self, app_name: str, category: str, description: str, user_prompt: str, image_type: str) -> str:
       """
       Fallback category-specific prompts that are much more detailed
       """
       # SPECIAL CASE: Logo fallback
       if image_type.lower() == "logo":
           return f"Modern minimalist logo design for {app_name} {category} app, clean vector graphics, professional branding, app icon style, simple geometric design"
       
       # Use user prompt if provided
       base_prompt = user_prompt if user_prompt else f"Create a {category} image"
       
       prompts = {
           "healthcare": f"young athletic person wearing smartwatch fitness tracker, checking heart rate and calories on phone app, modern gym background, professional product photography, realistic detailed, smartphone screen showing {app_name} fitness app interface with charts and data",
           
           "finance": f"professional business person using {app_name} financial app on smartphone, modern office setting, charts and graphs visible on phone screen, budget tracking interface, clean professional photography, realistic detailed",
           
           "education": f"students using {app_name} learning app on tablet, modern classroom or library setting, educational interface visible on screen, people engaged in learning, professional photography, realistic detailed",
           
           "entertainment": f"people enjoying {app_name} entertainment app on phones, fun social setting, app interface visible on screens, engaged users, modern professional photography, realistic detailed",
           
           "travel": f"traveler using {app_name} travel app on phone, airport or destination background, map and travel booking interface on screen, professional travel photography, realistic detailed",
           
           "food": f"person using {app_name} food app in kitchen or restaurant, recipe or food delivery interface on phone screen, appetizing food visible, professional food photography, realistic detailed",
           
           "technology": f"tech professional using {app_name} app on modern devices, clean tech office environment, app interface clearly visible on screens, professional tech photography, realistic detailed"
       }
       
       category_prompt = prompts.get(category, base_prompt)
       return category_prompt + ", high quality, professional, modern design"