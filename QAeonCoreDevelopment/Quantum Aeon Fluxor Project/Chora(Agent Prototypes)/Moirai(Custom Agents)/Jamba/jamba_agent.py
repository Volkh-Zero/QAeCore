"""Run this model in Python

> pip install azure-ai-inference

This script provides an interactive chat session with a Jamba model
hosted on GitHub's inference service. It maintains conversation history
for context-aware interactions.
"""
import os
import sys
import importlib.util
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

# Import base_agent using importlib to handle special characters in path
base_agent_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Chora(AgentPrototypes)",
    "Moirai(CustomAgents)",
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
ENDPOINT = "https://models.github.ai/inference"
DEFAULT_MODEL = "ai21-labs/AI21-Jamba-1.5-Large"
DEFAULT_TEMPERATURE = 0.8
DEFAULT_TOP_P = 0.1
# ---------------------

def get_github_token():
    """
    Retrieves the GitHub token from the environment variables.
    Exits the script with an error message if the token is not found.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: The 'GITHUB_TOKEN' environment variable is not set.", file=sys.stderr)
        print("Please create a Personal Access Token (PAT) on GitHub and set it as GITHUB_TOKEN.", file=sys.stderr)
        print("See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens", file=sys.stderr)
        sys.exit(1)
    return token

class JambaAgent(BaseAgent):
    def __init__(self):
        super().__init__("Jamba")
        self.client = self._initialize_client()

    def _initialize_client(self):
        github_token = get_github_token()
        try:
            return ChatCompletionsClient(
                endpoint=ENDPOINT,
                credential=AzureKeyCredential(github_token),
            )
        except Exception as e:
            print(f"Error creating ChatCompletionsClient: {e}", file=sys.stderr)
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

                self.add_to_history(user_input, None) # Add user message to history

                # Convert chat history to the format expected by the API
                api_messages = []
                for msg in self.chat_history:
                    if msg.get("user"):
                        api_messages.append(UserMessage(content=msg["user"]))
                    if msg.get("bot"):
                        api_messages.append(AssistantMessage(content=msg["bot"]))


                response = self.client.complete(
                    messages=api_messages,
                    model=DEFAULT_MODEL,
                    temperature=DEFAULT_TEMPERATURE,
                    top_p=DEFAULT_TOP_P,
                )
                
                assistant_message = response.choices[0].message
                
                if assistant_message.content:
                    print(f"Assistant: {assistant_message.content}")
                    # Update the last entry in history with the bot's response
                    self.chat_history[-1]["bot"] = assistant_message.content
                    self.save_chat_history()


                if assistant_message.tool_calls:
                    print("Assistant wants to use tools:")
                    for tool_call in assistant_message.tool_calls:
                        print(f"- Function: {tool_call.function.name}")
                        print(f"  Arguments: {tool_call.function.arguments}")
                    # In a real application, you would execute the tools here
                    # and append the results as ToolMessage objects.
                    # For this example, we'll just inform the user.

            except HttpResponseError as e:
                print(f"\nAn API error occurred: {e}", file=sys.stderr)
                if e.status_code == 401:
                    print("Authentication failed. Please check your GITHUB_TOKEN.", file=sys.stderr)
                self.chat_history.pop() # Remove the last user message to allow retrying
            except (KeyboardInterrupt, EOFError):
                print("\nExiting chat.")
                break
            except Exception as e:
                print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
                if self.chat_history:
                    self.chat_history.pop()


def main():
    """
    Main function to run the interactive chat client.
    """
    agent = JambaAgent()
    agent.chat()


if __name__ == "__main__":
    main()
