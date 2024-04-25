from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship 

Base = declarative_base()


class HumanResponses(Base):
    __tablename__ = 'human_responses'

    response_id = Column(Integer, primary_key=True, index=True)
    expected_response = Column(Text)

    follow_up_questions = relationship("AIFollowUpQuestions", back_populates="human_response")


class AIFollowUpQuestions(Base):
    __tablename__ = 'ai_follow_up_questions'

    follow_up_id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("human_responses.response_id"))
    follow_up_question = Column(Text)

    human_response = relationship("HumanResponses", back_populates="follow_up_questions")

DATABASE_URL = "postgresql://postgres:postgres@db/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# テーブルが存在しない場合は作成
Base.metadata.create_all(bind=engine)