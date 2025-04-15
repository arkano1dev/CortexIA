import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import shortuuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = os.getenv('BASE_DIR', os.path.join(os.path.dirname(__file__), 'data'))

class NoteManager:
    """Gestor de notas, diario, ideas y proyectos"""
    
    def __init__(self, base_dir=BASE_DIR):
        """Inicializa el gestor de notas"""
        self.base_dir = base_dir
        
        # Directorios para diferentes tipos de contenido
        self.notes_dir = os.path.join(base_dir, "notes")
        self.journal_dir = os.path.join(base_dir, "journal")
        self.ideas_dir = os.path.join(base_dir, "ideas")
        self.projects_dir = os.path.join(base_dir, "projects")
        self.analysis_dir = os.path.join(base_dir, "analysis")
        self.refined_dir = os.path.join(base_dir, "refined")
        
        # Archivo JSON para almacenar metadatos
        self.notes_file = os.path.join(base_dir, "notes.json")
        self.journal_file = os.path.join(base_dir, "journal.json")
        self.ideas_file = os.path.join(base_dir, "ideas.json")
        self.projects_file = os.path.join(base_dir, "projects.json")
        self.refined_file = os.path.join(base_dir, "refined.json")
        
        # Asegurar que existan los directorios necesarios
        self._ensure_directories()
        
        # Cargar datos existentes
        self.notes = self._load_json(self.notes_file)
        self.journal = self._load_json(self.journal_file)
        self.ideas = self._load_json(self.ideas_file)
        self.projects = self._load_json(self.projects_file)
    
    def _ensure_directories(self):
        """Asegura que existan los directorios necesarios"""
        # Crear directorios
        os.makedirs(self.notes_dir, exist_ok=True)
        os.makedirs(self.journal_dir, exist_ok=True)
        os.makedirs(self.ideas_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.analysis_dir, exist_ok=True)
        os.makedirs(self.refined_dir, exist_ok=True)
    
    def _load_json(self, file_path: str) -> List[Dict]:
        """Carga un archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar {file_path}: {str(e)}")
            return []
    
    def _save_json(self, file_path: str, data: List[Dict]):
        """Guarda datos en un archivo JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error al guardar {file_path}: {str(e)}")
    
    def create_note(self, content: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Crea una nueva nota"""
        # Generar ID corto
        note_id = shortuuid.uuid()[:8]
        
        # Crear la nota
        note = {
            'id': note_id,
            'content': content,
            'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'project_id': project_id
        }
        
        # Cargar notas existentes
        notes = self._load_json(self.notes_file)
        
        # Agregar la nueva nota
        notes.append(note)
        
        # Guardar notas
        self._save_json(self.notes_file, notes)
        
        return note
    
    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una nota por su ID"""
        notes = self._load_json(self.notes_file)
        for note in notes:
            if note['id'] == note_id:
                return note
        return None
    
    def get_notes(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene todas las notas o las de un proyecto específico"""
        notes = self._load_json(self.notes_file)
        if project_id:
            return [note for note in notes if note.get('project_id') == project_id]
        return notes
    
    def get_recent_notes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene las notas más recientes"""
        notes = self._load_json(self.notes_file)
        # Ordenar por fecha de creación (más recientes primero)
        notes.sort(key=lambda x: x['created'], reverse=True)
        return notes[:limit]
    
    def create_journal_entry(self, content: str) -> Dict[str, Any]:
        """Crea una nueva entrada de diario"""
        # Generar ID corto
        entry_id = shortuuid.uuid()[:8]
        
        # Crear la entrada
        entry = {
            'id': entry_id,
            'content': content,
            'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Cargar entradas existentes
        entries = self._load_json(self.journal_file)
        
        # Agregar la nueva entrada
        entries.append(entry)
        
        # Guardar entradas
        self._save_json(self.journal_file, entries)
        
        return entry
    
    def get_journal_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una entrada de diario por su ID"""
        entries = self._load_json(self.journal_file)
        for entry in entries:
            if entry['id'] == entry_id:
                return entry
        return None
    
    def get_recent_journal_entries(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene las entradas de diario más recientes"""
        entries = self._load_json(self.journal_file)
        # Ordenar por fecha de creación (más recientes primero)
        entries.sort(key=lambda x: x['created'], reverse=True)
        return entries[:limit]
    
    def create_idea(self, content: str) -> Dict[str, Any]:
        """Crea una nueva idea"""
        # Generar ID corto
        idea_id = shortuuid.uuid()[:8]
        
        # Crear la idea
        idea = {
            'id': idea_id,
            'content': content,
            'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Cargar ideas existentes
        ideas = self._load_json(self.ideas_file)
        
        # Agregar la nueva idea
        ideas.append(idea)
        
        # Guardar ideas
        self._save_json(self.ideas_file, ideas)
        
        return idea
    
    def get_idea(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una idea por su ID"""
        ideas = self._load_json(self.ideas_file)
        for idea in ideas:
            if idea['id'] == idea_id:
                return idea
        return None
    
    def get_recent_ideas(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene las ideas más recientes"""
        ideas = self._load_json(self.ideas_file)
        # Ordenar por fecha de creación (más recientes primero)
        ideas.sort(key=lambda x: x['created'], reverse=True)
        return ideas[:limit]
    
    def create_project(self, title: str) -> Dict[str, Any]:
        """Crea un nuevo proyecto"""
        # Generar ID corto
        project_id = shortuuid.uuid()[:8]
        
        # Crear el proyecto
        project = {
            'id': project_id,
            'title': title,
            'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Cargar proyectos existentes
        projects = self._load_json(self.projects_file)
        
        # Agregar el nuevo proyecto
        projects.append(project)
        
        # Guardar proyectos
        self._save_json(self.projects_file, projects)
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un proyecto por su ID"""
        projects = self._load_json(self.projects_file)
        for project in projects:
            if project['id'] == project_id:
                return project
        return None
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Obtiene todos los proyectos"""
        return self._load_json(self.projects_file)
    
    def save_analysis(self, note_id: str, analysis: str):
        """Guarda un análisis de una nota"""
        # Crear directorio si no existe
        os.makedirs(f'{self.analysis_dir}/{note_id}', exist_ok=True)
        
        # Guardar el análisis
        with open(f'{self.analysis_dir}/{note_id}/analysis.txt', 'w', encoding='utf-8') as f:
            f.write(analysis)
    
    def update_note(self, note_id: str, content: str) -> bool:
        """Actualiza el contenido de una nota"""
        notes = self._load_json(self.notes_file)
        for note in notes:
            if note['id'] == note_id:
                note['content'] = content
                note['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                self._save_json(self.notes_file, notes)
                return True
        return False
    
    def delete_note(self, note_id: str) -> bool:
        """Elimina una nota"""
        notes = self._load_json(self.notes_file)
        for i, note in enumerate(notes):
            if note['id'] == note_id:
                notes.pop(i)
                self._save_json(self.notes_file, notes)
                return True
        return False
    
    def add_tag(self, note_id: str, tag: str) -> bool:
        """Añade una etiqueta a una nota"""
        notes = self._load_json(self.notes_file)
        for note in notes:
            if note['id'] == note_id:
                if tag not in note['tags']:
                    note['tags'].append(tag)
                    self._save_json(self.notes_file, notes)
                return True
        return False
    
    def get_notes_by_tag(self, tag: str) -> List[Dict]:
        """Obtiene todas las notas con una etiqueta específica"""
        notes = self._load_json(self.notes_file)
        return [note for note in notes if tag in note.get('tags', [])] 