"""Run this model in Python

> pip install mistralai>=1.0.0
"""
import os
from mistralai import Mistral

# To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings. 
# Create your PAT token by following instructions here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
client = Mistral(
    api_key=os.environ["GITHUB_TOKEN"],
    server_url="https://models.github.ai/inference"
)

response = client.chat.complete(
    model="mistral-ai/Mistral-Large-2411",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
    temperature=1.0,
    max_tokens=1000,
    top_p=1.0
)

print(response.choices[0].message.content)