"""Параметри бази знань. Значення читаються з .env, у коді лише типові."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class KBConfig:
    vault_path: Path
    chroma_path: Path
    collection: str = "obsidian_kb"
    embed_model: str = "all-MiniLM-L6-v2"
    embed_dim: int = 384
    chunk_chars: int = 1200
    top_k: int = 4
    max_distance: float = 0.55
    chroma_host: str = ""
    chroma_port: int = 8000

def load_config() -> KBConfig:
    vault = os.getenv("OBSIDIAN_VAULT", "../kb-vault")
    base_dir = Path(__file__).resolve().parent.parent
    vault_path = (base_dir / vault).resolve() if not Path(vault).is_absolute() else Path(vault).resolve()
    
    if not vault_path.is_dir():
        # fallback search
        alt_vault = Path(r"c:\7 sem\Ші\kb-vault").resolve()
        if alt_vault.is_dir():
            vault_path = alt_vault
        else:
            raise RuntimeError(f"Сховище не знайдено: {vault_path}")

    chroma_raw = os.getenv("CHROMA_PATH", "./chroma_data")
    chroma_path = (base_dir / chroma_raw).resolve() if not Path(chroma_raw).is_absolute() else Path(chroma_raw).resolve()

    return KBConfig(
        vault_path=vault_path,
        chroma_path=chroma_path,
        collection=os.getenv("KB_COLLECTION", "obsidian_kb"),
        embed_model=os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"),
        embed_dim=int(os.getenv("EMBED_DIM", "384")),
        chunk_chars=int(os.getenv("CHUNK_CHARS", "1200")),
        top_k=int(os.getenv("KB_TOP_K", "4")),
        max_distance=float(os.getenv("KB_MAX_DISTANCE", "0.55")),
        chroma_host=os.getenv("CHROMA_HOST", ""),
        chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
    )
