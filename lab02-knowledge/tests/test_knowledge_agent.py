import pytest
from pathlib import Path
import chromadb
from kb.vault import parse_note, resolve_note_path, Note
from kb.chunker import chunk_note
from kb.embedder import HashEmbedder
from kb.store import KnowledgeStore, EmbedderMismatch
from kb.indexer import index_vault
from kb.tools import KnowledgeTools
from kb.config import KBConfig
from agent.validator import validate_decision
from agent.errors import DecisionError
from agent.loop import run_agent

@pytest.fixture
def tmp_vault(tmp_path: Path):
    v = tmp_path / "vault"
    v.mkdir()
    (v / "01-folder").mkdir()
    
    note1 = """---
tags: [тест, архітектура]
aliases: [T1]
source: "Test Source"
updated: 2026-11-01
---
# Перша тестова нотатка

Опис сутності для модульного тесту.

## Розділ один
Детальний зміст розділу один. Посилання на [[Друга нотатка]].

## Розділ два
Зміст другого розділу для перевірки розбиття.
"""
    (v / "01-folder" / "Перша-нотатка.md").write_text(note1, encoding="utf-8")
    
    note2 = """---
tags: [тест, безпека]
aliases: [T2]
source: "Source 2"
updated: 2026-11-01
---
# Друга нотатка

Зміст другої нотатки про безпеку та токени.

## Авторизація
Опис механізмів авторизації.
"""
    (v / "01-folder" / "Друга-нотатка.md").write_text(note2, encoding="utf-8")
    return v

@pytest.fixture
def tmp_store(tmp_path: Path):
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma_data"))
    embedder = HashEmbedder(dimension=64)
    return KnowledgeStore(client, "test_collection", embedder)

# 1. Тест читання властивостей і посилань
def test_parse_note_properties_and_links(tmp_vault):
    file = tmp_vault / "01-folder" / "Перша-нотатка.md"
    note = parse_note(tmp_vault, file)
    assert note.title == "Перша тестова нотатка"
    assert "тест" in note.tags
    assert "архітектура" in note.tags
    assert "Друга нотатка" in note.links
    assert note.aliases == ["T1"]
    assert note.content_hash != ""

# 2. Тест захисту від виходу за межі сховища (Path Traversal)
def test_resolve_note_path_security(tmp_vault):
    p = resolve_note_path(tmp_vault, "Перша-нотатка")
    assert p.is_file()

    with pytest.raises(ValueError, match="Спроба виходу за межі сховища"):
        resolve_note_path(tmp_vault, "../../etc/passwd")

    with pytest.raises(FileNotFoundError):
        resolve_note_path(tmp_vault, "Неіснуюча-нотатка")

# 3. Тест розбиття за заголовками Markdown
def test_chunking_by_headings(tmp_vault):
    file = tmp_vault / "01-folder" / "Перша-нотатка.md"
    note = parse_note(tmp_vault, file)
    chunks = chunk_note(note)
    assert len(chunks) == 3
    sections = [c.section for c in chunks]
    assert "Перша тестова нотатка" in sections
    assert "Розділ один" in sections
    assert "Розділ два" in sections
    assert all("Перша-нотатка.md::" in c.id for c in chunks)

# 4. Тест інкрементної індексації (додавання, незмінність, оновлення, видалення)
def test_incremental_indexing(tmp_vault, tmp_store):
    rep1 = index_vault(tmp_vault, tmp_store)
    assert rep1.added == 2
    assert rep1.unchanged == 0

    rep2 = index_vault(tmp_vault, tmp_store)
    assert rep2.added == 0
    assert rep2.unchanged == 2

    f = tmp_vault / "01-folder" / "Перша-нотатка.md"
    f.write_text(f.read_text(encoding="utf-8") + "\nНовий рядок для зміни хешу.", encoding="utf-8")
    rep3 = index_vault(tmp_vault, tmp_store)
    assert rep3.updated == 1
    assert rep3.unchanged == 1

    (tmp_vault / "01-folder" / "Друга-нотатка.md").unlink()
    rep4 = index_vault(tmp_vault, tmp_store)
    assert rep4.deleted == 1
    assert rep4.unchanged == 1

# 5. Тест пошуку з фільтром за тегом
def test_search_with_tag_filter(tmp_vault, tmp_store):
    index_vault(tmp_vault, tmp_store)
    res_arch = tmp_store.search("тест", tag="архітектура")
    assert len(res_arch) > 0
    for r in res_arch:
        assert "архітектура" in r.chunk.tags

    res_sec = tmp_store.search("тест", tag="безпека")
    assert len(res_sec) > 0
    for r in res_sec:
        assert "безпека" in r.chunk.tags

# 6. Тест порогу релевантності та повернення маркера NOT_FOUND
def test_threshold_and_not_found(tmp_vault, tmp_store):
    index_vault(tmp_vault, tmp_store)
    tools = KnowledgeTools(tmp_store, vault=tmp_vault, max_distance=0.01)
    obs = tools.search_knowledge("абсолютно невідомий сторонній запит XYZ")
    assert "NOT_FOUND" in obs

# 7. Тест валідатора простору дій (відхилення невідомої дії та аргументів)
def test_validator_rejects_invalid_actions():
    # Валідна дія
    validate_decision({"action": "search_knowledge", "arguments": {"query": "тест"}})
    
    # Невідома дія
    with pytest.raises(DecisionError, match="unknown action"):
        validate_decision({"action": "bash_exec", "arguments": {"command": "rm -rf"}})

    # Відсутній обов'язковий аргумент
    with pytest.raises(DecisionError, match="missing arguments for read_note"):
        validate_decision({"action": "read_note", "arguments": {}})

# 8. Тест зупинки агента за лімітом кроків MAX_STEPS
def test_agent_max_steps_termination(tmp_vault, tmp_store):
    index_vault(tmp_vault, tmp_store)
    tools = KnowledgeTools(tmp_store, vault=tmp_vault)

    loop_decider = lambda goal, obs, step, max_s: {
        "action": "search_knowledge",
        "arguments": {"query": "нескінченний цикл"},
        "decision_summary": "продовжую пошук"
    }

    state = run_agent("Тестова ціль", tools, decision_fn=loop_decider, max_steps=3)
    assert state.status == "MAX_STEPS_EXCEEDED"
    assert len(state.steps) == 3

# 9. Тест захисту від EmbedderMismatch при зміні розмірності
def test_embedder_mismatch_detection(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma_mismatch"))
    emb1 = HashEmbedder(dimension=32, name="hash-32")
    KnowledgeStore(client, "strict_col", emb1)

    emb2 = HashEmbedder(dimension=64, name="hash-64")
    with pytest.raises(EmbedderMismatch, match="collection 'strict_col' was built with hash-32"):
        KnowledgeStore(client, "strict_col", emb2)

# 10. Тест просунутої дії write_note (Human-in-the-loop)
def test_write_note_requires_confirmation(tmp_vault, tmp_store):
    tools = KnowledgeTools(tmp_store, vault=tmp_vault)

    res1 = tools.write_note("Нова замітка", "Контент", confirmed=False)
    assert "REQUIRES_CONFIRMATION" in res1
    assert not (tmp_vault / "Inbox" / "Нова-замітка.md").exists()

    res2 = tools.write_note("Нова замітка", "Контент", confirmed=True)
    assert "SUCCESS" in res2
    assert (tmp_vault / "Inbox" / "Нова-замітка.md").exists()
