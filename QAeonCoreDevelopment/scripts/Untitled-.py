https://b1d04880-b767-476f-9ef4-561fcdfda031.europe-west3-0.gcp.cloud.qdrant.io

import requests

# List all collections (GET /collections)
response = requests.get(
  "httpss://b1d04880-b767-476f-9ef4-561fcdfda031.europe-west3-0.gcp.cloud.qdrant.io:6333/collections",
  headers={
    "api-key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.KHYTCR-5fdQnPUJddlGBZogfsehty8rl5QwMqHXzKys"
  },
)

print(response.json())
