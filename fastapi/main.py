from fastapi import FastAPI, WebSocket, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, HumanResponses, AIFollowUpQuestions
from pydantic import BaseModel
import httpx
import logging

import random

from src.cli import search

app = FastAPI()


class FollowUpQuestionCreate(BaseModel):
    follow_up_question: str

class HumanResponseCreate(BaseModel):
    expected_response: str
    follow_up_questions: list[FollowUpQuestionCreate] = []

class HumanResponse(BaseModel):
    response_id: int
    expected_response: str
    follow_up_questions: list[FollowUpQuestionCreate]

    class Config:
        orm_mode = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    data_path = "data/20240428160810.json"
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # 候補者の発言に似たテキストを検索
        similar_candidate_replies = search(path=data_path, query=data, size=3, only_candidate=True)
        similar_students_reply = random.choice(similar_candidate_replies)
        # そのテキストに対応する返答を取得
        interviewer_response_content = random.choice(similar_students_reply.children).comment
        await websocket.send_text(f"{interviewer_response_content}")


@app.post("/responses/", response_model=HumanResponse)
def create_response(response: HumanResponseCreate, db: Session = Depends(get_db)):
    db_response = HumanResponses(
        expected_response=response.expected_response
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)

    for fq in response.follow_up_questions:
        db_follow_up = AIFollowUpQuestions(
            response_id=db_response.response_id,
            follow_up_question=fq.follow_up_question
        )
        db.add(db_follow_up)
    db.commit()

    return db_response

@app.get("/responses/{response_id}", response_model=HumanResponse)
def read_response(response_id: int, db: Session = Depends(get_db)):
    db_response = db.query(HumanResponses).filter(HumanResponses.response_id == response_id).first()
    if db_response is None:
        raise HTTPException(status_code=404, detail="Response not found")
    return db_response


class SynthesisRequest(BaseModel):
    text: str

@app.post("/synthesize")
async def synthesize_text(request: SynthesisRequest):
    lambda_url = "https://6h63ipcwp8.execute-api.us-east-1.amazonaws.com/role-ai/"
    api_key = ""  # APIキーをここに設定

    headers = {
        "x-api-key": api_key,  # API GatewayでAPIキーの使用を要求している場合
        "Content-Type": "application/json"
    }

    logging.info(f"Sending request to Lambda: {request.text}")

    async with httpx.AsyncClient() as client:
        response = await client.post(lambda_url, json={"text": request.text}, headers=headers)
    
    logging.info(f"Received response from Lambda: Status {response.status_code}, Body {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failedss to call Lambda function")