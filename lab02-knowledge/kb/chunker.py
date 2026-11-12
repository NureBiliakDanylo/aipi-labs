"""Розбиття нотатки на фрагменти за заголовками Markdown з урахуванням блоків коду."""
import re
from dataclasses import dataclass
from .vault import Note, strip_wikilinks

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")

@dataclass
class Chunk:
    id: str
    note_path: str
    section: str
    text: str
    tags: list[str]
    source_link: str

    @property
    def embed_text(self) -> str:
        clean = strip_wikilinks(self.text).strip()
        tags_str = ", ".join(self.tags) if self.tags else "none"
        return f"Нотатка: {self.source_link}\nРозділ: {self.section}\nТеги: {tags_str}\n{clean}"

def chunk_note(note: Note, max_chars: int = 1200) -> list[Chunk]:
    chunks: list[Chunk] = []
    lines = note.body.splitlines()
    current_section = note.title
    current_lines: list[str] = []
    idx = 0
    in_code = False

    def flush():
        nonlocal idx, current_lines
        content = "\n".join(current_lines).strip()
        if content:
            if len(content) > max_chars * 1.5:
                paras = content.split("\n\n")
                sub_lines: list[str] = []
                sub_idx = 0
                for p in paras:
                    if sum(len(x) for x in sub_lines) + len(p) > max_chars and sub_lines:
                        c_text = "\n\n".join(sub_lines).strip()
                        chunks.append(Chunk(
                            id=f"{note.path}::{idx}.{sub_idx}",
                            note_path=note.path,
                            section=f"{current_section} (частина {sub_idx+1})",
                            text=c_text,
                            tags=note.tags,
                            source_link=f"{note.title}#{current_section}",
                        ))
                        sub_lines = [p]
                        sub_idx += 1
                    else:
                        sub_lines.append(p)
                if sub_lines:
                    chunks.append(Chunk(
                        id=f"{note.path}::{idx}.{sub_idx}",
                        note_path=note.path,
                        section=f"{current_section} (частина {sub_idx+1})",
                        text="\n\n".join(sub_lines).strip(),
                        tags=note.tags,
                        source_link=f"{note.title}#{current_section}",
                    ))
            else:
                chunks.append(Chunk(
                    id=f"{note.path}::{idx}",
                    note_path=note.path,
                    section=current_section,
                    text=content,
                    tags=note.tags,
                    source_link=f"{note.title}#{current_section}",
                ))
            idx += 1
        current_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            current_lines.append(line)
            continue

        if not in_code:
            m = HEADING.match(line)
            if m:
                flush()
                current_section = m.group(2).strip()
                continue

        current_lines.append(line)

    flush()
    return chunks
