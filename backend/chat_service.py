from database_handler import DatabaseHandler
from llm_handler import LLMHandler
import requests

class ChatService:
    def __init__(self, db_handler: DatabaseHandler, llm_handler: LLMHandler, serpapi_key: str):
        self.db_handler = db_handler
        self.llm_handler = llm_handler
        self.serpapi_key = serpapi_key

    def web_search_snippets(self, query: str, num_results: int = 3) -> str:
        try:
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "engine": "google",
                "num": num_results
            }
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            snippets = []
            for result in data.get("organic_results", [])[:num_results]:
                snippet = result.get("snippet") or result.get("title")
                if snippet:
                    snippets.append(snippet)
            return "\n".join(snippets)
        except Exception as e:
            print(f"Web search error: {e}")
            return ""

    def chat(self, user_msg, session_id, username, user_id):
        # 1. Retrieve chat history (if needed)
        conversation = self.db_handler.get_conversation(session_id, user_id)
        if not conversation:
            conversation = self.db_handler.create_conversation(session_id, user_id)
        messages = self.db_handler.get_conversation_messages(conversation.id)
        # 2. Perform web search
        web_context = self.web_search_snippets(user_msg)
        # 3. Build context
        if web_context:
            context = f"Relevant web information:\n{web_context}\n---\nUser question: {user_msg}"
        else:
            context = user_msg
        # 4. Call LLMHandler
        response_text = self.llm_handler.generate_response(context)
        # 5. Save messages
        self.db_handler.save_message(conversation.id, "user", user_msg)
        self.db_handler.save_message(conversation.id, "assistant", response_text)
        self.db_handler.update_conversation_activity(conversation)
        # 6. Return response and history
        return response_text, messages 