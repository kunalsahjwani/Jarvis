# # test_streamlit_generation.py - Test actual Streamlit code
# """
# Test your model for Streamlit code generation specifically
# """

# from transformers import AutoTokenizer, AutoModelForCausalLM
# from peft import PeftModel
# import torch

# def test_streamlit_code():
#     """Test Streamlit-specific code generation"""
    
#     print("Testing Streamlit code generation...")
    
#     try:
#         # Load your model (we know this works now)
#         tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-1.5B-Instruct")
#         if tokenizer.pad_token is None:
#             tokenizer.pad_token = tokenizer.eos_token
            
#         base_model = AutoModelForCausalLM.from_pretrained(
#             "Qwen/Qwen2.5-Coder-1.5B-Instruct",
#             torch_dtype=torch.float32
#         )
        
#         model = PeftModel.from_pretrained(base_model, "kunalsahjwani/qwen-streamlit-coder")
#         print("Your fine-tuned model loaded!")
        
#         # Test Streamlit-specific prompt
#         prompt = """Create a Streamlit app for expense tracking:

# ```python
# import streamlit as st
# import pandas as pd

# st.title("Expense Tracker")
# st.sidebar.header("Add New Expense")

# # Input form"""
        
#         inputs = tokenizer(prompt, return_tensors="pt")
        
#         print("Generating Streamlit code (30-60 seconds on CPU)...")
        
#         with torch.no_grad():
#             output = model.generate(
#                 **inputs,
#                 max_new_tokens=150,  # Reasonable length
#                 temperature=0.3,     # Slightly creative
#                 do_sample=True,
#                 pad_token_id=tokenizer.eos_token_id
#             )
        
#         response = tokenizer.decode(output[0], skip_special_tokens=True)
#         generated_part = response[len(prompt):]
        
#         print("Streamlit code generated!")
#         print("\n" + "="*50)
#         print("YOUR FINE-TUNED MODEL OUTPUT:")
#         print("="*50)
#         print(response)
#         print("="*50)
        
#         # Save to file for testing
#         with open("generated_app.py", "w") as f:
#             f.write(response)
#         print("\nCode saved to 'generated_app.py'")
#         print("Test it with: streamlit run generated_app.py")
        
#         return True
        
#     except Exception as e:
#         print(f"Error: {e}")
#         return False

# if __name__ == "__main__":
#     test_streamlit_code()