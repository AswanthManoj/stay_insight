from pydantic import BaseModel
import httpx
import asyncio, os
from typing import List

# class Step(BaseModel):
#     explanation: str
#     output: str

# class MathReasoning(BaseModel):
#     steps: List[Step]
#     final_answer: str

# class AsyncOpenAI:
#     def __init__(self, api_key: str):
#         self.api_key = api_key
#         self.base_url = "https://api.openai.com/v1"

#     async def chat_completion_parse(self, model: str, messages: List[dict], response_format: BaseModel):
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 f"{self.base_url}/chat/completions",
#                 headers={
#                     "Authorization": f"Bearer {self.api_key}",
#                     "Content-Type": "application/json"
#                 },
#                 json={
#                     "model": model,
#                     "messages": messages,
#                     "response_format": {
#                         "type": "json_schema",
#                         "json_schema": response_format.model_json_schema()
#                     }
#                 }
#             )
#             response.raise_for_status()
#             data = response.json()
#             return response_format.model_validate(data['choices'][0]['message']['function_call']['arguments'])

# async def main():
#     client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#     completion = await client.chat_completion_parse(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "You are a helpful math tutor. Guide the user through the solution step by step."},
#             {"role": "user", "content": "how can I solve 8x + 7 = -23"}
#         ],
#         response_format=MathReasoning
#     )

#     print(completion)

# if __name__ == "__main__":
#     asyncio.run(main())

from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor. Guide the user through the solution step by step."},
        {"role": "user", "content": "how can I solve 8x + 7 = -23"}
    ],
    response_format=MathReasoning,
)

math_reasoning = completion.choices[0].message.parsed

print(math_reasoning)