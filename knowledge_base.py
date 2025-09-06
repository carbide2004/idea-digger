import json
import os

KNOWLEDGE_BASE_FILE = "knowledge_base.json"

def load_knowledge_base():
    """加载本地论文知识库。"""
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        with open(KNOWLEDGE_BASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_knowledge_base(kb):
    """保存本地论文知识库。"""
    with open(KNOWLEDGE_BASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=4)

def add_to_knowledge_base(paper_id, analysis_result):
    """将论文分析结果添加到知识库。"""
    kb = load_knowledge_base()
    kb[paper_id] = analysis_result
    save_knowledge_base(kb)

def get_from_knowledge_base(paper_id):
    """从知识库获取论文分析结果。"""
    kb = load_knowledge_base()
    return kb.get(paper_id)