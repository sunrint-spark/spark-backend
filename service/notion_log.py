import aiohttp
import os
from urllib.parse import urlparse

# import json
# import asyncio


# Notion API 설정
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def is_valid_image_url(url):
    valid_extensions = (".jpg", ".jpeg", ".png")
    parsed_url = urlparse(url)
    path = parsed_url.path
    return path.lower().endswith(valid_extensions)


async def create_page_with_images(
    session, title, markdown_content, image_urls, search_urls
):
    url = f"https://api.notion.com/v1/pages"

    # 마크다운 내용을 줄 단위로 분리
    lines = markdown_content.split("\n")
    children = []

    for line in lines:
        if line.startswith("#"):
            # 제목 레벨 확인
            level = len(line.split()[0])
            content = line.lstrip("#").strip()

            if level == 1:
                block_type = "heading_1"
            elif level == 2:
                block_type = "heading_2"
            elif level == 3:
                block_type = "heading_3"
            else:
                block_type = "paragraph"

            children.append(
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    },
                }
            )
        else:
            # 일반 텍스트
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    },
                }
            )

    children.append(
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "참조 링크"}}]
            },
        }
    )

    for search_url in search_urls:
        search_url_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": search_url, "link": {"url": search_url}},
                    }
                ]
            },
        }
        children.append(search_url_block)

    children.append(
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "참조 이미지"}}]
            },
        }
    )
    # 필터링된 이미지 URL 리스트
    filtered_image_urls = [url for url in image_urls if is_valid_image_url(url)]

    # 이미지 블록 추가
    for image_url in filtered_image_urls:
        image_block = {
            "object": "block",
            "type": "image",
            "image": {"type": "external", "external": {"url": image_url}},
        }
        children.append(image_block)

        # 이미지 URL을 텍스트로 추가
        image_url_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": image_url,  # 표시할 텍스트로 이미지 URL 사용
                            "link": {"url": image_url},  # URL을 하이퍼링크로 추가
                        },
                    }
                ]
            },
        }
        children.append(image_url_block)

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {"title": {"title": [{"text": {"content": title}}]}},
        "children": children,
    }

    text_context = []
    text_context.append(lines)
    text_context.append(image_urls)
    text_context.append(search_urls)

    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            print(f"페이지 '{title}'이(가) 성공적으로 생성되었습니다.")
            new_page = await response.json()
            page_id = new_page["id"]

            page_url = f"https://www.notion.so/{page_id.replace('-', '')}"

            converted_url = convert_notion_url(page_url)

            print(f"Page created successfully! You can view it at: {converted_url}")

            json_return = {"page_url": converted_url, "text_context": text_context}
            return json_return

        else:
            print(f"오류 발생: {response.status}")
            print(await response.text())


def convert_notion_url(original_url):
    new_base_url = "https://sparkcontents.notion.site/"
    path = original_url.replace("https://www.notion.so/", "")
    new_url = new_base_url + path
    return new_url


async def notionlog(main_title, markdown_content, image_urls, search_urls):
    try:
        async with aiohttp.ClientSession() as session:
            return await create_page_with_images(
                session, main_title, markdown_content, image_urls, search_urls
            )
    except Exception as e:
        print(f"An error occurred: {str(e)}")
