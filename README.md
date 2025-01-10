# CodeTalk 🤖

[![Streamlit App](https://github.com/vedpatil1345/Code-explainer/blob/main/screenshot1.png)](https://codetalk.streamlit.app)
[![Streamlit App](https://github.com/vedpatil1345/Code-explainer/blob/main/screenshot2.png)](https://codetalk.streamlit.app)

CodeTalk is an interactive code analysis and error explanation tool powered by LLM technology. It helps developers understand, debug, and improve their code through intelligent analysis and natural language conversation.

## ✨ Features

- **Code Analysis**: Get detailed explanations of your code's purpose, structure, and functionality
- **Error Explanation**: Understand and fix error messages with context-aware solutions
- **Interactive Chat**: Discuss your code and errors with an AI assistant
- **Multi-Language Support**: Supports Python, JavaScript, Java, and C++
- **Real-time Analysis**: Get instant feedback on your code
- **Comprehensive Reports**: Receive detailed analysis including:
  - Code explanation
  - Requirements analysis
  - Error detection
  - Improvement suggestions

## 🚀 Live Demo

Try out CodeTalk at: [https://code-explainer-107.streamlit.app](https://code-explainer-107.streamlit.app)

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **LLM Integration**: Groq API (llama-3.2-90b-vision-preview model)
- **Code Execution**: Supports multiple language runtimes
- **Additional Libraries**:
  - `langchain_groq`
  - `execjs`
  - `streamlit.components.v1`
  - `dotenv`

## 🔧 Setup & Installation

1. Clone the repository:
```bash
git clone https://github.com/vedpatil1345/Code-explainer.git
cd Code-explainer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root and add your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```
Or Add Groq API Key when you run app first time:
   [![Streamlit App](https://github.com/vedpatil1345/Code-explainer/blob/main/screenshot3.png)](https://codetalk.streamlit.app)
  
4. Run the application:
```bash
streamlit run app.py
```

## 💡 Usage

### Code Analysis Tab
1. Select your programming language
2. Paste your code in the text area
3. Click "Analyze Code" to get comprehensive insights
4. Use the chat interface to ask specific questions about your code

### Error Explainer Tab
1. Paste your error message
2. (Optional) Add relevant code context
3. Click "Analyze Error" to receive:
   - Detailed error explanation
   - Step-by-step solutions
   - Common pitfalls to avoid
   - Related resources
4. Use the chat interface to get clarification on the error analysis

## 🔒 Security

- Restricted execution environment for code analysis
- Secure API key handling
- Sandboxed code execution

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## ⭐ Support

If you find this project helpful, please consider giving it a star on GitHub!
