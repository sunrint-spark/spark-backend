import asyncio
import aiohttp
import json
import os

# Notion API 설정
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


async def create_page(session, title, markdown_content):
    url = "https://api.notion.com/v1/pages"

    new_page_data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {"title": {"title": [{"text": {"content": title}}]}},
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": markdown_content}}
                    ]
                },
            }
        ],
    }

    async with session.post(url, headers=headers, json=new_page_data) as response:
        if response.status == 200:
            print(f"페이지 '{title}'이(가) 성공적으로 생성되었습니다.")
        else:
            print(f"오류 발생: {response.status}")
            print(await response.text())


async def notionlog(main_title, markdown_content):
    try:
        async with aiohttp.ClientSession() as session:
            await create_page(session, main_title, markdown_content)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
