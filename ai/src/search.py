import prepare
import json
from pydantic import BaseModel

# class Reply(BaseModel):
#     parent: str | None
#     chara: prepare.Chara
#     id: str
#     comment: str
#     comment_vector: list[float]
#     children: list["Reply"]

parent_dict = {}
class UniReply(prepare.Reply):
    parent: str | None
    children: list["UniReply"]

    def connect(self) -> prepare.Reply:
        reply = prepare.Reply(
            parent=None if self.parent=='' else parent_dict[self.parent],
            chara=self.chara,
            id=self.id,
            comment=self.comment,
            comment_vector=self.comment_vector,
            children=[]
        )
        parent_dict[self.id] = reply
        reply.children = [child.connect() for child in self.children]

        return reply

if __name__ == '__main__':
    with open('data/sample.json', 'r') as f:
        j = json.load(f)
    print(j)
    ur = UniReply.model_validate(j)
    ur.connect()
    # generate_reply_tree(Path("ai/data/reply_tree.json"), "こんにちは", size=100)
    pass