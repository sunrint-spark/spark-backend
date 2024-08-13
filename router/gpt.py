from fastapi import APIRouter, HTTPException, Request
from fastapi_restful.cbv import cbv
from openai import OpenAI
import aiohttp
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .notion_log import notionlog

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
당신은 AI 아이디어 스케치북이라는 시스템입니다. 사용자가 주제를 입력하면 그에 따른 아이디어를 트리 형식으로 제시해주세요.
각 단계에서 3-4개의 하위 항목을 제안하고, 사용자가 선택한 항목에 대해 더 자세한 하위 카테고리나 아이디어를 제시하세요. 최대 5단계까지 깊이 들어갈 수 있습니다.
필수 규칙:
최대한 단계를 줄이세요.
각 항목은 간결하게 설명하세요.
출력은 json형태로 출력하세요.
진행 상황에 start, select, end, markdown를 "status"에 저장하세요.
사용자가 특정 항목을 선택하면 그에 대한 항목만 제시하세요.
사용자의 입력에 따라 유연하게 대응하세요.
규칙:
사용자가 입력한것의 상위 아이디어를 그대로 "uppercategories"에 저장하세요.
사용자가 입력한 아이디어를 그대로 "currentcategories"에 저장하세요.
사용자가 입력한것의 하위 아이디어 를"subcategories"에 리스트로 저장하세요.
(예{
  "uppercategories": "미니멀리즘",
  "subcategories": [ "디자인 원칙",  "색상 팔레트",
"가구 및 장식", "공간 활용"]
})
1단계일때는 "uppercategories":null로 저장하고, "currentcategories"에 사용자가 입력한 그대로 저장하세요.
4단계에 도달하거나 사용자가 종료 요청을 하면 최종 아이디어나 구체적인 제안을 "idea"에 제시하세요.(예
{
  "status": "end",
  "uppercategories": "자율주행 자동차 개발",
  "currentcategories": "데이터 분석",
  "idea": [
    "객체 인식을 위해 YOLO 또는 SSD와 같은 알고리즘을 사용하여 실시간으로 차량 및 보행자를 탐지합니다.",
    "차선 감지를 위해 Canny edge detection 및 Hough 변환을 활용하여 도로 차선을 식별합니다.",
    "이미지 전처리 기술을 적용하여 노이즈 제거, 색상 보정 등을 통해 데이터 품질을 향상시킵니다.",
    "딥러닝 모델을 활용해 학습된 네트워크를 사용하여 다양한 주행 상황에 적응할 수 있습니다."
  ],
  "image_keyword": "자율주행 데이터 분석",
  "image_urls": []
})
최종 아이디어나 구체적인 제안을 제시할때 기존 저장형식에 추가로 정리할 수 있는 단어를 "image_keyword"에 저장하고 "image_urls" = null으로 저장하세요.
markdown 규칙:
status가 'end'인 상황에서 #markdown을 입력받으면 "status": "markdown", "main_title":"제목", "markdown": "내용"형식으로 저장하세요.
"main_title"에는 1단계 "currentcategories"를 저장하세요.
"markdown"에는 1단계부터 #markdown을 입력받기 전까지의 트리를 마크다운형식으로 저장하세요
최종단계에 도달한 후 #markdown을 입력받으면 "status": "markdown"으로 저장하고, 지금까지 했던 모든 대화를 정리하여 "main_title에 단어로 저장하고, 1단계 부터 최종 단계의 트리를 마크다운 형식으로 트리 구조를 확인 할 수 있도록 "markdown"에 저장하세요.
마크 다운 형식으로 저장할때 1단계는 들여쓰기 없이 , 2단계는 들여쓰기 1개, 3단계는 들여쓰기 2단계 ... 이 순서대로 저장하세요.
"""


assistant = client.beta.assistants.create(
    name="Idea_assistant",
    instructions=system_message,
    model=engine_name,
)

# Create a thread once and reuse it for all requests
thread = client.beta.threads.create()

# 전역 변수로 notion_image_urls 선언
notion_image_urls = []

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
    global notion_image_urls
    try:
        answer = answer.replace("```", "").strip()
        answer = answer.replace("json", "").strip()
        json_answer = json.loads(answer.strip())

        if json_answer.get("image_keyword"):
            image_urls = await search_google_images(
                google_api_key, google_search_engine_id, json_answer["image_keyword"]
            )
            json_answer["image_urls"] = image_urls
            notion_image_urls = image_urls

        return json_answer
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Failed to decode JSON response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during JSON conversion: {str(e)}")

async def notionlogformat(json_answer):
    global notion_image_urls
    print(f'notion_image_urls: {notion_image_urls}')
    main_title = json_answer.get("main_title")
    markdown_content = json_answer.get("markdown")
    print("노션에 기록중...")
    await notionlog(main_title, markdown_content, notion_image_urls)

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
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt,
            )
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

                if json_answer.get("status") == "markdown":
                    await notionlogformat(json_answer)

                return json_answer
            else:
                raise HTTPException(status_code=500, detail=f"Thread run status: {run.status}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
