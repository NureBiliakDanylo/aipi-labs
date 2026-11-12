"""Читання сховища Obsidian: властивості (YAML), теги, вікі-посилання."""
import hashlib
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
import frontmatter

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]*))?(?:\|([^\]]+))?\]\]")
INLINE_TAG = re.compile(r"(?<![\w&#])#([^\s#\[\]()`,.;:!?\"']+)")

@dataclass
class Note:
    path: str
    title: str
    body: str
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    properties: dict = field(default_factory=dict)
    content_hash: str = ""

def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(v).strip() for v in value if str(v).strip()]

def strip_wikilinks(text: str) -> str:
    """[[A|b]] -> b, [[A#Розділ]] -> A, [[A]] -> A: для ембедингів і показу."""
    return WIKILINK.sub(lambda m: (m.group(3) or m.group(1)).strip(), text)

def parse_note(vault: Path, file: Path) -> Note:
    raw = file.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    tags = _as_list(post.get("tags"))
    for tag in INLINE_TAG.findall(post.content):
        if tag not in tags:
            tags.append(tag)
    return Note(
        path=file.relative_to(vault).as_posix(),
        title=str(post.get("title") or (re.search(r"^#\s+(.+)$", post.content, re.M).group(1).strip() if re.search(r"^#\s+(.+)$", post.content, re.M) else file.stem)),
        body=post.content,
        tags=[t.lstrip("#") for t in tags],
        aliases=_as_list(post.get("aliases")),
        links=sorted({m.group(1).strip() for m in WIKILINK.finditer(post.content)}),
        properties={k: str(v) for k, v in post.metadata.items()},
        content_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    )

def iter_notes(vault: Path) -> Iterator[Note]:
    """Усі .md-файли, крім службових (.obsidian, .trash) і шаблонів (_templates)."""
    for file in sorted(vault.rglob("*.md")):
        rel = file.relative_to(vault)
        if any(part.startswith((".", "_")) for part in rel.parts):
            continue
        yield parse_note(vault, file)

def resolve_note_path(vault: Path, name: str) -> Path:
    """Безпечно перетворює шлях або назву нотатки на абсолютний шлях усередині сховища."""
    clean = re.sub(r"^[\\/]+", "", name.strip())
    clean = WIKILINK.sub(r"\1", clean)
    if not clean.endswith(".md"):
        clean += ".md"
    target = (vault / clean).resolve()
    if not target.is_relative_to(vault.resolve()):
        raise ValueError(f"Спроба виходу за межі сховища: {name}")
    if target.is_file():
        return target
    # Пошук за назвою файла в підкаталогах
    stem = Path(clean).stem.lower()
    for file in vault.rglob("*.md"):
        if file.stem.lower() == stem and not any(p.startswith((".", "_")) for p in file.relative_to(vault).parts):
            return file.resolve()
    raise FileNotFoundError(f"Нотатку не знайдено: {name}")
