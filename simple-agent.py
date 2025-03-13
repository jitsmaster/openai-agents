from agents import Agent, OpenAIChatCompletionsModel, Runner
from openai import AsyncOpenAI

# ollama_client = AsyncOpenAI(
#     api_key="",  # Your OpenAI API key
#     base_url="http://localhost:11434/v1")  # The base URL of the Ollama API

# agent = Agent(name="Assistant", 
#               instructions="You are a helpful assistant",
#               model=OpenAIChatCompletionsModel( 
#                   model="gemma3",  # The model to use
#                   openai_client=ollama_client))
agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "写一首关于编程中递归的俳句。")
print(result.final_output)
