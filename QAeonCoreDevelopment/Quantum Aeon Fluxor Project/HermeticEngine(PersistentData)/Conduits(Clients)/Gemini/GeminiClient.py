# Quantum Aeon Core/Hermetic Engine (Persistent Data)/Conduits/GeminiClient.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiClient:
    """
    A dedicated client for interacting with the Google Gemini API.

    This class handles the configuration, API key management, and the
    logic for sending prompts to the Gemini models. It is designed to be
    a singleton or a shared instance to avoid repeated configuration.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GeminiClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # We only run configuration once.
        if hasattr(self, '_configured') and self._configured:
            return
        
        print("--- Configuring Gemini Client ---")
        load_dotenv() # Loads environment variables from a .env file
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file. Please ensure it is set.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro') # As per your directive
        self._configured = True
        print("--- Gemini Client Configured Successfully ---")

    def query(self, prompt: str) -> str:
        """
        Sends a query to the configured Gemini model.

        Args:
            prompt (str): The prompt to send to the language model.

        Returns:
            str: The text content of the model's response.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Basic error handling. In a production system, this would be more robust.
            print(f"An error occurred while querying Gemini: {e}")
            return f"Error: Could not get a response from the model. Details: {e}"

# --- Example Usage ---
if __name__ == "__main__":
    # To test this file directly:
    # 1. Make sure you have a .env file in the root of your project.
    # 2. The .env file should contain: GOOGLE_API_KEY='your_api_key_here'
    # 3. Make sure you have the necessary libraries:
    #    pip install google-generativeai python-dotenv
    
    print("Testing the GeminiClient...")
    client = GeminiClient()
    test_prompt = "In one sentence, what is the purpose of a good LLM client class?"
    response_text = client.query(test_prompt)
    
    print(f"\nTest Prompt: {test_prompt}")
    print(f"Gemini's Response: {response_text}")