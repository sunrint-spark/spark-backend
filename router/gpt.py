from fastapi import APIRouter
from fastapi_restful.cbv import cbv
from openai import OpenAI
import os
# import json
import aiohttp

router = APIRouter()
client = OpenAI()

OpenAI.api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
engine_name = "gpt-4o-mini-2024-07-18"

system_message = """
당신은 AI 아이디어 스케치북이라는 시스템입니다. 사용자가 주제를 입력하면 그에 따른 아이디어를 트리 형식으로 제시해주세요. 
            각 단계에서 3-5개의 하위 항목을 제안하고, 사용자가 선택한 항목에 대해 더 자세한 하위 카테고리나 아이디어를 제시하세요.
            최대 3단계까지 깊이 들어갈 수 있습니다.
            규칙:
                항상 트리 구조로 응답하세요 
                각 항목은 간결하게 설명하세요.
                사용자가 특정 항목을 선택하면 그에 대한 하위 항목을 제시하세요.
                하위 항목을 제시할 때, 선택된 항목의 바로 1단계 아래 항목만 제시하세요.
                3단계에 도달하면 최종 아이디어나 구체적인 제안을 제시하세요.
                사용자의 입력에 따라 유연하게 대응하세요.
                                """

assistant = client.beta.assistants.create(
    name="Idea_assistant",
    instructions=system_message,
    model=engine_name,
)

# Create a thread once and reuse it for all requests
thread = assistant.threads.create()

async def search_google_images(api_key, search_engine_id, query, num_results=3):
    search_url = "https://www.googleapis.com/customsearch/v1"
    search_params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "searchType": "image",
        "num": num_results,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, params=search_params) as response:
            if response.status != 200:
                response.raise_for_status()
            results = await response.json()
            image_urls = [item.get("link") for item in results.get("items", [])]

    return image_urls

@cbv(router)
class GPT:
    @router.post("/gpt")
    async def gpt(self, prompt: str):
        global thread
        if thread is None:
            thread = assistant.threads.create()
        print(f'thread id: {thread.id}')
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        print(f'prompt: {prompt}')
        print(f'message: {message["content"]}')
        return message["content"]



