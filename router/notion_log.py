import asyncio
import aiohttp
import json
import os

# Notion API 설정
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = "your_database_id_here"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

async def create_page(session, title, markdown_content):
    url = "https://api.notion.com/v1/pages"

    new_page_data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": markdown_content}}]
                }
            }
        ]
    }

    async with session.post(url, headers=headers, json=new_page_data) as response:
        if response.status == 200:
            print(f"페이지 '{title}'이(가) 성공적으로 생성되었습니다.")
        else:
            print(f"오류 발생: {response.status}")
            print(await response.text())

async def main():
    title = input("페이지 제목을 입력하세요: ")
    markdown_content = input("마크다운 내용을 입력하세요: ")

    async with aiohttp.ClientSession() as session:
        await create_page(session, title, markdown_content)
