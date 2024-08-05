from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
import openai
import os

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")
model_name = "ft:gpt-3.5-turbo-0125:personal::9rGlkk8Q"
@cbv(router)
class GPT:
    @router.post("/gpt")
    async def gpt(self, prompt: str):
        completion = openai.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": """만약 어떤 단어나 문장 뒤에 키워드 라는 말이 있으면 그 말의 키워드를 3~4개를 keyword:"" json형식으로 출력해야해 예를 들면
                                자율주행차를 입력헀을때
                                {
                                    "keyword": [
                                        "자율주행 기술",
                                        "센서 및 데이터 처리",
                                        "교통안전",
                                        "법규 및 정책"
                                    ]
                                }
                                또 사용자가 키워드를 입력하면 그 키워드에 대해 좀 더 자세한 키워드를 3~4씩 출력해야해
                                또 만약 어떤 단어나 문장 뒤에 마무리 라는 말이 있으면 그 말의 키워드를 3~4개를  keyword:"" json 형태로 출력하고 그 말을 설명한 문장을 description:""에 저장해 예를들면
                                {
                                    "description": "차량이 스스로 안전하게 주행할 수 있도록 하는 자율주행 기술, 이를 통해 장애물 회피, 교통 신호 인식, 주행 경로 최적화를 달성합니다."
                                    "keyword": [
                                        "머신러닝 알고리즘",
                                        "컴퓨터 비전",
                                        "경로 계획",
                                        "센서 퓨전"
                                    ],
                                }
                                """
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,


            response_format={"type": "json_object"}
        )
        print(f'input: {prompt}')
        print(completion.choices[0].message.content)
        return completion.choices[0].message.content






