from fastapi import FastAPI, WebSocket, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, HumanResponses, AIFollowUpQuestions
from pydantic import BaseModel

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
        responses = search(path=data_path, query=data, size=3, only_interviewer=True)
        response = random.choice(responses)
        # responseの頭に含まれる「面接官: 」を取り除く
        response  = str(response).replace("面接官: ", "")
        await websocket.send_text(f"{response}")


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
