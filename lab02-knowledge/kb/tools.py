"""Дії агента над базою знань: search_knowledge, read_note, write_note."""
import time
from pathlib import Path
from .config import KBConfig, load_config
from .vault import parse_note, resolve_note_path, strip_wikilinks
from .store import KnowledgeStore
from .embedder import FallbackMiniLMEmbedder, GeminiEmbedder
import chromadb

NOT_FOUND = "NOT_FOUND"

class KnowledgeTools:
    def __init__(self, store: KnowledgeStore, vault: Path, top_k: int = 4, max_distance: float = 0.55, max_note_chars: int = 4000):
        self.store = store
        self.vault = vault
        self.config = KBConfig(vault_path=vault, chroma_path=store.client._system.settings.persist_directory if hasattr(store.client, "_system") else Path("./chroma_data"), top_k=top_k, max_distance=max_distance)
        self.top_k = top_k
        self.max_distance = max_distance
        self.max_note_chars = max_note_chars

    def search_knowledge(self, query: str, tag: str | None = None) -> str:
        """Семантичний пошук фрагментів нотаток, найближчих до запиту."""
        hits = self.store.search(query, top_k=self.top_k, tag=tag)
        relevant = [h for h in hits if h.distance <= self.max_distance]
        if not relevant:
            best = f"{hits[0].distance:.3f}" if hits else "n/a"
            return (
                f"{NOT_FOUND}: no notes closer than {self.max_distance} "
                f"for query '{query}' (best distance: {best})."
            )

        fragments: list[str] = []
        for h in relevant:
            heading_clean = h.heading.split(" > ")[-1]
            frag = (
                f'<fragment source="[[{h.title}#{heading_clean}]]" path="{h.path}" distance="{h.distance:.3f}">\n'
                f'{strip_wikilinks(h.text)}\n'
                f'</fragment>'
            )
            fragments.append(frag)
        return "\n\n".join(fragments)

    def read_note(self, path: str) -> str:
        """Повний текст нотатки зі сховища, обгорнутий у <note> тег (захист від виходу та Prompt Injection)."""
        try:
            file = resolve_note_path(self.vault, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        except FileNotFoundError:
            return f"{NOT_FOUND}: note '{path}' does not exist"

        note = parse_note(self.vault, file)
        text = strip_wikilinks(note.body)
        if len(text) > self.max_note_chars:
            text = text[:self.max_note_chars] + f"\n... (truncated, total {len(note.body)} chars)"

        tags_str = ", ".join(note.tags)
        links_str = ", ".join(note.links)
        return (
            f'<note source="[[{note.title}]]" path="{note.path}" tags="{tags_str}" links="{links_str}">\n'
            f'{text}\n'
            f'</note>'
        )

    def write_note(self, title: str, content: str, confirmed: bool = False) -> str:
        """Просунута дія: створення нової нотатки виключно в папці Inbox/ з обов'язковим підтвердженням."""
        if not confirmed:
            return "REQUIRES_CONFIRMATION: Дія write_note створює нотатку в Inbox/ і вимагає явного підтвердження людини."
        inbox_dir = self.vault / "Inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{title.strip().replace(' ', '-')}.md"
        target_path = inbox_dir / filename
        note_body = f"""---
tags: [inbox, agent-created]
source: "AI Agent"
updated: {time.strftime('%Y-%m-%d')}
---
# {title}

{content.strip()}
"""
        target_path.write_text(note_body, encoding="utf-8")
        return f"SUCCESS: Нотатку збережено в Inbox/{filename}"

def build_tools(config: KBConfig | None = None) -> KnowledgeTools:
    cfg = config or load_config()
    if cfg.chroma_host:
        client = chromadb.HttpClient(host=cfg.chroma_host, port=cfg.chroma_port)
    else:
        client = chromadb.PersistentClient(path=str(cfg.chroma_path))
    
    # Вибір моделі: GeminiEmbedder якщо задано ключ або MiniLM
    if cfg.embed_model.startswith("gemini") and os.getenv("GEMINI_API_KEY"):
        embedder = GeminiEmbedder(model=cfg.embed_model, dim=cfg.embed_dim)
    else:
        embedder = FallbackMiniLMEmbedder(dimension=cfg.embed_dim, name=cfg.embed_model)

    store = KnowledgeStore(embedder, collection=cfg.collection, path=cfg.chroma_path, client=client)
    return KnowledgeTools(store, vault=cfg.vault_path, top_k=cfg.top_k, max_distance=cfg.max_distance)
