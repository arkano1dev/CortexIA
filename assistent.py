import os
import logging
import json
import shortuuid
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import requests
from prompt_manager import PromptManager

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
AUTHORIZED_USER_ID = int(os.getenv('AUTHORIZED_USER_ID'))
OLLAMA_HOST = os.getenv('OLLAMA_HOST')
BASE_DIR = os.getenv('BASE_DIR', os.path.join(os.path.dirname(__file__), 'data'))

# Lista de usuarios autorizados
ALLOWED_USERS = [AUTHORIZED_USER_ID]

# Global variables for user states
user_states = {}  # Dictionary to store each user's state

class NoteManager:
    """Manager for notes and projects"""
    
    def __init__(self, base_dir=BASE_DIR):
        """Initializes the note manager"""
        self.base_dir = base_dir
        self.notes_dir = os.path.join(base_dir, "notes")
        self.projects_dir = os.path.join(base_dir, "projects")
        self.refined_dir = os.path.join(base_dir, "refined")
        
        # JSON files for storing metadata
        self.notes_file = os.path.join(base_dir, "notes.json")
        self.projects_file = os.path.join(base_dir, "projects.json")
        self.refined_file = os.path.join(base_dir, "refined.json")
        
        # Ensure necessary directories exist
        self._ensure_directories()
        
        # Initialize JSON files if they don't exist
        if not os.path.exists(self.notes_file):
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
                
        if not os.path.exists(self.projects_file):
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
                
        if not os.path.exists(self.refined_file):
            with open(self.refined_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _ensure_directories(self):
        """Ensures that necessary directories exist"""
        os.makedirs(self.notes_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.refined_dir, exist_ok=True)
    
    def _load_json(self, file_path: str):
        """Loads data from a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            return []
    
    def _save_json(self, file_path: str, data):
        """Saves data to a JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {str(e)}")
            return False
    
    def _get_next_id(self, prefix, notes):
        """Gets the next ID for a note type"""
        # Find the highest current ID
        max_id = 0
        for note in notes:
            if note["id"].startswith(prefix):
                try:
                    num = int(note["id"][len(prefix):])
                    max_id = max(max_id, num)
                except ValueError:
                    pass
        
        # Return the next ID
        return f"{prefix}{max_id + 1}"
    
    def create_note(self, content: str, project_id=None):
        """Creates a new note"""
        notes = self._load_json(self.notes_file)
        
        # Determine the prefix based on the note type
        if project_id:
            prefix = "projectnote"
        else:
            prefix = "note"
        
        # Get the next ID
        note_id = self._get_next_id(prefix, notes)
        
        note = {
            "id": note_id,
            "content": content,
            "created": datetime.now().isoformat(),
            "project_id": project_id
        }
        
        notes.append(note)
        self._save_json(self.notes_file, notes)
        
        return note
    
    def create_idea(self, content: str):
        """Creates a new idea"""
        notes = self._load_json(self.notes_file)
        
        # Get the next ID for ideas
        idea_id = self._get_next_id("idea", notes)
        
        idea = {
            "id": idea_id,
            "content": content,
            "created": datetime.now().isoformat(),
            "type": "idea"
        }
        
        notes.append(idea)
        self._save_json(self.notes_file, notes)
        
        return idea
    
    def get_note(self, note_id: str):
        """Gets a note by its ID"""
        notes = self._load_json(self.notes_file)
        for note in notes:
            if note["id"] == note_id:
                return note
        return None
    
    def get_recent_notes(self, limit=10):
        """Gets the most recent notes"""
        notes = self._load_json(self.notes_file)
        notes.sort(key=lambda x: x["created"], reverse=True)
        return notes[:limit]
    
    def create_project(self, title: str):
        """Creates a new project"""
        projects = self._load_json(self.projects_file)
        
        # Use the title as the project ID
        project_id = title
        
        # Check if a project with that name already exists
        for project in projects:
            if project["id"] == project_id:
                return project
        
        project = {
            "id": project_id,
            "title": title,
            "created": datetime.now().isoformat()
        }
        
        # Create directory for the project
        project_dir = os.path.join(self.projects_dir, project["id"])
        os.makedirs(project_dir, exist_ok=True)
        
        projects.append(project)
        self._save_json(self.projects_file, projects)
        
        return project
    
    def get_project(self, project_id: str):
        """Gets a project by its ID (name)"""
        projects = self._load_json(self.projects_file)
        for project in projects:
            if project["id"] == project_id:
                return project
        return None
    
    def get_projects(self):
        """Gets all projects"""
        return self._load_json(self.projects_file)
    
    def get_notes_by_project(self, project_id: str):
        """Gets all notes of a project"""
        notes = self._load_json(self.notes_file)
        return [note for note in notes if note.get("project_id") == project_id]

    def update_note(self, note_id: str, content: str) -> bool:
        """Updates the content of a note and saves the refined version"""
        notes = self._load_json(self.notes_file)
        refined_notes = self._load_json(self.refined_file)
        
        # Find the original note
        original_note = None
        for note in notes:
            if note["id"] == note_id:
                original_note = note
                break
        
        if original_note:
            # Create the refined version
            refined_note = {
                "id": note_id,
                "original_content": original_note["content"],
                "refined_content": content,
                "created": datetime.now().isoformat(),
                "project_id": original_note.get("project_id")
            }
            
            # Save the refined version
            refined_notes.append(refined_note)
            self._save_json(self.refined_file, refined_notes)
            
            # Update the original note
            original_note["content"] = content
            original_note["updated"] = datetime.now().isoformat()
            self._save_json(self.notes_file, notes)
            
            return True
        return False
    
    def get_refined_note(self, note_id: str):
        """Gets the refined version of a note by its ID"""
        refined_notes = self._load_json(self.refined_file)
        for note in refined_notes:
            if note["id"] == note_id:
                return note
        return None

# Initialize the note manager
note_manager = NoteManager()

class InterfaceGenerator:
    """Clase para generar interfaces de usuario"""
    
    @staticmethod
    def create_main_menu():
        """Creates the main menu"""
        keyboard = [
            [InlineKeyboardButton("📝 Nueva nota", callback_data="new_note")],
            [InlineKeyboardButton("💡 Nueva idea", callback_data="new_idea")],
            [InlineKeyboardButton("📋 Proyectos", callback_data="menu_projects")],
            [InlineKeyboardButton("🔍 Refinar texto", callback_data="refine_message")],
            [InlineKeyboardButton("🤖 Prompt base", callback_data="base_prompt")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_cancel_menu():
        """Creates the cancel menu"""
        keyboard = [
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_base_prompt_menu(prompt_content):
        """Creates the menu to view and edit the base prompt"""
        keyboard = [
            [InlineKeyboardButton("✏️ Editar prompt", callback_data="edit_base_prompt")],
            [InlineKeyboardButton("🔙 Menú principal", callback_data="menu_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_notes_menu(notes):
        """Crea el menú de notas"""
        keyboard = []
        
        # Agregar botones para cada nota
        for note in notes:
            # Crear un título corto para la nota (primeros 30 caracteres)
            title = note['content'][:30] + "..." if len(note['content']) > 30 else note['content']
            
            # Determinar el tipo de nota para mostrar el icono correcto
            icon = "📝"
            if note.get("type") == "idea":
                icon = "💡"
            elif note.get("project_id"):
                icon = "📋"
            
            keyboard.append([InlineKeyboardButton(f"{icon} {note['id']} - {title}", callback_data=f"note_{note['id']}")])
        
        # Agregar botones de acción
        keyboard.append([InlineKeyboardButton("➕ Nueva nota", callback_data="new_note")])
        keyboard.append([InlineKeyboardButton("🔙 Menú principal", callback_data="menu_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_projects_menu(projects):
        """Crea el menú de proyectos"""
        keyboard = []
        
        # Agregar botones para cada proyecto
        for project in projects:
            keyboard.append([InlineKeyboardButton(f"📋 {project['title']}", callback_data=f"project_{project['id']}")])
        
        # Agregar botones de acción
        keyboard.append([InlineKeyboardButton("➕ Nuevo proyecto", callback_data="new_project")])
        keyboard.append([InlineKeyboardButton("🔙 Menú principal", callback_data="menu_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_help_menu():
        """Crea el menú de ayuda"""
        keyboard = [
            [InlineKeyboardButton("📝 Ayuda sobre notas", callback_data="help_notes")],
            [InlineKeyboardButton("💡 Ayuda sobre ideas", callback_data="help_ideas")],
            [InlineKeyboardButton("📋 Ayuda sobre proyectos", callback_data="help_projects")],
            [InlineKeyboardButton("🔍 Ayuda sobre refinamiento", callback_data="help_refine")],
            [InlineKeyboardButton("🔙 Menú principal", callback_data="menu_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_note_buttons(note_id):
        """Crea los botones para una nota"""
        keyboard = [
            [InlineKeyboardButton("🔍 Refinar", callback_data=f"refine_note_{note_id}")],
            [InlineKeyboardButton("🔙 Volver a notas", callback_data="menu_notes")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_project_buttons(project_id):
        """Crea los botones para un proyecto"""
        keyboard = [
            [InlineKeyboardButton("➕ Nueva nota", callback_data=f"new_project_note_{project_id}")],
            [InlineKeyboardButton("🤖 Preguntar sobre este proyecto", callback_data=f"ask_project_{project_id}")],
            [InlineKeyboardButton("🔙 Volver a proyectos", callback_data="menu_projects")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_confirmation_buttons():
        """Creates confirmation buttons"""
        keyboard = [
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def format_note_message(note):
        """Formatea un mensaje de nota"""
        # Determinar el tipo de nota para mostrar el icono correcto
        icon = "📝"
        if note.get("type") == "idea":
            icon = "💡"
        elif note.get("project_id"):
            icon = "📋"
            
        return f"{icon} Nota #{note['id']}\n\n{note['content']}"
    
    @staticmethod
    def format_project_message(project, notes=None):
        """Formatea un mensaje de proyecto"""
        message = f"📋 Proyecto: {project['title']}\n\n"
        
        if notes:
            message += "Notas del proyecto:\n\n"
            for note in notes:
                title = note['content'][:30] + "..." if len(note['content']) > 30 else note['content']
                message += f"• {note['id']} - {title}\n"
        
        return message

# Initialize the interface generator
interface = InterfaceGenerator()

def is_authorized(user_id: int) -> bool:
    """Checks if a user is authorized to use the bot"""
    return user_id == AUTHORIZED_USER_ID

def is_english(text: str) -> bool:
    """Detects if text is in English or Spanish"""
    # Common words in English and Spanish for better detection
    english_words = {'the', 'and', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'this', 'that', 'these', 'those', 'what', 'when', 'where', 'why', 'how', 'who', 'which'}
    spanish_words = {'el', 'la', 'los', 'las', 'es', 'son', 'está', 'están', 'tiene', 'tienen', 'este', 'esta', 'estos', 'estas', 'qué', 'cuándo', 'dónde', 'por qué', 'cómo', 'quién'}
    
    # Convert text to lowercase and split into words
    words = text.lower().split()
    
    # Count words in English and Spanish
    english_count = sum(1 for word in words if word in english_words)
    spanish_count = sum(1 for word in words if word in spanish_words)
    
    # If there are more English words than Spanish words, we consider it English
    return english_count > spanish_count

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Lo siento, no tienes permiso para usar este bot.")
        return

    welcome_message = (
        "👋 ¡Bienvenido al Asistente de Notas!\n\n"
        "Este bot te ayuda a organizar tus notas y proyectos.\n\n"
        "Puedes:\n"
        "• Crear nuevas notas\n"
        "💡 Guardar ideas\n"
        "📋 Organizar proyectos\n"
        "🔍 Refinar textos\n"
        "🤖 Ver y editar el prompt base de la IA\n"
        "❓ Obtener ayuda\n\n"
        "¿Qué te gustaría hacer?"
    )
    await update.message.reply_text(welcome_message, reply_markup=InterfaceGenerator.create_main_menu())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /help"""
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Lo siento, no tienes permiso para usar este bot.")
        return

    help_text = (
        "❓ ¿Con qué necesitas ayuda?\n\n"
        "Puedo ayudarte con:\n"
        "• Cómo guardar y organizar notas\n"
        "• Cómo guardar ideas\n"
        "• Cómo crear y gestionar proyectos\n"
        "• Cómo refinar textos con IA\n\n"
        "Selecciona una opción para ver más detalles:"
    )

    await update.message.reply_text(
        text=help_text,
        reply_markup=interface.create_help_menu()
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the main menu"""
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You're not authorized to use this bot.")
        return
    
    await update.message.reply_text(
        "Select an option:",
        reply_markup=interface.create_main_menu()
    )

def get_help_text(help_type: str) -> str:
    """Obtiene el texto de ayuda según el tipo"""
    if help_type == "notes":
        return (
            "📝 Ayuda sobre notas\n\n"
            "Las notas te permiten guardar información importante para referencia posterior.\n\n"
            "Para crear una nota:\n"
            "1. Selecciona '📝 Nueva nota' del menú principal\n"
            "2. Escribe el contenido de tu nota\n"
            "3. La nota se guardará automáticamente\n\n"
            "Para ver tus notas:\n"
            "1. Selecciona '📝 Nueva nota' del menú principal\n"
            "2. Verás una lista de tus notas más recientes\n"
            "3. Selecciona una nota para ver su contenido\n\n"
            "También puedes refinar una nota existente para mejorar su presentación."
        )
    elif help_type == "ideas":
        return (
            "💡 Ayuda sobre ideas\n\n"
            "Las ideas te permiten guardar pensamientos o conceptos que quieres desarrollar más tarde.\n\n"
            "Para guardar una idea:\n"
            "1. Selecciona '💡 Nueva idea' del menú principal\n"
            "2. Escribe tu idea\n"
            "3. La idea se guardará automáticamente\n\n"
            "Las ideas son similares a las notas, pero están diseñadas para conceptos más breves o en desarrollo."
        )
    elif help_type == "projects":
        return (
            "📋 Ayuda sobre proyectos\n\n"
            "Los proyectos son carpetas donde puedes organizar tus notas por tema.\n\n"
            "Para crear un proyecto:\n"
            "1. Selecciona '📋 Proyectos' del menú principal\n"
            "2. Selecciona '➕ Nuevo proyecto'\n"
            "3. Escribe el nombre del proyecto\n\n"
            "Para agregar una nota a un proyecto:\n"
            "1. Selecciona un proyecto de la lista\n"
            "2. Selecciona '➕ Nueva nota'\n"
            "3. Escribe el contenido de tu nota\n\n"
            "También puedes preguntar a la IA sobre un proyecto para obtener información basada en todas las notas del proyecto."
        )
    elif help_type == "refine":
        return (
            "🔍 Ayuda sobre refinamiento\n\n"
            "El refinamiento te ayuda a mejorar tus textos usando IA.\n\n"
            "Para refinar un texto:\n"
            "1. Selecciona '🔍 Refinar texto' del menú principal\n"
            "2. Escribe el texto que quieres refinar\n"
            "3. La IA te ayudará a refinar el texto\n\n"
            "La IA detectará automáticamente el idioma del texto y lo refinará en el mismo idioma, manteniendo el significado original pero mejorando su presentación."
        )
    else:
        return (
            "❓ Ayuda general\n\n"
            "Este bot te ayuda a organizar tus notas, ideas y proyectos.\n\n"
            "Comandos principales:\n"
            "• /start - Iniciar el bot\n"
            "• /menu - Ver el menú principal\n"
            "• /help - Ver esta ayuda\n\n"
            "Para más ayuda específica, selecciona una categoría:\n"
            "• 📝 Ayuda sobre notas\n"
            "• 💡 Ayuda sobre ideas\n"
            "• 📋 Ayuda sobre proyectos\n"
            "• 🔍 Ayuda sobre refinamiento"
        )

async def process_with_ai(message: str, context: str = "") -> str:
    """Processes a message with the IA"""
    try:
        # Prepare the request to Ollama
        ollama_url = f"{OLLAMA_HOST}/api/generate"
        
        # Get the current base prompt
        prompt_manager = PromptManager()
        base_prompt = prompt_manager.get_prompt()
        
        # Detect the language of the message
        is_english_text = is_english(message)
        language_instruction = "Respond in English only, without translations." if is_english_text else "Responde en español únicamente, sin traducciones."
        
        # Construct the complete prompt
        complete_prompt = f"{base_prompt['content']}\n\n{language_instruction}\n\n"
        
        # If there's additional context, include it
        if context:
            complete_prompt += f"Additional context:\n{context}\n\n"
        
        # Add the user's message
        complete_prompt += f"User: {message}\n\nAssistant:"
            
        payload = {
            "model": "gemma3",  # This model can be changed based on what's running in Ollama
            "prompt": complete_prompt,
            "stream": False
        }
        
        # Send request to Ollama
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()
        
        # Process response
        ai_response = response.json()['response']
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error processing with IA: {str(e)}")
        error_message = "Sorry, I had a problem processing your message. Could you try again?" if is_english_text else "Lo siento, tuve un problema al procesar tu mensaje. ¿Podrías intentarlo de nuevo?"
        return error_message

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data=None):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in ALLOWED_USERS:
        await query.answer("Lo siento, no tienes permiso para usar este bot.")
        return

    # Usar el callback_data proporcionado o el del query
    data = callback_data if callback_data else query.data

    if data == "menu_main":
        user_states[user_id] = None
        await query.message.edit_text(
            "¡Bienvenido al Asistente de Notas! ¿Qué te gustaría hacer?",
            reply_markup=interface.create_main_menu()
        )

    elif data == "base_prompt":
        prompt_manager = PromptManager()
        base_prompt = prompt_manager.get_prompt()
        
        message = (
            "🤖 *Prompt Base Actual*\n\n"
            f"```\n{base_prompt['content']}\n```\n\n"
            "Puedes editar este prompt haciendo clic en 'Editar prompt'."
        )
        
        await query.message.edit_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=interface.create_base_prompt_menu(base_prompt['content'])
        )

    elif data == "edit_base_prompt":
        context.user_data['waiting_for_base_prompt'] = True
        await query.message.edit_text(
            text=(
                "✏️ *Editar Prompt Base*\n\n"
                "Por favor, envía el nuevo prompt base para la IA.\n\n"
                "Este prompt se usará como base para todas las interacciones con la IA.\n"
                "Puedes incluir instrucciones específicas sobre cómo debe comportarse la IA."
            ),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Cancelar", callback_data="menu_main")
            ]])
        )

    elif data == "new_note":
        user_states[user_id] = "waiting_for_note"
        await query.message.edit_text(
            "📝 *Nueva Nota*\n\nPor favor, escribe el contenido de tu nota:",
            parse_mode='Markdown',
            reply_markup=interface.create_cancel_menu()
        )
        
    elif data == "new_idea":
        user_states[user_id] = "waiting_for_idea"
        await query.message.edit_text(
            "💡 *Nueva Idea*\n\nPor favor, escribe tu idea:",
            parse_mode='Markdown',
            reply_markup=interface.create_cancel_menu()
        )

    elif data == "menu_projects":
        projects = note_manager.get_projects()
        await query.message.edit_text(
            "📋 *Proyectos*\n\nSelecciona un proyecto para ver sus notas o crear uno nuevo:",
            parse_mode='Markdown',
            reply_markup=interface.create_projects_menu(projects)
        )

    elif data == "new_project":
        user_states[user_id] = "waiting_for_project_name"
        await query.message.edit_text(
            "📋 *Nuevo Proyecto*\n\nPor favor, escribe el nombre del proyecto:",
            parse_mode='Markdown',
            reply_markup=interface.create_cancel_menu()
        )

    elif data.startswith("project_"):
        project_id = data.split("_")[1]
        project = note_manager.get_project(project_id)
        
        if project:
            project_notes = note_manager.get_notes_by_project(project_id)
            keyboard = []
            
            if project_notes:
                for note in project_notes:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📝 {note['id']} - {note['content'][:30]}...",
                            callback_data=f"note_{note['id']}"
                        )
                    ])
            else:
                keyboard.append([InlineKeyboardButton("No hay notas en este proyecto", callback_data="dummy")])
            
            # Agregar botones de acción del proyecto
            keyboard.extend(interface.create_project_buttons(project_id).inline_keyboard)
            
            await query.message.edit_text(
                text=interface.format_project_message(project, project_notes),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.message.edit_text(
                "❌ Proyecto no encontrado.",
                reply_markup=interface.create_projects_menu(note_manager.get_projects())
            )

    elif data.startswith("new_project_note_"):
        project_id = data.split("_")[3]
        project = note_manager.get_project(project_id)
        
        if project:
            user_states[user_id] = {
                "state": "waiting_for_project_note",
                "project_id": project_id
            }
            await query.message.edit_text(
                text=f"📝 Vamos a agregar una nota al proyecto '{project['title']}'.\n\n"
                     f"Por favor, envía el contenido de tu nota.\n"
                     f"Esta nota se guardará automáticamente en el proyecto seleccionado.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancelar", callback_data=f"project_{project_id}")]])
            )
        else:
            await query.message.edit_text(
                "❌ Proyecto no encontrado.",
                reply_markup=interface.create_projects_menu(note_manager.get_projects())
            )

    elif data == "refine_message":
        user_states[user_id] = {"state": "waiting_for_refinement"}
        await query.message.edit_text(
            text="🔍 Vamos a refinar tu texto.\n\n"
                 "Por favor, envía el contenido que quieres refinar.\n"
                 "Usaré la IA para ayudarte a mejorarlo, manteniendo su significado principal pero mejorando su presentación.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancelar", callback_data="menu_main")]])
        )

    elif data.startswith("refine_note_"):
        note_id = data.split("_")[2]
        note = note_manager.get_note(note_id)
        
        if note:
            user_states[user_id] = {"state": "waiting_for_refinement", "note_id": note_id}
            await query.message.edit_text(
                text=f"🔍 Vamos a refinar esta nota:\n\n{note['content']}\n\n"
                     f"¿Quieres proceder con el refinamiento?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Refinar", callback_data=f"confirm_refine_{note_id}")],
                    [InlineKeyboardButton("🔙 Cancelar", callback_data=f"note_{note_id}")]
                ])
            )

    elif data.startswith("confirm_refine_"):
        note_id = data.split("_")[2]
        note = note_manager.get_note(note_id)
        
        if note:
            prompt = "Refina el siguiente texto para hacerlo más claro y conciso, manteniendo su significado principal. Si está en español, refínalo en español. Si está en inglés, refínalo en inglés."
            refined_text = await process_with_ai(note['content'], prompt)
            
            note_manager.update_note(note_id, refined_text)
            
            await query.message.edit_text(
                text=f"✅ ¡Nota refinada con éxito!\n\n"
                     f"Texto original:\n{note['content']}\n\n"
                     f"Texto refinado:\n{refined_text}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver a notas", callback_data="menu_notes")]])
            )

    elif data == "cancel":
        user_states[user_id] = None
        await query.message.edit_text(
            "❌ Operación cancelada.\n\n¿Qué te gustaría hacer?",
            reply_markup=interface.create_main_menu()
        )

    elif data.startswith("ask_project_"):
        project_id = data.split("_")[2]
        project = note_manager.get_project(project_id)
        
        if project:
            project_notes = note_manager.get_notes_by_project(project_id)
            
            if project_notes:
                context = f"Estoy trabajando en un proyecto llamado '{project['title']}'. Aquí están las notas del proyecto:\n\n"
                for note in project_notes:
                    context += f"Nota #{note['id']}:\n{note['content']}\n\n"
                    
                context += "Estoy listo para responder preguntas sobre este proyecto basado en estas notas."
                
                user_states[user_id] = {"state": "project_chat", "project_id": project_id, "context": context}
                
                await query.message.edit_text(
                    text=f"🤖 Estoy listo para responder preguntas sobre el proyecto '{project['title']}'.\n\n"
                         f"Este proyecto tiene {len(project_notes)} notas.\n"
                         f"Puedes hacerme cualquier pregunta sobre el contenido de estas notas.\n\n"
                         f"Para salir de este modo, selecciona '🔙 Volver a proyectos'.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver a proyectos", callback_data=f"project_{project_id}")]])
                )
            else:
                await query.message.edit_text(
                    text=f"🤖 El proyecto '{project['title']}' no tiene notas todavía.\n\n"
                         f"Agrega algunas notas antes de hacer preguntas sobre el proyecto.",
                    reply_markup=interface.create_project_buttons(project_id)
                )

    elif data == "help":
        help_text = (
            "❓ ¿Con qué necesitas ayuda?\n\n"
            "Puedo ayudarte con:\n"
            "• Cómo guardar y organizar notas\n"
            "• Cómo guardar ideas\n"
            "• Cómo crear y gestionar proyectos\n"
            "• Cómo refinar textos con IA\n\n"
            "Selecciona una opción para ver más detalles:"
        )
        
        await query.message.edit_text(
            text=help_text,
            reply_markup=interface.create_help_menu()
        )

    elif data.startswith("help_"):
        help_type = data.split("_")[1]
        help_text = get_help_text(help_type)
        
        await query.message.edit_text(
            text=help_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver a ayuda", callback_data="help")]])
        )

    elif data == "menu_notes":
        notes = note_manager.get_recent_notes()
        await query.message.edit_text(
            text="📝 *Notas Recientes*\n\nSelecciona una nota para ver su contenido o crear una nueva:",
            parse_mode='Markdown',
            reply_markup=interface.create_notes_menu(notes)
        )

    elif data.startswith("note_"):
        note_id = data.split("_")[1]
        note = note_manager.get_note(note_id)
        
        if note:
            await query.message.edit_text(
                text=interface.format_note_message(note),
                reply_markup=interface.create_note_buttons(note_id)
            )
        else:
            await query.message.edit_text(
                "❌ Nota no encontrada.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver a notas", callback_data="menu_notes")]])
            )

    elif data.startswith("chat_project_"):
        # Redirigir a ask_project_ para mantener compatibilidad
        project_id = data.split("_")[2]
        await handle_callback(update, context, f"ask_project_{project_id}")

    await query.answer()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message_text = update.message.text

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Lo siento, no tienes permiso para usar este bot.")
        return

    if user_id in user_states:
        state = user_states[user_id]
        
        if state == "waiting_for_note":
            # Crear una nueva nota
            note = note_manager.create_note(message_text)
            user_states[user_id] = None
            await update.message.reply_text(
                f"✅ Nota guardada con ID: {note['id']}\n\n"
                f"Contenido:\n{note['content'][:100]}...",
                reply_markup=interface.create_main_menu()
            )
            
        elif state == "waiting_for_idea":
            # Crear una nueva idea
            idea = note_manager.create_idea(message_text)
            user_states[user_id] = None
            await update.message.reply_text(
                f"✅ Idea guardada con ID: {idea['id']}\n\n"
                f"Contenido:\n{idea['content'][:100]}...",
                reply_markup=interface.create_main_menu()
            )
            
        elif state == "waiting_for_project_name":
            # Crear un nuevo proyecto
            project = note_manager.create_project(message_text)
            user_states[user_id] = None
            await update.message.reply_text(
                f"✅ Proyecto '{project['title']}' creado exitosamente.",
                reply_markup=interface.create_projects_menu(note_manager.get_projects())
            )
            
        elif state == "waiting_for_project_note":
            # Crear una nota dentro de un proyecto
            project_id = user_states[user_id]["project_id"]
            note = note_manager.create_note(message_text, project_id)
            user_states[user_id] = None
            await update.message.reply_text(
                f"✅ Nota guardada en el proyecto con ID: {note['id']}\n\n"
                f"Contenido:\n{note['content'][:100]}...",
                reply_markup=interface.create_project_buttons(project_id)
            )
    
    else:
        # If there's no state, process directly with the IA
        try:
            # Process with the IA without any additional context
            ai_response = await process_with_ai(message_text)
            
            # Send the IA response
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Error processing message with IA: {str(e)}")
            error_message = "Sorry, I had a problem processing your message. Could you try again?" if is_english(message_text) else "Lo siento, tuve un problema al procesar tu mensaje. ¿Podrías intentarlo de nuevo?"
            await update.message.reply_text(error_message)

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles received commands"""
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You're not authorized to use this bot.")
        return
    
    command = update.message.text.split()[0].lower()
    
    if command == "/start":
        await start(update, context)
    elif command == "/menu":
        await menu_command(update, context)
    elif command == "/help":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "Command not recognized. Use /help to see available commands."
        )

def main():
    """Starts the bot"""
    # Configure the bot
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Start the bot
    main() 