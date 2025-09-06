# Idea Digger

Idea Digger 是一个基于 Gemini 模型的智能代理，旨在帮助用户探索和分析新的想法。它可以根据用户的输入，智能地判断是否需要检索 arXiv 上的相关论文，并对论文进行分析，最终与用户进行互动式的头脑风暴，提供有价值的见解和建议。

## 功能

- **智能想法分析**：根据用户输入的想法，利用 Gemini 模型进行初步分析。
- **本地知识库**：Agent 会优先在本地知识库中查找已分析的论文，提高效率。
- **arXiv 论文检索**：如果本地知识库中没有匹配的论文，Agent 会自动检索 arXiv 上的相关论文。
- **论文内容分析**：下载并分析检索到的 PDF 论文内容，提取关键信息。
- **交互式头脑风暴**：与用户进行多轮对话，共同探讨想法，提供新的视角和建议。
- **实时状态显示**：在终端实时显示 Agent 的工作状态，让用户了解当前进展。
- **错误处理与日志记录**：完善的错误处理机制和日志记录，方便问题排查。

## 安装

1. **克隆仓库**：

   ```bash
   git clone <your-repository-url>
   cd idea_digger
   ```

2. **创建并激活虚拟环境**：

   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**：

   ```bash
   pip install -r requirements.txt
   ```

## 配置 API 密钥

1. **获取 Gemini API 密钥**：
   访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取您的 `GOOGLE_API_KEY`。

2. **创建 `.env` 文件**：
   在项目根目录下创建名为 `.env` 的文件，并添加您的 API 密钥：

   ```
   GOOGLE_API_KEY=YOUR_API_KEY_HERE
   ```
   请将 `YOUR_API_KEY_HERE` 替换为您的实际 API 密钥。

## 使用方法

运行 `main.py` 文件：

```bash
python main.py
```

程序启动后，您将被提示输入您的想法。Agent 将根据您的输入进行分析，并可能进行论文检索和头脑风暴。

## 示例交互

```
请输入您的想法：开发一个基于AI的智能家居系统，可以根据用户习惯自动调节室内环境。
Agent 正在分析您的想法...
Agent 认为您的想法需要进行 arXiv 论文检索。正在提取关键词...
提取到的关键词：智能家居, AI, 自动调节, 用户习惯
正在 arXiv 上搜索相关论文...
已下载论文：...
正在分析论文内容...
分析完成。现在开始头脑风暴。
Agent: 这是一个很有趣的想法！我们可以从以下几个方面来深入探讨：...
您：...
```

## 文件结构

```
.env
.gitignore
main.py
papers/
├── ... (下载的论文)
knowledge_base.py
knowledge_base.json
requirements.txt
README.md
```

## 许可证

MIT License

## 贡献

欢迎贡献！如果您有任何建议或发现 Bug，请提交 Issue 或 Pull Request。