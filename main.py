import os
from langchain_tavily import TavilySearch
from langchain_community.tools import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts.prompt import PromptTemplate
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# 工具1：网页搜索工具 (Tavily)
# Tavily 相比普通搜索更适合Agent，它会返回精炼的、适合LLM处理的结果
web_search_tool = TavilySearch(max_results=3, description="用于搜索最新的实时信息、趋势和广泛的公众知识。")

# 工具2：Arxiv 论文检索工具
# 限制只返回最相关的一篇论文的摘要，以提高效率
arxiv_tool = ArxivQueryRun(
    api_wrapper=ArxivAPIWrapper(top_k_results=1, load_max_docs=1),
    description="用于查询和获取特定学术领域的科学论文摘要，尤其是前沿科技和理论研究。"
)

# 工具3：自定义的核心 - 内容分析与Idea挖掘工具
@tool("Content Analyzer and Idea Miner")
def analyze_content(content: str) -> str:
    """
    当获取了足够的信息（例如论文摘要或搜索结果）后，使用此工具进行深度分析。
    输入检索到的文本内容，此工具会分析其核心贡献、潜在局限性，并提出未来可研究的3个具体方向。
    """
    analyzer_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    prompt = f"""
    根据以下内容，请进行深入的“Idea挖掘”分析：
    ---
    {content}
    ---
    
    请严格按照以下结构输出你的分析报告：
    1.  **核心思想 (Core Idea)**: 这份内容的关键信息或论文的核心贡献是什么？
    2.  **潜在局限性 (Limitations)**: 基于现有信息，这个技术、方法或观点可能存在哪些未被提及的缺点或挑战？
    3.  **创新点挖掘 (Idea Mining)**: 请基于其局限性或现有框架，提出3个具体、可执行的、新颖的研究点或改进方向。
    """
    
    response = analyzer_llm.invoke(prompt)
    return response.content

# 将所有工具放入一个列表
tools = [web_search_tool, arxiv_tool, analyze_content]

class Agent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.chat_history = []

        # 初始化LangChain Agent
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        prompt_hub_template = hub.pull("hwchase17/react")
        custom_prompt_template = """
回答以下问题，尽你所能。你有权使用以下工具：

{tools}

使用以下格式：

Question: 你必须回答的输入问题
Thought: 你应该时刻思考该做什么。**在决定行动之前，请先评估问题的性质。如果问题可以用你的通用知识回答，就直接回答。如果需要检索，请判断使用哪个工具更合适（网页搜索用于快速、广泛的信息；Arxiv用于深度、专业的学术信息）。并在思考中说明你选择的理由以及预估这会增加一些处理时间，以体现你在效率和质量间的权衡。**
Action: 应该采取的行动，应为[{tool_names}]中的一个
Action Input: 对行动的输入
Observation: 行动的结果
...（这个Thought/Action/Action Input/Observation的过程可以重复N次）
Thought: 我现在知道最终答案了
Final Answer: 对原始输入问题的最终回答

开始！

Question: {input}
Thought:{agent_scratchpad}
"""
        prompt = PromptTemplate.from_template(custom_prompt_template)
        self.langchain_agent = create_react_agent(llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.langchain_agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def run(self, user_query):
        response = self.agent_executor.invoke({
            "input": user_query,
            "chat_history": self.chat_history
        })
        self.chat_history.append(("user", user_query))
        self.chat_history.append(("agent", response["output"]))
        return response["output"]

if __name__ == "__main__":
    API_KEY = os.getenv("GOOGLE_API_KEY") 
    if not API_KEY:
        print("请设置 GOOGLE_API_KEY 环境变量。")
    else:
        agent = Agent(API_KEY)
        print("欢迎使用Idea挖掘Agent！输入您的问题，或输入 'exit' 退出。")
        while True:
            user_input = input("\n您的问题: ")
            if user_input.lower() == 'exit':
                print("感谢使用，再见！")
                break
            
            try:
                response = agent.run(user_input)
                print("\n--- Agent的回答 ---")
                print(response)
            except Exception as e:
                print(f"发生错误: {e}")
                print("请尝试重新提问。")