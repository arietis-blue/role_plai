from fire import Fire
from datetime import datetime
from data import generate_reply_tree
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

def search():
    ...

if __name__ == "__main__":
    Fire({
        'generate': generate,
        'search': search,
    })