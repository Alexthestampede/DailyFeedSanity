# AGENTS.md

Guidelines for agentic coding agents operating in this repository.

## Overview

DailyFeedSanity: processes RSS feeds concurrently, downloads webcomics, summarizes news articles with AI (one JSON call per article: title + summary + clickbait/ad verdicts), generates a daily HTML digest in `output/YYYY-MM-DD/index.html`. Version scheme `YYYYMMDD.N` in `src/config.py __version__` (bump `.N` for same-day releases).

## Commands

```bash
./dailyfeedsanity.sh                      # Run the app (uses .venv; sets cwd to project root)
python -m src.main                        # Run the app directly
python -m src.main --feeds <file> --all-entries   # Custom feeds, bypass 24h filter
./dailyfeedsanity.sh --config             # Interactive wizard (also: python -m src.utils.config_wizard)

python scripts/test_response_cleaner.py   # Unit tests: run standalone, NOT via pytest
python scripts/test_json_extractor.py     # (they have __main__ entry points)
python scripts/test_thinking_model_handling.py
python scripts/test_single_article_ornith.py   # Live end-to-end vs remote Ollama

python scripts/sync_modulle.py            # Sync vendored lib/modulle from ~/Aish/ModuLLe
python scripts/sync_modulle.py --check    # Drift report only

ruff check .                              # Lint
black .                                   # Format
```

**Test execution quirk:** many `scripts/test_*.py` are standalone scripts with `main()` functions (some take CLI args like `test_ollama_summarizer.py <url>`). Under pytest, parameter-less functions whose names look like tests but take args (e.g. `test_ollama_connection(server_url)`) get collected and ERROR at setup ("fixture not found"). Run these standalone: `python scripts/<name>.py`. Only `test_response_cleaner.py`, `test_json_extractor.py` (mock-only suites) are deterministic offline tests; the rest need a live Ollama server.

**Install:** `./setup.sh` (creates `.venv`, installs deps, runs wizard) or `pip install -r requirements.txt` + `python -m src.utils.config_wizard`.

## Configuration layering (critical)

Settings resolve: `.config.json` (wizard-written) → env vars → `src/config.py` defaults.

- User settings live in `.config.json` (NOT committed): `ai_provider`, `text_model`, `vision_model`, `ollama_base_url`, `enable_ad_detection`, `request_timeout`, `decision_model`, API keys.
- To change AI model/provider/timeout/ad-detection, update `.config.json` via wizard options [1]-[3], [14] toggle ad detection, [15] set request timeout, [16] set decision model - or edit the JSON directly.
- `request_timeout` (default 30s): HTTP fetches use it directly; **AI generation calls use 3x**. Raise to 300+ for large local models.
- `ENABLE_AD_DETECTION` in `src/config.py` is only the *default*; the per-instance setting from `.config.json` (`enable_ad_detection`) is what actually gates detection at runtime. Don't "fix" this by reading the constant at the call site.

## Architecture notes

- **Two AI layers:** `lib/modulle` (vendored generic abstraction, upstream: github.com/Alexthestampede/ModuLLe) provides `BaseAIClient`/`BaseTextProcessor`; `src/ai_client/` wraps it with domain logic (`DomainTextProcessor`: summarization, clickbait/ad detection). Keep application logic in `src/`, keep ModuLLe generic.
- **Two-stage processing (optional):** with `decision_model` set in `.config.json` (nimble/clef/d1k32 decision models on Ollama >= 0.35.1), verdicts come from one `/v1/systemone` request as direct `noul` probabilities (no generative JSON parsing, no CoT risk); the generative call then produces only summary+title. Without it, verdicts ride in the single JSON call. Threshold: `DECISION_VERDICT_THRESHOLD` in `src/config.py` (0.7); probabilities included in result dicts as `clickbait_probability`/`ad_probability`.
- **News flow:** extract (trafilatura) → single JSON call (title+summary, + verdicts when no decision model) → fallback to legacy 4-call path if JSON parse fails. Detection prompts use only the first 1000 chars; summarization the first 10,000.
- **Vendored copy diverges from upstream by import style only:** upstream uses absolute `from modulle.x import y` (assumes pip install); vendored uses package-relative (`from ...utils.x import`). After every sync, run `scripts/sync_modulle.py` which rewrites imports automatically. Hand-editing vendored files risks divergence - port changes upstream first, then sync.
- **Import-masking trap:** a stale `pip install -e` of ModuLLe 0.1.0 can satisfy `import modulle` in a dev shell and mask broken vendored imports. Verify with `sys.modules['modulle'] = None` before imports (sync script does this). The app's `.venv` has no such shadow.
- **Concurrency:** feed fetching is parallel (`ThreadPoolExecutor`, `MAX_CONCURRENT_FEEDS=10`); article processing is sequential per article (4 AI calls → 1 with single-call workflow). This is the bottleneck, not fetching.
- **Error visibility:** feed-level errors AND failed articles/comics all roll into the digest's Errors section and the end-of-run log. `success: False` results must not be silently dropped.

## Thinking models (hard-won)

Models like Qwen3/Qwen3.8/Nemotron/Ornith emit chain-of-thought either in `thought` tags or as plain text ("We need answer...", "The user wants me to..."). Handling lives in `lib/modulle/utils/response_cleaner.py` (tag stripping, reasoning detection, strict `parse_yes_no`) and `lib/modulle/utils/json_extractor.py` (extracts JSON from fenced/preamble/reasoning-wrapped responses). Provider clients and `DomainTextProcessor` both clean defensively. Never parse detection verdicts with `"yes" in response` - reasoning mentioning "yes" in passing flags everything.

**Ollama generation must go through `/api/chat`** (`OllamaTextProcessor.generate()` routes there): `/api/generate` truncates mid-response and leaks CoT with chat-template models. This was a production bug (logs/thehorror.html precedent).

## Live testing rules

- **Max 5 articles per live test run.** Use a trimmed feed file + `--all-entries`, or interrupt after 5. Never launch full `--all-entries` against a 59-entry feed as a "test".
- Live tests hit the user's remote Ollama (`http://192.168.2.150:11434` per `.config.json`) - a shared machine. Local `localhost:11434` may not have the same models.
- To get the current date: `date +%Y-%m-%d` (matches output-folder naming `YYYY-MM-DD`).

## Code style

- Python 3.8+: type hints on all params/returns, Google-style docstrings on public functions/classes
- `snake_case` functions/vars, `PascalCase` classes, `UPPER_CASE` constants, `_underscore` privates
- Imports: standard → third-party → local; explicit names (no `import *`)
- Logging: `from ..utils.logging_config import get_logger; logger = get_logger(__name__)` - never `print()` in `src/`
- Specific exception types, no bare `except:`; log-and-return-None is the established error style in AI-layer code
- Secrets only via env vars (`OPENAI_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_API_KEY`); never commit keys or `.config.json`

## Version bump checklist

1. `__version__` in `src/config.py`
2. Run offline test suites (3 standalone scripts above)
3. If touching `lib/modulle`: run `python scripts/sync_modulle.py --check` first; port changes upstream, then sync
4. One small live run (≤5 articles) if AI-behavior code changed