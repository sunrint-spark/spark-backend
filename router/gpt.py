from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
import openai
import os

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")
engine_name = "ft:gpt-3.5-turbo-0125:personal::9qDv3x9y"
@cbv(router)
class GPT:
    @router.post("/gpt")
    async def gpt(self, prompt: str):
        completion = openai.chat.completions.create(
            model=engine_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content






