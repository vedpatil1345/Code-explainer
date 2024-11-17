import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, Callable, Optional
import subprocess
import os
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import execjs
from functools import lru_cache
from dotenv import load_dotenv,set_key

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "c++"

@dataclass
class Message:
    content: str
    is_bot: bool = False

class CodeExecutor:
    @staticmethod
    def execute_python(code: str) -> str:
        try:
            # Use restricted globals for safety
            restricted_globals = {
                '__builtins__': {
                    name: __builtins__[name]
                    for name in ['print', 'len', 'str', 'int', 'float', 'list', 'dict']
                }
            }
            exec(code, restricted_globals)
            return "Code executed successfully."
        except Exception as e:
            logger.error(f"Python execution error: {str(e)}")
            return f"Error: {str(e)}"

    @staticmethod
    def execute_javascript(code: str) -> str:
        try:
            return str(execjs.eval(code))
        except Exception as e:
            logger.error(f"JavaScript execution error: {str(e)}")
            return f"Error: {str(e)}"

    @staticmethod
    def execute_compiled_language(code: str, extension: str, compiler_cmd: list, cleanup_files: list) -> str:
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        source_file = temp_dir / f"Example{extension}"
        try:
            # Write code to file
            source_file.write_text(code)
            
            # Compile
            compile_process = subprocess.run(
                compiler_cmd, 
                capture_output=True, 
                text=True, 
                cwd=temp_dir
            )
            
            if compile_process.returncode != 0:
                return f"Compilation error: {compile_process.stderr}"
            
            # Run
            run_cmd = ["./Example"] if extension == ".cpp" else ["java", "Example"]
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=5,
                cwd=temp_dir
            )
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            return "Error: Execution timed out"
        except Exception as e:
            logger.error(f"Compilation/execution error: {str(e)}")
            return f"Error: {str(e)}"
        finally:
            # Cleanup
            for file in cleanup_files:
                try:
                    (temp_dir / file).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Cleanup error for {file}: {str(e)}")

class CodeAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        # Try to get API key from environment variable if not provided
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ API key not found. Please set it in .env file or pass it directly.")
            
        self.llm = ChatGroq(
            model="llama-3.2-90b-vision-preview",
            groq_api_key=self.api_key,
            temperature=0.9,
            max_tokens=2048
        )
        
    @lru_cache(maxsize=100)
    def analyze_code(self, code: str, language: str) -> Dict[str, str]:
        """Analyze code with caching for improved performance"""
        return {
            '👨🏻‍💻Code-Explanation': self.explain_code(code, language),
            '📋Requirements Analysis': self.get_requirements(code),
            '⚠ Error Detection': self.get_error(code, language),
            '💪Code Improvement': self.get_improvements(code, language)
        }
    
    def explain_code(self, code: str, language: str) -> str:
        template = """
        As an AI code assistant, please provide a detailed explanation of this {language} code:
        
        {code}
        
        Focus on:
        1. Overall purpose
        2. Key components
        3. Logic flow
        4. Important functions/methods
        """
        return self._get_llm_response(template, code=code, language=language)
    
    def get_requirements(self, code: str) -> str:
        template = """
        List all requirements needed to run this code:
        
        {code}
        
        Include:
        1. Dependencies
        2. Environment setup
        3. System requirements
        4. Prerequisites
        """
        return self._get_llm_response(template, code=code)
    
    def get_error(self, code: str, language: str) -> str:
        template = """
        Analyze this {language} code for potential errors:
        
        {code}
        
        Consider:
        1. Syntax errors
        2. Logic errors
        3. Common pitfalls
        4. Edge cases
        """
        return self._get_llm_response(template, code=code, language=language)
    
    def get_improvements(self, code: str, language: str) -> str:
        template = """
        Suggest improvements for this {language} code:
        
        {code}
        
        Focus on:
        1. Performance
        2. Readability
        3. Best practices
        4. Security
        """
        return self._get_llm_response(template, code=code, language=language)
    
    def _get_llm_response(self, template: str, **kwargs) -> str:
        try:
            prompt = PromptTemplate.from_template(template)
            return self.llm.predict(prompt.format(**kwargs))
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            return f"Analysis failed: {str(e)}"


