from pydantic import BaseModel, field_serializer
from openai import OpenAI
from pathlib import Path
import random
from typing import Literal, Generator, Self
from enum import Enum
import uuid
from loguru import logger
from dotenv import load_dotenv
import json
import numpy as np
import functools
from tqdm import tqdm

load_dotenv()

client = OpenAI()

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
    parent: Self | str | None
    chara: Chara
    id: str
    comment: str
    comment_vector: list[float]
    children: list[Self]

    @field_serializer('parent')
    def serialize_parent(self, parent: Self | str | None):
        """ 循環参照を避けるために、parentをidに変換して保存する
        """
        if parent is None:
            return ''
        elif isinstance(parent, str):
            return parent
        elif isinstance(parent, Reply):
            return parent.id
        else:
            raise ValueError(f"parent is not str or Reply: {parent}")
    
    def __str__(self):
        return f'{self.chara.ja}: {self.comment}'
    
    def __repr__(self):
        return str(self)
    
    @property
    def is_root(self) -> bool:
        return self.parent is None

    def from_root(self) -> list[Self]:
        """ rootからこれまでのReplyをrootから順にリストにして返す
        """
        _list: list[Self] = []
        node = self
        while not node.is_root:
            _list.append(node)
            node = node.parent
        _list.append(node)
        return _list[::-1]

    def generate_next(self, context_size: int | None = None) -> Self:
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
    def generate_root(question: str) -> Self:
        return Reply(parent=None, chara=Chara.INTERVIEWER, id=str(uuid.uuid4()), comment=question, comment_vector=vectorize(question), children=[])

    def debug(self, indent: int = 0):
        print(f"{' ' * indent}{self.chara.ja}: {self.comment}")
        for child in self.children:
            child.debug(indent=indent+2)
    
    def generate_search_function(self):

        # 検索用にデータを準備する
        ids = []
        vectors = []
        charas = []
        id_map: dict[str, Reply] = {}
        for reply in self.bfs():
            ids.append(reply.id)
            vectors.append(reply.comment_vector)
            charas.append(reply.chara)
            id_map[reply.id] = reply
        ids = np.array(ids, dtype=str)
        vectors = np.array(vectors)
        charas = np.array(charas)

        def search(body: str, size: int = 10, allows: list[Chara] = [Chara.CANDIDATE, Chara.INTERVIEWER]) -> list[Self]:
            vector = vectorize(body)

            use_indices = np.where(functools.reduce(lambda x, y: x | y, [charas == allow for allow in allows]))
            scores = np.dot(vectors[use_indices], vector)
            indices = np.argsort(scores)[::-1][:size]
            return [id_map[ids[use_indices][i]] for i in indices]
    
        return search

    def bfs(self) -> Generator[Self, None, None]:
        queue = [self]
        while queue:
            node = queue.pop(0)
            yield node
            queue.extend(node.children)
    
    def save(self, path: Path):
        with open(path, '+w') as f:
            f.write(self.model_dump_json())
    

    @staticmethod
    def load(path: Path) -> "Reply":
        with open(path, 'r') as f:
            j = json.load(f)

        root = Reply.model_validate(j)

        # parentが参照ではなく、idで指定されているので、idから参照を復元する
        id_map: dict[str, Reply] = {}
        for reply in root.bfs():
            id_map[reply.id] = reply
            if reply.parent is not None:
                reply.parent = id_map[reply.id]
        
        return root

def vectorize(text: str, fake=False) -> list[float]:
    if fake:
        return [random.random() for _ in range(3)]
    model = "text-embedding-3-small"
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def generate_reply_tree(path: Path, start: str, size: int = 100) -> Reply:
    root = Reply.generate_root(start)
    nodes: list[Reply] = [root]
    with tqdm(total=size-1) as pbar:
        while len(nodes) < size:
            pbar.update(1)
            node = random.choice(nodes)
            reply = node.generate_next()
            nodes.append(reply)
    
    s = root.model_dump_json()
    with open(path, '+w') as f:
        f.write(s)
    return root

if __name__ == '__main__':

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

    # データ生成
    # root = generate_reply_tree(Path("sample2.json"), random.choice(start_words), size=3)
    # root.debug()

    # データ検索
    root = Reply.load(Path("ai/sample2.json"))
    search = root.generate_search_function()
    results = search("私は学生です", allows=[Chara.CANDIDATE])
    for results in results:
        print(results)
