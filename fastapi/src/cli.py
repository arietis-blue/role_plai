from fire import Fire
from datetime import datetime
from data import generate_reply_tree, Reply, Chara
from pathlib import Path
from loguru import logger

def generate(start_question: str, size: int=100):
    """ start_question から始まるReplyツリーを生成します
    """
    now_str = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f'{now_str}.json'
    logger.info(f"{filename} にデータを生成します")
    root = generate_reply_tree(Path(filename), start_question, size)
    root.debug()

def search(path: str, query: str, size: int=5, only_candidate: bool=False, only_interviewer: bool=False):
    """ path に保存されたReplyツリーを読み込み、queryに対する応答を返します
    """

    if only_candidate and only_interviewer:
        raise ValueError("only_candidate と only_interviewer は同時に指定できません")
    
    if only_candidate:
        allows = [Chara.CANDIDATE]
    elif only_interviewer:
        allows = [Chara.INTERVIEWER]
    else:
        allows = [Chara.CANDIDATE, Chara.INTERVIEWER]
    root = Reply.load(Path(path))
    search = root.generate_search_function()
    replies = search(query, size=size, allows=allows)
    for reply in replies:
        logger.success(str(reply))

if __name__ == "__main__":
    Fire({
        'generate': generate,
        'search': search,
    })