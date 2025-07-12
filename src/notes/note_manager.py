"""
Note Manager - Obsidian-style note-taking for SprintReader
Handles highlight-to-note functionality and topic organization
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from qt_compat import QObject, pyqtSignal

@dataclass
class Note:
    """Represents a single note with metadata"""
    id: str
    title: str
    content: str
    topic_id: str
    document_id: int
    page_number: int
    excerpt: str = ""
    tags: List[str] = None
    created_at: str = ""
    updated_at: str = ""
    linked_notes: List[str] = None
    x_position: float = 0.0
    y_position: float = 0.0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.linked_notes is None:
            self.linked_notes = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

@dataclass
class Topic:
    """Represents a topic vault for organizing notes"""
    id: str
    name: str
    description: str = ""
    created_at: str = ""
    notes_count: int = 0
    color: str = "#7E22CE"  # Default purple accent
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class NoteManager(QObject):
    """Manages all note-taking operations and topic organization"""
    
    # Signals
    note_created = pyqtSignal(str)  # note_id
    note_updated = pyqtSignal(str)  # note_id
    note_deleted = pyqtSignal(str)  # note_id
    topic_created = pyqtSignal(str)  # topic_id
    notes_imported = pyqtSignal(int)  # count
    
    def __init__(self, base_path: str = "vaults"):
        super().__init__()
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # In-memory storage for performance
        self.notes: Dict[str, Note] = {}
        self.topics: Dict[str, Topic] = {}
        
        # Load existing data
        self._load_topics()
        self._load_notes()
        
        # Create default topic if none exist
        if not self.topics:
            self.create_topic("General", "Default topic for uncategorized notes")
    
    def create_note_from_highlight(self, 
                                 document_id: int,
                                 page_number: int, 
                                 highlighted_text: str,
                                 topic_name: str,
                                 user_notes: str = "",
                                 position: tuple = (0.0, 0.0)) -> str:
        """Create a note from highlighted PDF text"""
        
        # Get or create topic
        topic_id = self.get_or_create_topic(topic_name)
        
        # Generate note title from excerpt
        title = self._generate_note_title(highlighted_text)
        
        # Create note
        note = Note(
            id=str(uuid.uuid4()),
            title=title,
            content=user_notes,
            topic_id=topic_id,
            document_id=document_id,
            page_number=page_number,
            excerpt=highlighted_text,
            x_position=position[0],
            y_position=position[1]
        )
        
        # Save note
        self.notes[note.id] = note
        self._save_note(note)
        
        # Update topic count
        if topic_id in self.topics:
            self.topics[topic_id].notes_count += 1
            self._save_topic(self.topics[topic_id])
        
        self.note_created.emit(note.id)
        return note.id
    
    def create_topic(self, name: str, description: str = "") -> str:
        """Create a new topic vault"""
        # Check if topic already exists
        for topic in self.topics.values():
            if topic.name.lower() == name.lower():
                return topic.id
        
        topic = Topic(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        
        self.topics[topic.id] = topic
        self._save_topic(topic)
        self._create_topic_directory(topic)
        
        self.topic_created.emit(topic.id)
        return topic.id
    
    def get_or_create_topic(self, name: str) -> str:
        """Get existing topic or create new one"""
        for topic in self.topics.values():
            if topic.name.lower() == name.lower():
                return topic.id
        return self.create_topic(name)
    
    def update_note(self, note_id: str, content: str, title: str = None) -> bool:
        """Update existing note"""
        if note_id not in self.notes:
            return False
        
        note = self.notes[note_id]
        note.content = content
        note.updated_at = datetime.now().isoformat()
        
        if title:
            note.title = title
        
        # Process wiki links [[Note Name]]
        self._process_wiki_links(note)
        
        self._save_note(note)
        self.note_updated.emit(note_id)
        return True
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note"""
        if note_id not in self.notes:
            return False
        
        note = self.notes[note_id]
        
        # Remove from topic count
        if note.topic_id in self.topics:
            self.topics[note.topic_id].notes_count -= 1
            self._save_topic(self.topics[note.topic_id])
        
        # Delete file
        note_path = self._get_note_path(note)
        if note_path.exists():
            note_path.unlink()
        
        # Remove from memory
        del self.notes[note_id]
        
        self.note_deleted.emit(note_id)
        return True
    
    def search_notes(self, query: str, topic_id: str = None) -> List[Note]:
        """Search notes by content, title, or tags"""
        query_lower = query.lower()
        results = []
        
        for note in self.notes.values():
            # Filter by topic if specified
            if topic_id and note.topic_id != topic_id:
                continue
            
            # Search in title, content, excerpt, and tags
            searchable_text = f"{note.title} {note.content} {note.excerpt} {' '.join(note.tags)}"
            if query_lower in searchable_text.lower():
                results.append(note)
        
        # Sort by relevance (title matches first, then content)
        results.sort(key=lambda n: (
            0 if query_lower in n.title.lower() else 1,
            -len(n.content)
        ))
        
        return results
    
    def get_notes_by_topic(self, topic_id: str) -> List[Note]:
        """Get all notes for a specific topic"""
        return [note for note in self.notes.values() if note.topic_id == topic_id]
    
    def get_notes_by_document(self, document_id: int) -> List[Note]:
        """Get all notes for a specific document"""
        return [note for note in self.notes.values() if note.document_id == document_id]
    
    def get_linked_notes(self, note_id: str) -> List[Note]:
        """Get notes linked to this note"""
        if note_id not in self.notes:
            return []
        
        linked_ids = self.notes[note_id].linked_notes
        return [self.notes[nid] for nid in linked_ids if nid in self.notes]
    
    def add_tag_to_note(self, note_id: str, tag: str) -> bool:
        """Add tag to note"""
        if note_id not in self.notes:
            return False
        
        tag = tag.strip('#').lower()
        if tag not in self.notes[note_id].tags:
            self.notes[note_id].tags.append(tag)
            self.notes[note_id].updated_at = datetime.now().isoformat()
            self._save_note(self.notes[note_id])
            return True
        return False
    
    def get_all_tags(self) -> Set[str]:
        """Get all unique tags across all notes"""
        tags = set()
        for note in self.notes.values():
            tags.update(note.tags)
        return tags
    
    def export_topic_as_markdown(self, topic_id: str) -> str:
        """Export all notes in a topic as markdown"""
        if topic_id not in self.topics:
            return ""
        
        topic = self.topics[topic_id]
        topic_notes = self.get_notes_by_topic(topic_id)
        
        markdown = f"# {topic.name}\n\n"
        if topic.description:
            markdown += f"{topic.description}\n\n"
        
        markdown += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        markdown += f"**{len(topic_notes)} notes in this topic**\n\n---\n\n"
        
        for note in sorted(topic_notes, key=lambda n: n.created_at):
            markdown += f"## {note.title}\n\n"
            
            if note.excerpt:
                markdown += f"> {note.excerpt}\n\n"
            
            if note.content:
                markdown += f"{note.content}\n\n"
            
            # Add metadata
            markdown += f"*Page {note.page_number} • Created {note.created_at[:10]}*"
            
            if note.tags:
                markdown += f" • Tags: {', '.join(f'#{tag}' for tag in note.tags)}"
            
            markdown += "\n\n---\n\n"
        
        return markdown
    
    def export_all_notes(self, export_path: str) -> int:
        """Export all notes as markdown files"""
        export_dir = Path(export_path)
        export_dir.mkdir(exist_ok=True)
        
        exported_count = 0
        
        for topic_id, topic in self.topics.items():
            # Create topic directory
            topic_dir = export_dir / self._sanitize_filename(topic.name)
            topic_dir.mkdir(exist_ok=True)
            
            # Export topic summary
            topic_markdown = self.export_topic_as_markdown(topic_id)
            summary_path = topic_dir / "README.md"
            summary_path.write_text(topic_markdown, encoding='utf-8')
            exported_count += 1
            
            # Export individual notes
            topic_notes = self.get_notes_by_topic(topic_id)
            for note in topic_notes:
                note_markdown = self._note_to_markdown(note)
                note_filename = f"{self._sanitize_filename(note.title)}.md"
                note_path = topic_dir / note_filename
                note_path.write_text(note_markdown, encoding='utf-8')
                exported_count += 1
        
        return exported_count
    
    def _generate_note_title(self, excerpt: str) -> str:
        """Generate a note title from highlighted text"""
        # Take first 50 characters and clean up
        title = excerpt[:50].strip()
        
        # Remove line breaks and extra spaces
        title = ' '.join(title.split())
        
        # Add ellipsis if truncated
        if len(excerpt) > 50:
            title += "..."
        
        return title or "Untitled Note"
    
    def _process_wiki_links(self, note: Note):
        """Process [[Note Name]] links in note content"""
        import re
        
        # Find all wiki links
        wiki_pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(wiki_pattern, note.content)
        
        # Clear existing links
        note.linked_notes = []
        
        # Find matching notes
        for link_text in matches:
            for other_note in self.notes.values():
                if (other_note.title.lower() == link_text.lower() and 
                    other_note.id != note.id):
                    note.linked_notes.append(other_note.id)
                    break
    
    def _note_to_markdown(self, note: Note) -> str:
        """Convert note to markdown format"""
        markdown = f"# {note.title}\n\n"
        
        if note.excerpt:
            markdown += f"## Excerpt\n\n> {note.excerpt}\n\n"
        
        if note.content:
            markdown += f"## Notes\n\n{note.content}\n\n"
        
        # Add metadata
        markdown += "## Metadata\n\n"
        markdown += f"- **Page**: {note.page_number}\n"
        markdown += f"- **Created**: {note.created_at[:10]}\n"
        markdown += f"- **Updated**: {note.updated_at[:10]}\n"
        
        if note.tags:
            markdown += f"- **Tags**: {', '.join(f'#{tag}' for tag in note.tags)}\n"
        
        if note.linked_notes:
            markdown += f"- **Links**: {len(note.linked_notes)} connected notes\n"
        
        return markdown
    
    def _create_topic_directory(self, topic: Topic):
        """Create directory structure for topic"""
        topic_dir = self.base_path / self._sanitize_filename(topic.name)
        topic_dir.mkdir(exist_ok=True)
        
        # Create topic metadata file
        metadata = {
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'created_at': topic.created_at,
            'color': topic.color
        }
        
        metadata_path = topic_dir / '.topic.json'
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    
    def _get_note_path(self, note: Note) -> Path:
        """Get file path for note"""
        if note.topic_id in self.topics:
            topic_name = self.topics[note.topic_id].name
        else:
            topic_name = "General"
        
        topic_dir = self.base_path / self._sanitize_filename(topic_name)
        filename = f"{self._sanitize_filename(note.title)}.md"
        return topic_dir / filename
    
    def _save_note(self, note: Note):
        """Save note to markdown file"""
        note_path = self._get_note_path(note)
        note_path.parent.mkdir(exist_ok=True)
        
        # Add metadata header
        markdown = f"---\n"
        markdown += f"id: {note.id}\n"
        markdown += f"topic_id: {note.topic_id}\n"
        markdown += f"document_id: {note.document_id}\n"
        markdown += f"page_number: {note.page_number}\n"
        markdown += f"created_at: {note.created_at}\n"
        markdown += f"updated_at: {note.updated_at}\n"
        if note.tags:
            markdown += f"tags: [{', '.join(note.tags)}]\n"
        markdown += f"---\n\n"
        
        # Add content
        markdown += f"# {note.title}\n\n"
        
        if note.excerpt:
            markdown += f"## Excerpt\n\n> {note.excerpt}\n\n"
        
        if note.content:
            markdown += f"## Notes\n\n{note.content}\n"
        
        note_path.write_text(markdown, encoding='utf-8')
    
    def _save_topic(self, topic: Topic):
        """Save topic metadata"""
        self._create_topic_directory(topic)
    
    def _load_topics(self):
        """Load topics from filesystem"""
        if not self.base_path.exists():
            return
        
        for topic_dir in self.base_path.iterdir():
            if not topic_dir.is_dir():
                continue
            
            metadata_path = topic_dir / '.topic.json'
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
                    topic = Topic(**metadata)
                    self.topics[topic.id] = topic
                except Exception as e:
                    print(f"Error loading topic {topic_dir.name}: {e}")
            else:
                # Create topic from directory name
                topic_id = str(uuid.uuid4())
                topic = Topic(
                    id=topic_id,
                    name=topic_dir.name.replace('_', ' ').title()
                )
                self.topics[topic_id] = topic
                self._save_topic(topic)
    
    def _load_notes(self):
        """Load notes from markdown files"""
        for topic_dir in self.base_path.iterdir():
            if not topic_dir.is_dir():
                continue
            
            for note_file in topic_dir.glob("*.md"):
                if note_file.name.startswith('.'):
                    continue
                
                try:
                    content = note_file.read_text(encoding='utf-8')
                    note = self._parse_note_from_markdown(content, note_file.stem)
                    if note:
                        self.notes[note.id] = note
                except Exception as e:
                    print(f"Error loading note {note_file}: {e}")
    
    def _parse_note_from_markdown(self, content: str, filename: str) -> Optional[Note]:
        """Parse note from markdown content"""
        lines = content.split('\n')
        
        # Parse frontmatter
        if lines[0] == '---':
            frontmatter_end = 1
            while frontmatter_end < len(lines) and lines[frontmatter_end] != '---':
                frontmatter_end += 1
            
            if frontmatter_end < len(lines):
                frontmatter = {}
                for line in lines[1:frontmatter_end]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
                
                # Extract content after frontmatter
                content_lines = lines[frontmatter_end + 1:]
                content_text = '\n'.join(content_lines)
                
                # Parse content sections
                title, excerpt, notes = self._parse_note_content(content_text)
                
                return Note(
                    id=frontmatter.get('id', str(uuid.uuid4())),
                    title=title or filename,
                    content=notes,
                    topic_id=frontmatter.get('topic_id', ''),
                    document_id=int(frontmatter.get('document_id', 0)),
                    page_number=int(frontmatter.get('page_number', 1)),
                    excerpt=excerpt,
                    created_at=frontmatter.get('created_at', ''),
                    updated_at=frontmatter.get('updated_at', ''),
                    tags=eval(frontmatter.get('tags', '[]')) if frontmatter.get('tags') else []
                )
        
        return None
    
    def _parse_note_content(self, content: str) -> tuple:
        """Parse title, excerpt, and notes from content"""
        lines = content.split('\n')
        title = ""
        excerpt = ""
        notes = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                title = line[2:]
            elif line == '## Excerpt':
                current_section = 'excerpt'
            elif line == '## Notes':
                current_section = 'notes'
            elif line.startswith('## '):
                current_section = None
            elif current_section == 'excerpt' and line.startswith('> '):
                excerpt += line[2:] + ' '
            elif current_section == 'notes' and line:
                notes += line + '\n'
        
        return title.strip(), excerpt.strip(), notes.strip()
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        import re
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Limit length
        return sanitized[:100]