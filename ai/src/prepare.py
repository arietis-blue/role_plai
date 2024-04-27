from pydantic import BaseModel, field_serializer
from openai import OpenAI
from pathlib import Path
import random
from typing import Literal, Optional
from enum import Enum
import uuid
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

start_words = [
    '自己紹介をしてください',
    '好きな技術について教えてください',
    'あなたの強みについて教えてください',
    'あなたの弱みについて教えてください',
    'これまでチームで成し遂げた経験について教えてください',
    'これまでの失敗について教えてください',
    'どのようなチームで働きたいですか',
    'どのような技術を学びたいですか',
    'どのようなプロジェクトに参加したいですか',
    'どのような軸で就職活動をしていますか',
    '将来のキャリアプランについて教えてください',
    'なぜエンジニアになりたいのですか',
    'なぜ当社に入社したいですか',
    '今一番注目している技術について教えてください',
]

class Chara(Enum):
    CANDIDATE = "candidate"
    INTERVIEWER = "interviewer"

    def next(self) -> 'Chara':
        match self:
            case Chara.CANDIDATE:
                return Chara.INTERVIEWER
            case Chara.INTERVIEWER:
                return Chara.CANDIDATE
    
    @property
    def ja(self) -> str:
        match self:
            case Chara.CANDIDATE:
                return "学生"
            case Chara.INTERVIEWER:
                return "面接官"
    
    def infer_role(self, model_chara: "Chara") -> Literal["user", "assistant"]:
        if self == model_chara:
            return "assistant"
        else:
            return "user"


class Reply(BaseModel):
    parent: Optional["Reply"]
    chara: Chara
    id: str
    comment: str
    comment_vector: list[float]
    children: list["Reply"]

    @field_serializer('parent')
    def serialize_dt(self, parent, _info):
        if parent is None:
            return ''
        return parent.id
    
    @property
    def is_root(self) -> bool:
        return self.parent is None

    def from_root(self) -> list["Reply"]:
        """ rootからこれまでのReplyをrootから順にリストにして返す
        """
        _list: list[Reply] = []
        node = self
        while not node.is_root:
            _list.append(node)
            node = node.parent
        _list.append(node)
        return _list[::-1]

    def generate_next(self, context_size: int | None = None) -> "Reply":
        """ 破壊的メソッド
        """
        if context_size is not None:
            raise NotImplementedError("context_size is not implemented yet")
        
        context_replies = self.from_root()
        llm_chara = self.chara.next()
        system_messages = {"role": "system", "content": f"現在新卒エンジニアの就職面接が行われています。あなたは{llm_chara.ja}です。次の会話を踏まえて、適切な返答をしてください。"}
        messages = [system_messages] + [{"role": reply.chara.infer_role(llm_chara), "content": reply.comment} for reply in context_replies]
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        response = chat_completion.choices[0].message.content

        reply = Reply(parent=self, chara=llm_chara, id=str(uuid.uuid4()), comment=response, comment_vector=vectorize(response), children=[])
        self.children.append(reply)
        return reply
    
    @staticmethod
    def generate_root(question: str) -> "Reply":
        return Reply(parent=None, chara=Chara.INTERVIEWER, id=str(uuid.uuid4()), comment=question, comment_vector=vectorize(question), children=[])

    def debug(self, indent: int = 0):
        print(f"{' ' * indent}{self.chara.ja}: {self.comment}")
        for child in self.children:
            child.debug(indent=indent+2)

def vectorize(text: str, fake=False) -> list[float]:
    if fake:
        return [random.random() for _ in range(3)]
    model = "text-embedding-3-small"
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def generate_reply_tree(path: Path, start: str, size: int = 100) -> Reply:
    root = Reply.generate_root(start)
    nodes: list[Reply] = [root]
    while (i:=len(nodes)) < size:
        logger.info(f"Generating {i}/{size}")
        node = random.choice(nodes)
        reply = node.generate_next()
        nodes.append(reply)
    
    s = root.model_dump_json()
    with open(path, '+w') as f:
        f.write(s)
    return root

if __name__ == '__main__':
    root = generate_reply_tree(Path("sample.json"), random.choice(start_words), size=100)
    root.debug()
