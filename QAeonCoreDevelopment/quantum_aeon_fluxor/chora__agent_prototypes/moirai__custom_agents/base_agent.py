import json
import os
import re
from pathlib import Path

class BaseAgent:
    def __init__(self, agent_name):
        # Sanitize agent_name to remove invalid filename characters
        safe_agent_name = re.sub(r'[<>:"/\\|?*]', '_', agent_name)
        self.agent_name = safe_agent_name
        
        # Create chat_histories directory in the same directory as the agent script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.chat_histories_dir = os.path.join(script_dir, "chat_histories")
        os.makedirs(self.chat_histories_dir, exist_ok=True)
        
        self.chat_history_path = os.path.join(self.chat_histories_dir, f"{self.agent_name}_history.json")
        self.chat_history = []
        self.load_chat_history()
    
    def load_chat_history(self):
        """Load chat history from JSON file if it exists."""
        try:
            if os.path.exists(self.chat_history_path):
                with open(self.chat_history_path, "r") as f:
                    self.chat_history = json.load(f)
                print(f"Loaded chat history from {self.chat_history_path}")
            else:
                self.chat_history = []
        except (IOError, PermissionError) as e:
            print(f"Error reading chat history file: {e}")
            self.chat_history = []
        except json.JSONDecodeError as e:
            print(f"Error decoding chat history JSON: {e}")
            self.chat_history = []
    
    def save_chat_history(self):
        """Save current chat history to JSON file."""
        try:
            with open(self.chat_history_path, "w") as f:
                json.dump(self.chat_history, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Error saving chat history: {e}")
    
    def add_to_history(self, user_message, bot_response):
        """Add a message exchange to the chat history and save it."""
        if user_message is not None:
            self.chat_history.append({"user": user_message, "bot": bot_response})
            self.save_chat_history()
