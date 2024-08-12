import requests

# Notion API 설정
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_API_KEY = "YOUR_NOTION_API_KEY"
DATABASE_ID = "YOUR_DATABASE_ID"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 트리 구조로 저장할 데이터
prompt = "Example Prompt"
json_message = {
    "message_1": "This is the first message.",
    "message_2": {
        "sub_message_1": "This is a sub-message.",
        "sub_message_2": "This is another sub-message."
    },
    "message_3": "This is the third message."
}


def create_notion_page(parent_id, title, content=None):
    # 노션 페이지 생성 요청
    data = {
        "parent": {"type": "database_id", "database_id": parent_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        },
        "children": []
    }

    # 자식 블록 추가
    if content:
        data["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]

    response = requests.post(NOTION_API_URL, headers=headers, json=data)
    return response.json()


def save_tree_structure(database_id, prompt, json_message):
    # 루트 노드 생성 (Prompt)
    prompt_page = create_notion_page(database_id, prompt)
    prompt_page_id = prompt_page["id"]

    # json_message를 순회하면서 트리 구조 생성
    def add_json_to_notion(parent_id, json_data):
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                child_page = create_notion_page(parent_id, key)
                child_page_id = child_page["id"]
                add_json_to_notion(child_page_id, value)
        else:
            create_notion_page(parent_id, str(json_data), str(json_data))

    add_json_to_notion(prompt_page_id, json_message)


# 트리 구조 저장 실행
save_tree_structure(DATABASE_ID, prompt, json_message)
