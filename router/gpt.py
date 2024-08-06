from fastapi import APIRouter
from fastapi_restful.cbv import cbv
import openai
import os
import json
import requests



router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
engine_name = "gpt-4o-mini-2024-07-18"


system_message = """만약 어떤 단어나 문장 뒤에 키워드 라는 말이 있으면 그 말의 키워드를 3~4개를 keyword:"" json형식으로 출력하고 "status":select"로 출력해야해 예를 들면
                                자율주행차 키워드를 입력헀을때
                                {
                                    "keyword": [
                                        "자율주행 기술",
                                        "센서 및 데이터 처리",
                                        "교통안전",
                                        "법규 및 정책"
                                    ],
                                    "status": "select"
                                }
                                또 사용자가 키워드를 입력하면 그 키워드에 대해 좀 더 자세한 키워드를 3~4씩 출력해야해
                                만약 문장 뒤에 다시 라는 말이 있으면  그 말의 키워드를 새롭게 3~4개를 keyword:"" json 형식으로 출력하고 status는 방금 전 대화의 status로 출력해야해 예를 들면
                                 자율주행차 키워드를 입력헀을때
                                {
                                    "keyword": [
                                        "자율주행 기술",
                                        "센서 및 데이터 처리",
                                        "교통안전",
                                        "법규 및 정책"
                                    ],
                                    "status": "select"
                                }
                                자율주행차 다시 를 입력헀을때
                                {
                                    "keyword": [
                                        "자율주행 기술",
                                        "센서 및 데이터 처리",
                                        "인공지능",
                                        "자율주행차 시장 동향"
                                    ],
                                    "status": "select"
                                }
                                만약 어떤 단어나 문장 뒤에 생성과 비슷한 의미의 시작 단어가 있으면 그 말의 키워드를 3~4를 keyword:"" json 형식으로 출력하고 "status":"start"로 출력해야해
                                자율주행차 시작을 입력헀을때
                                {
                                    "keyword": [
                                        "자율주행 기술",
                                        "센서 및 데이터 처리",
                                        "교통안전",
                                        "법규 및 정책"
                                    ],
                                    "status": "start"
                                }

                                또 만약 어떤 단어나 문장 뒤에 마무리 혹은 까지 라는 말이 있으면 그 말의 키워드를 3~4개를  keyword:"" json 형태로 출력하고 그 말을 설명한 문장을 description:""에 저장하고 
                                "status":"end"로 출력해야해 또한 마지막에 가장 최근인 status:start인 것부터 지금까지의 대화를 간단한 문장으로 정리해 image_keyword에 저장해야해 예를들면  
                                {
                                    "description": "차량이 스스로 안전하게 주행할 수 있도록 하는 자율주행 기술, 이를 통해 장애물 회피, 교통 신호 인식, 주행 경로 최적화를 달성합니다."
                                    "keyword": [
                                        "머신러닝 알고리즘",
                                        "컴퓨터 비전",
                                        "경로 계획",
                                        "센서 퓨전"
                                    ],
                                    "status": "end"
                                    "image_keyword": 자율주행 기술
                                    "image_urls": None
                                } 
                                """


def search_google_images(api_key, search_engine_id, query, num_results=3):
    search_url = "https://www.googleapis.com/customsearch/v1"
    search_params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "searchType": "image",
        "num": num_results,
    }

    response = requests.get(search_url, params=search_params)
    results = response.json()

    image_urls = []
    for item in results.get("items", []):
        image_urls.append(item.get("link"))

    return image_urls

@cbv(router)
class GPT:
    @router.post("/gpt")
    async def gpt(self, prompt: str):
        completion = openai.chat.completions.create(
            model=engine_name,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            # response_format={"type": "json_object"}
        )
        response = json.loads(completion.choices[0].message.content)
        image_query = response.get("image_keyword")


        if image_query:
            print("이미지 검색중!")
            image_query = search_google_images(google_api_key, google_search_engine_id, image_query)
            response["image_urls"] = image_query
            print("이미지 검색 완료!")


        print(f'image_query: {image_query}')
        print(f'input: {prompt}')
        print(f'response: {response}')
        return response