class CodeTalkApp:
    def __init__(self):
        self.initialize_session_state()
        
        # Handle API key input if not found in environment
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            if 'api_key' not in st.session_state:
                st.session_state.api_key = None
                
            if not st.session_state.api_key:
                api_key = st.text_input("Enter your GROQ API key:", type="password")
                if api_key:
                    with open(".env", "w") as file:
                        file.write(f"GROQ_API_KEY = {api_key}")
                    st.session_state.api_key = api_key
                    st.success("API key saved for this session!")
                    st.rerun()
                return
            
            api_key = st.session_state.api_key
            
        try:
            self.code_analyzer = CodeAnalyzer(api_key)
        except Exception as e:
            st.error(f"Error initializing code analyzer: {str(e)}")
            return
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        defaults = {
            'messages': [],
            'code': "",
            'error': "",
            'analysis_results': None,  # New session state variable for analysis results
            'theme': 'light',
            'language': CodeLanguage.PYTHON.value,
            'chat_history': [],
            'current_code': ""  # New session state variable for current code
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def render_code_analysis_tab(self):
        code_col, chat_col = st.columns([1, 1])
        
        with code_col:
            st.header("Code Analysis")
            selected_language = st.selectbox(
                "Select Code Language",
                [lang.value for lang in CodeLanguage],
                key="language_selector"
            )
            
            code_input = st.text_area("Enter your code here:", height=200, key="code_input")
            
            if st.button("Analyze Code") and code_input:
                # Store the current code and analysis results in session state
                st.session_state.current_code = code_input
                st.session_state.analysis_results = self.code_analyzer.analyze_code(code_input, selected_language)
            
            # Display analysis results if they exist
            if st.session_state.analysis_results:
                for title, content in st.session_state.analysis_results.items():
                    with st.expander(title):
                        st.write(content)
        
        with chat_col:
            self.render_chat_interface()
    
    def render_error_tab(self):
        # Split into two columns
        error_col, chat_col = st.columns([1, 1])
        
        with error_col:
            st.header("Error Explainer")
            error_input = st.text_area("Paste your error message here:", height=100)
            st.markdown("### original Code(Optional)")
            code_context = st.text_area("Optional: Paste relevant code for better context", height=150)
            
            if st.button("Analyze Error") and error_input:
                # Store current error context
                st.session_state.current_error = {
                    'message': error_input,
                    'code_context': code_context
                }
                
                # Generate comprehensive error analysis
                analysis = self.analyze_error_comprehensive(error_input, code_context)
                
                # Display analysis in expandable sections
                with st.expander("🔍 Error Explanation", expanded=True):
                    st.markdown(analysis['explanation'])
                
                with st.expander("🛠️ Solution Steps"):
                    st.markdown(analysis['solution'])
                    
                with st.expander("🚫 Common Pitfalls"):
                    st.markdown(analysis['pitfalls'])
                    
                with st.expander("📚 Related Resources"):
                    st.markdown(analysis['resources'])
        
        with chat_col:
            st.header("Chat about the Error")
            # Display error-specific chat history
            if 'error_chat_history' not in st.session_state:
                st.session_state.error_chat_history = []
                
            for message in st.session_state.error_chat_history:
                with st.chat_message("assistant" if message.is_bot else "user"):
                    st.markdown(message.content)
            
            # Chat input
            user_message = st.chat_input("Ask about the error...")
            if user_message:
                # Add user message to history
                st.session_state.error_chat_history.append(Message(user_message, is_bot=False))
                
                # Generate context-aware response
                error_context = f"""
                Error message: {st.session_state.get('current_error', {}).get('message', '')}
                Code context: {st.session_state.get('current_error', {}).get('code_context', '')}
                Chat history: {[m.content for m in st.session_state.error_chat_history[-5:] if not m.is_bot]}
                Current question: {user_message}
                """
                
                response = self.code_analyzer._get_llm_response(
                    "Given this error context:\n{context}\n\nProvide a helpful, specific response addressing the user's question.",
                    context=error_context
                )
                
                # Add bot response to history
                st.session_state.error_chat_history.append(Message(response, is_bot=True))
                st.rerun()

    def analyze_error_comprehensive(self, error_message: str, code_context: str = "") -> Dict[str, str]:
        """Provide comprehensive error analysis with multiple aspects"""
        
        # Create context-aware prompt
        base_context = f"""Error message: {error_message}"""
        if code_context:
            base_context += f"\nRelated code:\n{code_context}"
        
        # Generate explanation
        explanation_prompt = f"""
        {base_context}
        
        Provide a clear, detailed explanation of this error in markdown format, including:
        1. What the error means in simple terms
        2. The specific part of the code causing the error (if code is provided)
        3. The underlying programming concept related to this error
        """
        
        # Generate solution steps
        solution_prompt = f"""
        {base_context}
        
        Provide step-by-step solutions in markdown format:
        1. Immediate fix steps
        2. Alternative approaches
        3. How to verify the fix worked
        """
        
        # Generate common pitfalls
        pitfalls_prompt = f"""
        {base_context}
        
        List in markdown format:
        1. Common mistakes that lead to this error
        2. Similar errors to watch out for
        3. Prevention tips
        """
        
        # Generate related resources
        resources_prompt = f"""
        {base_context}
        
        Provide in markdown format:
        1. Related documentation links
        2. Recommended learning resources
        3. Similar error patterns to study
        """
        
        return {
            'explanation': self.code_analyzer._get_llm_response(explanation_prompt),
            'solution': self.code_analyzer._get_llm_response(solution_prompt),
            'pitfalls': self.code_analyzer._get_llm_response(pitfalls_prompt),
            'resources': self.code_analyzer._get_llm_response(resources_prompt)
        }
    
    def render_chat_interface(self):
        st.header("Chat About The Code")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message("assistant" if message.is_bot else "user"):
                st.markdown(message.content)
        
        # Chat input
        user_message = st.chat_input("Ask a question about your code:")
        if user_message:
            # Include current code context in the chat
            context = f"Given this code:\n\n{st.session_state.current_code}\n\nUser question: {user_message}"
            self.handle_chat_message(context)
            st.rerun()
    
    def handle_chat_message(self, message: str):
        # Store only the user's question in chat history, not the code context
        user_question = message.split("User question: ")[-1]
        st.session_state.chat_history.append(Message(user_question, is_bot=False))
        
        response = self.code_analyzer._get_llm_response(
            "{message}\nResponse:",
            message=message
        )
        st.session_state.chat_history.append(Message(response, is_bot=True))
        
        # Add custom styling
    def run(self):
        st.set_page_config(page_title="CodeTalk", layout="wide")
    
        # Add custom styling with animation
        st.markdown("""
        
<style>
        /* Reset default styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
}

/* Hide Streamlit header */
header {
    visibility: hidden;
}

/* Background layers container */
.background-container {
    position: fixed;  /* Changed to fixed to cover full viewport */
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: -1;
}
.top-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: linear-gradient(to bottom,
                rgba(64, 64, 64, 0.8) 0%,
                rgba(64, 64, 64, 0.5) 50%,
                rgba(64, 64, 64, 0) 100%);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            z-index: 1000;
        }
/* Background animation layer */
.animation {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 0;
}

/* Background gradient overlay */
.app-bg {
    position: absolute;
    top: 60px;
    left: 30px;
    right:30px;
    height: 100%;
    background: linear-gradient(
        145deg,
        rgba(64, 64, 64, 0.60) 0%,
        rgba(64, 64, 64, 0.65) 40%,
        rgba(64, 64, 64, 0.70) 100%
    );
    align-self: center;
    justify-content: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 25px;
    backdrop-filter: blur(2px);
    z-index: 1;
}

        
        /* Main app container */
        .stApp {
            top: -50px;
            background-color: rgba(0, 0, 0, 0.4);
            z-index: 2;
            left: 30px;
            right: 30px;
        }
        
        /* Custom container styling */
        .css-1d391kg, .css-1n76uvr {
            background-color: rgba(0, 0, 0, 0.45);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        /* Input fields styling */
        .stTextInput input, .stTextArea textarea {
            background-color: rgba(255, 255, 255, 0.05);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Button styling */
        .stButton button {
            background-color: #4a4a4a;
            color: white;
            border: none;
        }
        
        /* Text color for all markdown and headings */
        .stMarkdown, p, h1, h2, h3 {
            color: white !important;
        }   
    </style>
        """, unsafe_allow_html=True)

            
        st.markdown("""<div class="top-bar"></div><div class="background-container"><iframe class="animation" src="https://melodic-kataifi-1ba173.netlify.app"></iframe><div class="app-bg"></div></div>""",unsafe_allow_html=True)
        
        st.markdown("# CodeTalk")
    
    # Rest of your code...
        
        if not hasattr(self, 'code_analyzer'):
            return
        
        tab1, tab2 = st.tabs(["💻 Code Analysis", "⚠️ Error Explainer"])
        
        with tab1:
            self.render_code_analysis_tab()
        with tab2:
            self.render_error_tab()
        st.markdown("""</div>""",unsafe_allow_html=True)

if __name__ == "__main__":
    app = CodeTalkApp()
    app.run()
