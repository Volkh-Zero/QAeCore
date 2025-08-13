"""Run this model in Python

> pip install mistralai

This script provides an interactive chat session with a Mistral model
hosted on GitHub's inference service. It maintains conversation history
for context-aware interactions.
"""
import os
import sys
import importlib.util
from mistralai import Mistral, UserMessage, AssistantMessage

# Import base_agent using importlib to handle special characters in path
base_agent_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Go up two levels to Moirai(CustomAgents)
    "base_agent.py"
)

try:
    spec = importlib.util.spec_from_file_location("base_agent", base_agent_path)
    base_agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base_agent)
    BaseAgent = base_agent.BaseAgent
except (ImportError, FileNotFoundError) as e:
    print(f"Error loading base_agent: {e}")
    raise

# --- Configuration ---
SERVER_URL = "https://models.github.ai/inference"
DEFAULT_MODEL = "mistral-ai/Codestral-2501"
DEFAULT_TEMPERATURE = 0.8
DEFAULT_TOP_P = 0.1
# ---------------------

def get_GH_TOKEN():
    """
    Retrieves the GitHub token from the environment variables.
    Exits the script with an error message if the token is not found.
    """
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("Error: The 'GH_TOKEN' environment variable is not set.", file=sys.stderr)
        print("Please create a Personal Access Token (PAT) on GitHub and set it.", file=sys.stderr)
        sys.exit(1)
    return token

class MistralAgent(BaseAgent):
    def __init__(self):
        super().__init__("Mistral")
        self.client = self._initialize_client()

    def _initialize_client(self):
        api_key = get_GH_TOKEN()
        try:
            return Mistral(
                server_url=SERVER_URL,
                api_key=api_key,
            )
        except Exception as e:
            print(f"Error creating Mistral client: {e}", file=sys.stderr)
            sys.exit(1)

    def chat(self):
        print(f"Starting interactive chat with model: {DEFAULT_MODEL}")
        print("Type 'quit' or 'exit' to end the session (or press Ctrl+C).")
        print("-" * 20)

        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    print("Exiting chat.")
                    break
                
                if not user_input:
                    continue

                self.add_to_history(user_input, None)

                api_messages = []
                for msg in self.chat_history:
                    if msg.get("user"):
                        api_messages.append(UserMessage(content=msg["user"]))
                    if msg.get("bot"):
                        api_messages.append(AssistantMessage(content=msg["bot"]))

                response = self.client.chat.complete(
                    model=DEFAULT_MODEL,
                    messages=api_messages,
                    temperature=DEFAULT_TEMPERATURE,
                    top_p=DEFAULT_TOP_P,
                )

                if response.choices and len(response.choices) > 0:
                    assistant_response = response.choices[0].message
                    print(f"Assistant: {assistant_response.content}")
                    self.chat_history[-1]['bot'] = assistant_response.content
                    self.save_chat_history()
                else:
                    print("Error: No response received from the model.", file=sys.stderr)
                    if self.chat_history:
                        self.chat_history.pop()

            except Exception as e:
                if "mistral" in str(e).lower() or "api" in str(e).lower():
                    print(f"\nMistral API error: {e}", file=sys.stderr)
                else:
                    print(f"\nUnexpected error: {e}", file=sys.stderr)
                if self.chat_history:
                    self.chat_history.pop()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting chat.")
                break

def main():
    """
    Main function to run the interactive chat client.
    """
    agent = MistralAgent()
    agent.chat()

if __name__ == "__main__":
    main()
