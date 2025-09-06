import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv() # Load environment variables from .env file

class Agent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def run(self, user_idea):
        print("Agent: 正在分析您的想法...")
        analysis_prompt = f"请分析以下用户提出的想法：'{user_idea}'。判断是否需要进行 arXiv 论文检索来补充或验证这个想法。如果需要，请给出3-5个相关的关键词，用逗号','分隔。如果不需要，请直接回答'不需要检索'。"
        response = self.model.generate_content(analysis_prompt)
        analysis_text = response.text.strip()
        print(f"Agent: {analysis_text}")

        if "不需要检索" not in analysis_text:
            keywords = analysis_text.split(',')
            all_analysis_results = []
            for keyword in keywords:
                papers = self._arxiv_search(keyword.strip())
                for paper in papers:
                    pdf_filename = f"papers/{paper.title.replace('/', '_')}.pdf"
                    analysis = self._analyze_paper(pdf_filename)
                    if analysis:
                        all_analysis_results.append(f"论文 '{paper.title}' 分析结果:\n{analysis}")
            self._brainstorm_with_user(user_idea, all_analysis_results)
        else:
            self._brainstorm_with_user(user_idea, [])

    def _arxiv_search(self, query, max_results=5):
        print(f"Agent: 正在 arXiv 上搜索 '{query}'...")
        import arxiv
        import requests

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers = []
        for result in search.results():
            papers.append(result)
            print(f"Agent: 找到论文: {result.title}")
            # Download PDF
            try:
                pdf_url = result.pdf_url
                response = requests.get(pdf_url)
                pdf_filename = f"papers/{result.title.replace('/', '_')}.pdf"
                os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)
                with open(pdf_filename, 'wb') as f:
                    f.write(response.content)
                print(f"Agent: 已下载论文到 {pdf_filename}")
            except Exception as e:
                logging.error(f"下载论文 {result.title} 失败: {e}")
        return papers

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
            print("Agent: 论文分析完成。")
            return response.text
        except Exception as e:
            logging.error(f"分析论文 '{paper_path}' 失败: {e}")
            return None

    def _brainstorm_with_user(self, user_idea, analysis_results):
        print("Agent: 让我们一起头脑风暴，深化您的想法。")
        brainstorm_prompt = f"用户想法：'{user_idea}'\n\n" \
                            f"相关论文分析结果：\n{'' .join(analysis_results) if analysis_results else '无'}\n\n" \
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