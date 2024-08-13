import asyncio
import aiohttp
import json
import os
from urllib.parse import urlparse

# Notion API 설정
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def is_valid_image_url(url):
    """
    Check if the URL ends with a valid image extension.
    """
    valid_extensions = (".jpg", ".jpeg", ".png")
    parsed_url = urlparse(url)
    path = parsed_url.path
    return path.lower().endswith(valid_extensions)

async def create_page_with_images(session, title, markdown_content, image_urls):
    url = "https://api.notion.com/v1/pages"

    # 필터링된 이미지 URL만 사용
    filtered_image_urls = [url for url in image_urls if is_valid_image_url(url)]

    # 기본 텍스트 블록 생성
    children_blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": markdown_content}}]
            }
        }
    ]

    # 유효한 이미지 URL을 이미지 블록으로 추가
    for image_url in filtered_image_urls:
        image_block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": image_url}
            }
        }
        image_url_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": image_url}}]
            }
        }
        children_blocks.append(image_block)
        children_blocks.append(image_url_block)

    new_page_data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        },
        "children": children_blocks
    }

    async with session.post(url, headers=headers, json=new_page_data) as response:
        if response.status == 200:
            print(f"페이지 '{title}'이(가) 성공적으로 생성되었습니다.")
        else:
            print(f"오류 발생: {response.status}")
            print(await response.text())

async def notionlog(main_title, markdown_content, image_urls):
    try:
        async with aiohttp.ClientSession() as session:
            await create_page_with_images(session, main_title, markdown_content, image_urls)
    except Exception as e:
        print(f"An error occurred: {str(e)}")