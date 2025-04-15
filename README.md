# CortexIA

A Telegram bot that helps you manage notes, ideas, and projects with AI assistance.

## Features

- Create and manage notes
- Generate ideas with AI assistance
- Organize projects with multiple notes
- Refine text using AI
- Interactive menus for easy navigation

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`:
   ```
   BOT_TOKEN=your_bot_token_here
   AUTHORIZED_USER_ID=your_user_id_here
   OLLAMA_HOST=your_AI_host_link_here
   BASE_DIR=/path/to/your/notes/directory
   ```
4. Set up Ollama:
   - Install [Ollama](https://ollama.ai/)
   - Run the Ollama server
   - Pull the model: `ollama pull mistral`

5. Run the bot:
   ```
   python assistent.py
   ```

## Usage

- `/start` - Start the bot
- `/help` - Get help on how to use the bot
- Use the interactive menus to navigate through notes, ideas, and projects

## Security

- Only authorized users can use the bot
- Sensitive information is stored in environment variables
- Notes and projects are stored locally

## License

MIT 
