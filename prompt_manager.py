import json
import os
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = os.getenv('BASE_DIR', os.path.join(os.path.dirname(__file__), 'data'))

class PromptManager:
    """Manager for prompts and context for the AI"""
    
    def __init__(self, base_dir=BASE_DIR):
        """Initializes the prompt manager"""
        self.base_dir = base_dir
        self.prompts_dir = os.path.join(base_dir, "prompts")
        
        # JSON file for storing prompts
        self.prompts_file = os.path.join(base_dir, "prompts.json")
        
        # Ensure necessary directories exist
        self._ensure_directories()
        
        # Initialize JSON file if it doesn't exist
        if not os.path.exists(self.prompts_file):
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        
        # Prompt and context files
        self.base_prompt_file = os.path.join(self.prompts_dir, "base_prompt.json")
        self.context_file = os.path.join(self.prompts_dir, "context.json")
        
        # Load base prompt and context
        self.base_prompt = self._load_json(self.base_prompt_file)
        self.context = self._load_json(self.context_file)
    
    def _ensure_directories(self):
        """Ensures that necessary directories exist"""
        os.makedirs(self.prompts_dir, exist_ok=True)
    
    def _load_json(self, file_path: str) -> Dict:
        """Loads a JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_prompt(self, additional_context: Optional[Dict] = None) -> Dict:
        """Gets the complete prompt with current context"""
        prompt = self.base_prompt.copy()
        
        if additional_context:
            context_str = "\n".join([f"{k}: {v}" for k, v in additional_context.items() if v])
            if context_str:
                prompt["content"] += f"\n\nCurrent context:\n{context_str}"
        
        return prompt
    
    def update_base_prompt(self, new_content: str) -> bool:
        """Updates the base prompt content"""
        try:
            self.base_prompt["content"] = new_content
            with open(self.base_prompt_file, 'w', encoding='utf-8') as f:
                json.dump(self.base_prompt, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error updating base prompt: {str(e)}")
            return False
    
    def set_context(self, key: str, value: any) -> bool:
        """Sets a value in the context"""
        try:
            self.context[key] = value
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error updating context: {str(e)}")
            return False
    
    def clear_context(self) -> bool:
        """Clears the current context"""
        try:
            self.context = {}
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error clearing context: {str(e)}")
            return False
    
    def _get_default_base_prompt(self) -> Dict:
        """Gets the default base prompt"""
        return {
            "role": "system",
            "content": """You are an intelligent and friendly personal assistant. Your goal is to help the user in a natural and effective way.

You have access to the following functionalities:
1. Notes: You can create, read and analyze notes
2. Journal: You can create and read journal entries
3. Ideas: You can save and develop ideas
4. Projects: You can organize notes in projects

When the user sends you a message:
1. Analyze the context and intention of the message
2. If it's a question or information request, respond directly
3. If it's a note, idea or journal entry, suggest saving it using the appropriate command
4. If it's a task or project, help organize it
5. If you need more information, ask specific questions

IMPORTANT - Language handling:
- ALWAYS respond in the language used by the user in their message
- If the user writes in Spanish, respond in Spanish
- If the user writes in English, respond in English
- If the user specifically requests a language (e.g., "respond in english"), respond in that language
- Maintain the same language throughout the conversation until the user changes it

Current context:
{context}

Remember:
- Be concise but informative
- Suggest actions when appropriate
- Maintain conversation context
- Use emojis moderately to make the conversation more friendly."""
        }

    def get_complete_prompt(self) -> str:
        """Gets the complete prompt with current context"""
        try:
            # Load base prompt
            with open(self.base_prompt_file, 'r', encoding='utf-8') as f:
                base_prompt = json.load(f)
            
            # Load context
            with open(self.context_file, 'r', encoding='utf-8') as f:
                context = json.load(f)
            
            # Format base prompt with context
            complete_prompt = base_prompt['content'].format(
                context=json.dumps(context, indent=2, ensure_ascii=False)
            )
            
            return complete_prompt
            
        except Exception as e:
            logger.error(f"Error getting complete prompt: {str(e)}")
            # In case of error, return a basic prompt
            return """You are an intelligent and friendly personal assistant.
Respond naturally and helpfully to the user.
Maintain a conversational but professional tone.""" 