from fastapi import FastAPI, WebSocket, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, HumanResponses, AIFollowUpQuestions
from pydantic import BaseModel

import random


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
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # 受け取ったtextが想定回答と一致しているものを取得
        db_response = db.query(HumanResponses).filter(HumanResponses.expected_response == data).first()
        if db_response:
            if db_response.follow_up_questions:
                # follow_up_questionsのリストからランダムに一つ選択して送信
                follow_up_question = random.choice(db_response.follow_up_questions)
                await websocket.send_text(follow_up_question.follow_up_question)
            else:
                # 想定回答と一致しているがDBに深掘り質問のデータがない場合
                await websocket.send_text("No follow-up questions available.")
        else:
            await websocket.send_text(f"{data}")

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
