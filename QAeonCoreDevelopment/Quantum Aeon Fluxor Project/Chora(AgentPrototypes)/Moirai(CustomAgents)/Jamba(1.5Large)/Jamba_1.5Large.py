"""Run this model in Python

> pip install azure-ai-inference

This script provides an interactive chat session with a Jamba model
hosted on GitHub's inference service. It maintains conversation history
for context-aware interactions.
"""
import os
import sys
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, UserMessage, ToolMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

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

def main():
    """
    Main function to run the interactive chat client.
    """
    github_token = get_github_token()

    try:
        client = ChatCompletionsClient(
            endpoint=ENDPOINT,
            credential=AzureKeyCredential(github_token),
        )
    except Exception as e:
        print(f"Error creating ChatCompletionsClient: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting interactive chat with model: {DEFAULT_MODEL}")
    print("Type 'quit' or 'exit' to end the session (or press Ctrl+C).")
    print("-" * 20)

    # This list will store the conversation history
    messages = []

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["quit", "exit"]:
                print("Exiting chat.")
                break
            
            if not user_input:
                continue

            messages.append(UserMessage(content=user_input))

            response = client.complete(
                messages=messages,
                model=DEFAULT_MODEL,
                temperature=DEFAULT_TEMPERATURE,
                top_p=DEFAULT_TOP_P,
            )
            
            assistant_message = response.choices[0].message
            
            if assistant_message.content:
                print(f"Assistant: {assistant_message.content}")
                messages.append(assistant_message)

            if assistant_message.tool_calls:
                print("Assistant wants to use tools:")
                for tool_call in assistant_message.tool_calls:
                    print(f"- Function: {tool_call.function.name}")
                    print(f"  Arguments: {tool_call.function.arguments}")
                # In a real application, you would execute the tools here
                # and append the results as ToolMessage objects.
                # For this example, we'll just inform the user.
                messages.append(assistant_message) # Add assistant's tool request to history
                # Example of adding a tool response:
                # messages.append(ToolMessage(content="<tool_output>", tool_call_id=tool_call.id))


        except HttpResponseError as e:
            print(f"\nAn API error occurred: {e}", file=sys.stderr)
            if e.status_code == 401:
                print("Authentication failed. Please check your GITHUB_TOKEN.", file=sys.stderr)
            # Remove the last user message to allow retrying
            if messages and isinstance(messages[-1], UserMessage):
                messages.pop()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
            # Remove the last user message to allow retrying
            if messages and isinstance(messages[-1], UserMessage):
                messages.pop()


if __name__ == "__main__":
    main()
