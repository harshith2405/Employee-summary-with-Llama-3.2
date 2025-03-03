import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Make the API call
response = openai.Completion.create(
    model="gpt-3.5-turbo",
    prompt="give me 10 best anime",
    max_tokens=100
)

# Extract and print the response
output = response['choices'][0]['text']
print(output)
