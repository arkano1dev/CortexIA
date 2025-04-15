import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class InterfaceGenerator:
    """Clase para generar interfaces de usuario"""
    
    @staticmethod
    def create_main_menu():
        """Crea el menú principal"""
        keyboard = [
            [InlineKeyboardButton("📝 New note", callback_data="new_note")],
            [InlineKeyboardButton("💡 New idea", callback_data="new_idea")],
            [InlineKeyboardButton("📋 Projects", callback_data="menu_projects")],
            [InlineKeyboardButton("🔍 Refine text", callback_data="refine_message")],
            [InlineKeyboardButton("🤖 Base prompt", callback_data="base_prompt")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_base_prompt_menu(prompt_content):
        """Crea el menú para ver y editar el prompt base"""
        keyboard = [
            [InlineKeyboardButton("✏️ Edit prompt", callback_data="edit_base_prompt")],
            [InlineKeyboardButton("🔙 Main menu", callback_data="menu_main")]
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
            keyboard.append([InlineKeyboardButton(f"📝 {note['id']} - {title}", callback_data=f"note_{note['id']}")])
        
        # Agregar botones de acción
        keyboard.append([InlineKeyboardButton("➕ New note", callback_data="new_note")])
        keyboard.append([InlineKeyboardButton("🔙 Main menu", callback_data="menu_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_projects_menu(projects):
        """Crea el menú de proyectos"""
        keyboard = []
        
        # Agregar botones para cada proyecto
        for project in projects:
            keyboard.append([InlineKeyboardButton(f"📋 {project['title']}", callback_data=f"project_{project['id']}")])
        
        # Agregar botones de acción
        keyboard.append([InlineKeyboardButton("➕ New project", callback_data="new_project")])
        keyboard.append([InlineKeyboardButton("🔙 Main menu", callback_data="menu_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_help_menu():
        """Crea el menú de ayuda"""
        keyboard = [
            [InlineKeyboardButton("📝 Notes help", callback_data="help_notes")],
            [InlineKeyboardButton("💡 Ideas help", callback_data="help_ideas")],
            [InlineKeyboardButton("📋 Projects help", callback_data="help_projects")],
            [InlineKeyboardButton("🔍 Refinement help", callback_data="help_refine")],
            [InlineKeyboardButton("🔙 Main menu", callback_data="menu_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_note_buttons(note_id):
        """Crea los botones para una nota"""
        keyboard = [
            [InlineKeyboardButton("🔍 Refine", callback_data=f"refine_note_{note_id}")],
            [InlineKeyboardButton("🔙 Back to notes", callback_data="menu_notes")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_project_buttons(project_id):
        """Crea los botones para un proyecto"""
        keyboard = [
            [InlineKeyboardButton("➕ New note", callback_data=f"new_project_note_{project_id}")],
            [InlineKeyboardButton("🤖 Ask about this project", callback_data=f"ask_project_{project_id}")],
            [InlineKeyboardButton("🔙 Back to projects", callback_data="menu_projects")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_cancel_menu():
        """Crea el menú de cancelación"""
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def format_note_message(note):
        """Formatea un mensaje de nota"""
        return f"📝 Note #{note['id']}\n\n{note['content']}"
    
    @staticmethod
    def format_project_message(project, notes=None):
        """Formatea un mensaje de proyecto"""
        message = f"📋 Project: {project['title']}\n\n"
        
        if notes:
            message += "Project notes:\n\n"
            for note in notes:
                title = note['content'][:30] + "..." if len(note['content']) > 30 else note['content']
                message += f"• {note['id']} - {title}\n"
        
        return message 