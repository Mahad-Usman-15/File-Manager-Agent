from agents import AsyncOpenAI,OpenAIChatCompletionsModel,RunConfig
from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_KEY=os.getenv("OPENAI_KEY")
BASE_URL="https://api.openai.com/v1/chat/completions"
if not OPENAI_KEY:
  raise ValueError("APi key not found")
client=AsyncOpenAI(
    api_key=OPENAI_KEY,
    base_url=BASE_URL
)

model=OpenAIChatCompletionsModel(
    openai_client=client,
    model="gemini-2.0-flash"
)


config=RunConfig(
    model=model,
    model_provider=client,
    tracing_disabled=True,
)

