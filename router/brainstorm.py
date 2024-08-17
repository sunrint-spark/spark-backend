import asyncio
import traceback

import aiohttp, logging
import json, os
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI as OpenAI

from service.credential import get_current_user
from service.notion_log import notionlog
from entity.user import User as ODMUser

from utils.log import Logger
from typing import AsyncGenerator

logger = Logger.create(__name__, level=logging.DEBUG)

router = APIRouter(
    prefix="/brainstorm",
    tags=["GPT"],
)
client = OpenAI()

# 환경 변수에서 API 키 로드
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
gpt_assistant_id = os.getenv("ASSISTANT_ID")

# 전역 변수로 notion_image_urls 선언
notion_image_urls = []
notion_search_urls = []


async def search_google_url(api_key, search_engine_id, query, num_results=1):
    search_url = "https://www.googleapis.com/customsearch/v1"
    search_params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": num_results,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Google API error: {response.reason}",
                    )
                results = await response.json()
                search_urls = [item.get("link") for item in results.get("items", [])]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while fetching urls: {str(e)}"
        )

    return search_urls


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
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Google API error: {response.reason}",
                    )
                results = await response.json()
                image_urls = [item.get("link") for item in results.get("items", [])]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while fetching images: {str(e)}"
        )

    return image_urls


async def convert2json(answer):
    global notion_image_urls
    global notion_search_urls
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
        if json_answer.get("search_keyword"):
            for keyword in json_answer["search_keyword"]:
                search_urls = await search_google_url(
                    google_api_key, google_search_engine_id, keyword
                )
                json_answer["search_urls"] += search_urls
                notion_search_urls += search_urls

        return json_answer
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Failed to decode JSON response.")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during JSON conversion: {str(e)}",
        )


async def notionlogformat(json_answer):
    global notion_image_urls
    global notion_search_urls
    print(f"notion_image_urls: {notion_image_urls}")
    main_title = json_answer.get("main_title")
    markdown_content = json_answer.get("markdown")
    print("노션에 기록중...")
    notion_url = await notionlog(
        main_title, markdown_content, notion_image_urls, notion_search_urls
    )
    result_json = {"notion_url": notion_url}
    return result_json


async def stream_assistant(prompt: str, thread_id: str) -> AsyncGenerator[str, None]:
    try:
        _message = await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt,
        )
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=gpt_assistant_id,
        )
        logger.info(f"Run ID: {run.id}")
        while True:
            run = await client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )
            logger.info(f"[{thread_id}, Run status: {run.status}")
            if run.status == "completed":
                break
            await asyncio.sleep(1)
        messages = await client.beta.threads.messages.list(
            thread_id=thread_id, run_id=run.id
        )
        json_answer = await convert2json(messages.data[0].content[0].text.value)

        if json_answer.get("status") == "markdown":
            json_answer = await notionlogformat(json_answer)

        yield str(
            json.dumps(
                {
                    "status": "completed",
                    "thread_id": thread_id,
                    "result": json_answer,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/stream")
async def brainstorm(
    thread_id: str = Query(..., title="Thread ID"),
    prompt: str = Query(..., title="Prompt"),
    _user: "ODMUser" = Depends(get_current_user),
):
    if thread_id is None:
        raise HTTPException(status_code=400, detail="Thread ID is required.")
    if thread_id == "new":
        new_thread = await client.beta.threads.create()
        thread_id = new_thread.id
    print("hello")

    return StreamingResponse(
        stream_assistant(prompt, thread_id), media_type="text/event-stream"
    )
