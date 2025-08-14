import google.generativeai as genai
import json
from typing import List, Dict, Any, Optional


class Gemini:
    def __init__(self, model: str, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

    def add_user_message(self, messages: list, message):
        user_message = {
            "role": "user",
            "content": message if isinstance(message, str) else str(message),
        }
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message):
        assistant_message = {
            "role": "assistant",
            "content": message if isinstance(message, str) else str(message),
        }
        messages.append(assistant_message)

    def text_from_message(self, message):
        if hasattr(message, 'text'):
            return message.text
        elif isinstance(message, str):
            return message
        else:
            return str(message)

    def _convert_messages_to_gemini_format(self, messages: List[Dict]) -> List[Dict]:
        """Convert messages to Gemini format"""
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]
            
            if isinstance(content, list):
                # Handle tool results and complex content
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") == "tool_result":
                            text_parts.append(f"Tool result: {part.get('content', '')}")
                        else:
                            text_parts.append(str(part))
                    else:
                        text_parts.append(str(part))
                content = " ".join(text_parts)
            
            gemini_messages.append({
                "role": role,
                "parts": [{"text": content}]
            })
        
        return gemini_messages

    def _convert_tools_to_gemini_format(self, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """Convert MCP tools to Gemini function calling format"""
        if not tools:
            return None
        
        gemini_tools = []
        for tool in tools:
            function_declaration = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
            gemini_tools.append({"function_declaration": function_declaration})
        
        return gemini_tools

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ):
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # Prepare generation config
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": 8000,
            }
            
            if stop_sequences:
                generation_config["stop_sequences"] = stop_sequences

            # Create chat session
            chat = self.model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            
            # Get the last message (current user input)
            current_message = gemini_messages[-1]["parts"][0]["text"] if gemini_messages else ""
            
            # Add system prompt if provided
            if system:
                current_message = f"System: {system}\n\nUser: {current_message}"

            # Handle tools
            if tools:
                gemini_tools = self._convert_tools_to_gemini_format(tools)
                if gemini_tools:
                    # For now, we'll include tool info in the prompt
                    tools_info = "\n\nAvailable tools:\n"
                    for tool in tools:
                        tools_info += f"- {tool['name']}: {tool['description']}\n"
                    current_message += tools_info

            # Generate response
            response = chat.send_message(
                current_message,
                generation_config=generation_config
            )
            
            # Create a response object that mimics Anthropic's format
            class GeminiResponse:
                def __init__(self, text_content):
                    self.text = text_content
                    self.content = [{"type": "text", "text": text_content}]
                    self.stop_reason = "end_turn"
            
            return GeminiResponse(response.text)
            
        except Exception as e:
            print(f"Error in Gemini chat: {e}")
            # Return a default response in case of error
            class ErrorResponse:
                def __init__(self, error_msg):
                    self.text = f"Sorry, I encountered an error: {error_msg}"
                    self.content = [{"type": "text", "text": self.text}]
                    self.stop_reason = "error"
            
            return ErrorResponse(str(e))
