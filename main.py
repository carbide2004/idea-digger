import os
import logging
import arxiv
import requests
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import difflib
from knowledge_base import load_knowledge_base, add_to_knowledge_base, get_from_knowledge_base

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv() # Load environment variables from .env file

class Agent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def run(self, user_idea):
        print("Agent: 正在分析您的想法...")
        analysis_prompt = f"请分析以下用户提出的想法：'{user_idea}'。判断是否需要进行 arXiv 论文检索来补充或验证这个想法。如果需要，请在你的回答最后给出3-5个相关的关键词，这些关键词应该被包装在<keywords></keywords>标签中，用逗号','分隔。如果不需要，请直接回答'不需要检索'。"
        response = self.model.generate_content(analysis_prompt)
        analysis_text = response.text.strip()
        print(f"Agent的原始回答: \n{analysis_text}")

        import re
        keywords_match = re.search(r'<keywords>(.*?)</keywords>', analysis_text, re.DOTALL)
        if keywords_match:
            keywords = [k.strip() for k in keywords_match.group(1).split(',') if k.strip()]
            if not keywords:
                print("Agent: 未能从模型响应中提取到有效关键词，将不进行论文检索。")
                self._brainstorm_with_user(user_idea, [])
                return
            all_analysis_results = []
            for keyword in keywords:
                results = self._paper_search(keyword.strip())
                if not results:
                    print(f"Agent: 未找到与关键词 '{keyword.strip()}' 相关的论文或分析结果。")
                    continue

                for item in results:
                    if item["source"] == "local":
                        all_analysis_results.append(f"本地知识库中论文 '{item['paper_id']}' 的分析结果:\n{item['analysis_result']}")
                    elif item["source"] == "arxiv":
                        analysis_result = self._analyze_paper(item["paper_path"])
                        if analysis_result:
                            all_analysis_results.append(f"论文 '{item['paper_id']}' 分析结果:\n{analysis_result}")
            self._brainstorm_with_user(user_idea, all_analysis_results)
        else:
            self._brainstorm_with_user(user_idea, [])

    def _paper_search(self, query):
        logging.info(f"正在搜索相关论文：{query}")
        local_results = self._local_search(query)
        if local_results:
            return local_results
        arxiv_results = self._arxiv_search(query)
        if arxiv_results:
            return arxiv_results
        return []

    def _local_search(self, query):
        """
        从本地知识库中检索与查询相关的论文分析结果
        
        参数:
            query: 搜索查询字符串
            
        返回:
            包含匹配论文信息的列表，格式为:
            [{"paper_id": str, "analysis_result": str, "source": "local"}, ...]
            如果没有匹配项则返回空列表
        """
        logging.info(f"正在从本地知识库搜索相关论文：{query}")

        kb = load_knowledge_base()
        local_results = []
        for paper_id, analysis_result in kb.items():
            # 使用difflib进行模糊匹配，判断查询字符串与已存储论文标题的相似度
            if difflib.SequenceMatcher(None, query.lower(), paper_id.lower()).ratio() > 0.8:
                logging.info(f"从本地知识库中找到匹配的分析结果：{paper_id}")
                local_results.append({
                    "paper_id": paper_id,
                    "analysis_result": analysis_result,
                    "source": "local"
                })
        logging.info(f"从本地知识库中找到 {len(local_results)} 条匹配结果")
        return local_results

    def _arxiv_search(self, query):
        logging.info(f"正在 arXiv 上搜索相关论文：{query}")
            
        try:
            search = arxiv.Search(
                query=query,
                max_results=5,
                sort_by=arxiv.SortCriterion.Relevance
            )
            papers = []
            for result in search.results():
                papers.append(result)

            if not os.path.exists("papers"):
                os.makedirs("papers")

            arxiv_results = []
            for paper in papers:
                try:
                    filename = f"papers/{paper.title.replace('/', '_')}.pdf"
                    paper.download_pdf(filename=filename)
                    arxiv_results.append({
                        "paper_id": paper.title.replace('/', '_'),
                        "paper_path": filename,
                        "source": "arxiv"
                    })
                    logging.info(f"已下载论文：{filename}")
                except Exception as e:
                    logging.error(f"下载论文 {paper.title} 失败：{e}")
            logging.info(f"从 arXiv 中找到 {len(arxiv_results)} 条匹配结果")
            return arxiv_results
        except Exception as e:
            logging.error(f"arXiv 搜索失败：{e}")
            return []

    def _analyze_paper(self, paper_path):
        print(f"Agent: 正在分析论文 '{paper_path}'...")
        from PyPDF2 import PdfReader

        try:
            reader = PdfReader(paper_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            
            if not text:
                print(f"Agent: 无法从论文 '{paper_path}' 中提取文本。")
                return None

            prompt = f"请分析以下论文内容，指出其主要贡献、方法、结果以及可能的局限性：\n\n{text[:4000]}..."
            response = self.model.generate_content(prompt)
            analysis_result = response.text
            add_to_knowledge_base(paper_path, analysis_result)
            print("Agent: 论文分析完成。")
            return analysis_result
        except Exception as e:
            logging.error(f"分析论文 '{paper_path}' 失败: {e}")
            return None

    def _brainstorm_with_user(self, user_idea, analysis_results):
        print("Agent: 让我们一起头脑风暴，深化您的想法。")
        brainstorm_prompt = f"用户想法：'{user_idea}'\n\n" \
                            f"你之前给出的相关论文分析结果：\n{'' .join(analysis_results) if analysis_results else '无'}\n\n" \
                            "请根据以上信息，指出用户想法的不足之处，并提出如何使其更具新颖性（novelty）和实用性（practicality）的建议。请以对话的形式进行，等待用户反馈。"
        
        response = self.model.generate_content(brainstorm_prompt)
        print(f"Agent: {response.text}")

        while True:
            user_input = input("您的回复（输入'q'结束）：")
            if user_input.lower() == 'q':
                break
            
            follow_up_prompt = f"用户回复：'{user_input}'\n\n请继续进行头脑风暴，深化想法。"
            response = self.model.generate_content(follow_up_prompt)
            print(f"Agent: {response.text}")

if __name__ == "__main__":
    # Replace with your actual API key or load from environment variables
    API_KEY = os.getenv("GOOGLE_API_KEY") 
    if not API_KEY:
        print("请设置 GOOGLE_API_KEY 环境变量。")
    else:
        agent = Agent(API_KEY)
        user_idea = input("请输入您的想法：")
        agent.run(user_idea)