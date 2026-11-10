# Forcing a Registered Self-Appellation at the Response Opening

Mechanism study: forcing an LLM agent to open every response with its registered
self-appellation, enforced by four layers of host hooks, and a grouped empirical study
over 358k assistant responses across three agent platforms (Claude Code, Codex, ZCode).

> [!TIP]
> 中文說明見 [README.zh-TW.md](README.zh-TW.md)。論文有英文與繁中兩版（見下）。

## Paper

| Language | Source | PDF |
|---|---|---|
| English (default) | [`main.tex`](main.tex) | `xelatex main.tex` → `main.pdf` |
| 繁體中文 | [`main-zh-TW.tex`](main-zh-TW.tex) | `xelatex main-zh-TW.tex` → `main-zh-TW.pdf` |

Both versions carry the same content and the same corpus snapshot. Preprint PDFs are
rendered from the sources above; no other artifacts are distributed.

## TL;DR

Two recurring low-quality patterns in agent responses—sycophancy (endorsement without
verification) and role confusion (addressing tool output as "you")—are suppressed by a
zero-cost mechanism: force every response to open with the agent's registered
self-appellation, enforced by four layers of host hooks.

Key results (see Table 2 in the paper):

- Self-appellation group: 9,255 responses, **zero** sycophancy rate across all platforms.
- Second-person openings and sycophancy co-occur strongly, replicated across platforms:
  **40.9%** (Codex, n=931) and **46.6%** (ZCode, n=408).
- Role confusion (addressing the user right after a tool result) is near **100%** in the
  addressee and second-person groups; zero in the self-appellation and first-person groups.

## Reproduction

`code/opening_stats.py` regenerates the opening-group statistics from local
conversation databases. It reads local data only; nothing is uploaded.

```sh
python code/opening_stats.py                 # default platform paths
AGENT_NAME="YourAgent" python code/opening_stats.py   # set the registered name
CLAUDE_PROJECTS=... CODEX_DB=... ZCODE_DB=... python code/opening_stats.py
```

Requirements: Python 3.10+, standard library only. The script prints aggregate
statistics and stores no conversation content.

The sycophancy-classification criteria in the study are shared with the production
enforcement guards (same module), so measurement and enforcement cannot drift apart.

## Citation

If this study is useful to you, please cite the paper:

```bibtex
@misc{shiduki2026appellation,
  author       = {Shiduki},
  title        = {Forcing a Registered Self-Appellation at the Response Opening
                  Reduces LLM-Agent Sycophancy and Role Confusion:
                  Mechanism Design and a Large-Scale Empirical Study Across Agent Platforms},
  year         = {2026},
  howpublished = {\url{https://github.com/teps3105/agent-opening-appellation-study}},
  note         = {Draft; in Chinese (main-zh-TW.tex) and English (main.tex)}
}
```

## License

CC BY 4.0 for the paper text; the reproduction script is MIT.
