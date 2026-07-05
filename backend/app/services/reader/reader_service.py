import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class ReaderCommand(str, Enum):
    READ = "read"
    PAUSE = "pause"
    CONTINUE = "continue"
    FASTER = "faster"
    SLOWER = "slower"
    REPEAT = "repeat"
    GOTO_PAGE = "goto_page"


class ReaderService:
    def __init__(self, ai_engine: AIEngine):
        self.ai_engine = ai_engine
        self._current_position = 0
        self._current_content = ""
        self._is_paused = False
        self._speed = 1.0

    async def read_text(self, text: str) -> Dict[str, Any]:
        self._current_content = text
        self._current_position = 0
        self._is_paused = False
        return {
            "content": text,
            "total_length": len(text),
            "position": 0,
            "status": "reading",
        }

    async def read_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        suffix = path.suffix.lower()
        content = ""

        if suffix in (".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml"):
            content = path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".pdf":
            content = await self._read_pdf(file_path)
        elif suffix in (".docx", ".doc"):
            content = await self._read_docx(file_path)
        elif suffix == ".epub":
            content = await self._read_epub(file_path)
        else:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return {"error": f"Unsupported format: {suffix}"}

        return await self.read_text(content)

    async def command(self, command: ReaderCommand, **params) -> Dict[str, Any]:
        if command == ReaderCommand.PAUSE:
            self._is_paused = True
            return {"status": "paused", "position": self._current_position}
        elif command == ReaderCommand.CONTINUE:
            self._is_paused = False
            return {"status": "reading", "position": self._current_position}
        elif command == ReaderCommand.FASTER:
            self._speed = min(3.0, self._speed + 0.25)
            return {"status": "reading", "speed": self._speed}
        elif command == ReaderCommand.SLOWER:
            self._speed = max(0.5, self._speed - 0.25)
            return {"status": "reading", "speed": self._speed}
        elif command == ReaderCommand.REPEAT:
            return {"status": "repeating", "position": self._current_position}
        elif command == ReaderCommand.GOTO_PAGE:
            page = params.get("page", 0)
            self._current_position = page * 1000
            return {"status": "reading", "position": self._current_position}
        return {"status": "unknown_command"}

    async def _read_pdf(self, file_path: str) -> str:
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return " ".join(page.extract_text() for page in reader.pages)
        except ImportError:
            return "[PDF reader requires PyPDF2: pip install PyPDF2]"
        except Exception as e:
            return f"[PDF read error: {e}]"

    async def _read_docx(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return "[DOCX reader requires python-docx: pip install python-docx]"
        except Exception as e:
            return f"[DOCX read error: {e}]"

    async def _read_epub(self, file_path: str) -> str:
        try:
            import ebooklib
            from ebooklib import epub
            book = epub.read_epub(file_path)
            from bs4 import BeautifulSoup
            texts = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    texts.append(soup.get_text())
            return "\n".join(texts)
        except ImportError:
            return "[EPUB reader requires ebooklib and beautifulsoup4]"
        except Exception as e:
            return f"[EPUB read error: {e}]"
