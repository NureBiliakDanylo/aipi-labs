"""Інкрементна індексація сховища Obsidian у Chroma."""
import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
import chromadb
from .config import load_config
from .vault import iter_notes, parse_note
from .chunker import chunk_note
from .embedder import FallbackMiniLMEmbedder
from .store import KnowledgeStore

@dataclass
class IndexReport:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    elapsed_sec: float = 0.0

def index_vault(vault_path: Path, store: KnowledgeStore, rebuild: bool = False) -> IndexReport:
    manifest_path = store.client._system.settings.persist_directory if hasattr(store.client, "_system") else None
    manifest_file = Path(manifest_path or "./chroma_data") / f"{store.collection_name}_manifest.json"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    
    saved_hashes: dict[str, str] = {}
    if not rebuild and manifest_file.exists():
        try:
            saved_hashes = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception:
            saved_hashes = {}

    start_t = time.perf_counter()
    report = IndexReport()
    current_notes = {n.path: n for n in iter_notes(vault_path)}
    new_hashes: dict[str, str] = {}

    # 1. Видалені нотатки
    for old_path in list(saved_hashes.keys()):
        if old_path not in current_notes:
            store.delete_by_note_path(old_path)
            report.deleted += 1

    # 2. Нові та оновлені
    for path, note in current_notes.items():
        new_hashes[path] = note.content_hash
        old_hash = saved_hashes.get(path)
        if old_hash == note.content_hash and not rebuild:
            report.unchanged += 1
            continue

        if old_hash is not None:
            store.delete_by_note_path(path)
            report.updated += 1
        else:
            report.added += 1

        chunks = chunk_note(note)
        store.add_chunks(chunks)

    report.elapsed_sec = round(time.perf_counter() - start_t, 3)
    manifest_file.write_text(json.dumps(new_hashes, indent=2, ensure_ascii=False), encoding="utf-8")
    return report

def main():
    parser = argparse.ArgumentParser(description="Інкрементний індексатор сховища Obsidian")
    parser.add_argument("--rebuild", action="store_true", help="Повна перебудова індексу")
    args = parser.parse_args()

    cfg = load_config()
    print(f"Vault: {cfg.vault_path}")
    print(f"Chroma: {cfg.chroma_path} | Collection: {cfg.collection}")

    if cfg.chroma_host:
        client = chromadb.HttpClient(host=cfg.chroma_host, port=cfg.chroma_port)
    else:
        client = chromadb.PersistentClient(path=str(cfg.chroma_path))

    embedder = FallbackMiniLMEmbedder(dimension=cfg.embed_dim, name=cfg.embed_model)
    store = KnowledgeStore(client, cfg.collection, embedder)

    rep = index_vault(cfg.vault_path, store, rebuild=args.rebuild)
    print(f"Index report: added={rep.added}, updated={rep.updated}, unchanged={rep.unchanged}, deleted={rep.deleted} in {rep.elapsed_sec}s")

if __name__ == "__main__":
    main()
