from fastapi import APIRouter, HTTPException, Request
from fastapi_restful.cbv import cbv
from openai import OpenAI
import os
import aiohttp
import json


router = APIRouter(
    tags=["GPT"],
)
client = OpenAI()

# 환경 변수에서 API 키 로드
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
engine_name = "gpt-4o-mini-2024-07-18"

system_message = """
당신은 AI 아이디어 스케치북이라는 시스템입니다. 사용자가 주제를 입력하면 그에 따른 아이디어를 트리 형식으로 제시해주세요. 각 단계에서 3-4개의 하위 항목을 제안하고, 사용자가 선택한 항목에 대해 더 자세한 하위 카테고리나 아이디어를 제시하세요. 최대 5단계까지 깊이 들어갈 수 있습니다.
규칙:
최대한 단계를 줄이세요.
각 항목은 간결하게 설명하세요.
출력은 json형태로 출력하세요.
진행 상황에 start, select, end를 "status"에 저장하세요.
사용자가 입력한것의 상위 아이디어를 그대로 "uppercategories"에 저장하세요.
사용자가 입력한 아이디어를 그대로 "currentcategories"에 저장하세요.
사용자가 입력한것의 하위 아이디어 를"subcategories"에 리스트로 저장하세요.
(예{
  "uppercategories": "미니멀리즘",
  "subcategories": [ "디자인 원칙",  "색상 팔레트",
"가구 및 장식", "공간 활용"]
})
사용자가 특정 항목을 선택하면 그에 대한 항목만 제시하세요.
1단계일때는 "uppercategories":null로 저장하고, "currentcategories"에 사용자가 입력한 그대로 저장하세요.
4단계에 도달하거나 사용자가 종료 요청을 하면 최종 아이디어나 구체적인 제안을 제시하세요.
최종 아이디어나 구체적인 제안을 제시할때 기존 저장형식에 추가적으로 정리할 수 있는 단어를 "image_keyword"에 저장하고 "image_urls" = null으로 저장하세요.
최종단계에 도달한 후 만약 마크다운으로 정리라는 말을 사용자가 하면 지금까지 했던 모든 대화를 정리하여 "main_title에 단어로 저장하고, 모든 대화 기록을 마크다운 형식으로 트리 구조를 확인 할 수 있도록 "markdown"에 저장하세요.
사용자의 입력에 따라 유연하게 대응하세요.
"""

assistant = client.beta.assistants.create(
    name="Idea_assistant",
    instructions=system_message,
    model=engine_name,
)

# Create a thread once and reuse it for all requests
thread = client.beta.threads.create()

async def search_google_images(api_key, search_engine_id, query, num_results=3):
    search_url = "https://www.googleapis.com/customsearch/v1"
    search_params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "searchType": "image",
        "num": num_results,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail=f"Google API error: {response.reason}")
                results = await response.json()
                image_urls = [item.get("link") for item in results.get("items", [])]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching images: {str(e)}")

    return image_urls

async def convert2json(answer):
    try:
        answer = answer.replace("```", "").strip()
        answer = answer.replace("json", "").strip()
        json_answer = json.loads(answer.strip())
        if json_answer.get("image_keyword"):
            image_urls = await search_google_images(
                google_api_key, google_search_engine_id, json_answer["image_keyword"]
            )
            json_answer["image_urls"] = image_urls
        return json_answer
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Failed to decode JSON response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during JSON conversion: {str(e)}")

def threadcheck():
    global thread
    if thread is None:
        thread = client.beta.threads.create()

@cbv(router)
class GPT:
    @router.post("/gpt")
    async def gpt(self, prompt: str, request: Request):
        threadcheck()

        try:
            # print(f'assistant id:{assistant.id} thread id: {thread.id}')
            # 스레드에 메시지 추가
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt,
            )
            # 스레드 실행
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions=system_message
            )

            if run.status == 'completed':
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                print(f'prompt: {prompt}')
                json_answer = await convert2json(messages.data[0].content[0].text.value)
                print(f'json_answer: {json_answer}')
                return json_answer
            else:
                raise HTTPException(status_code=500, detail=f"Thread run status: {run.status}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
