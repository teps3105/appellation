#!/usr/bin/env python3
"""Group assistant responses by their opening token and compute mechanical quality
indicators over local agent-platform conversation databases.

Groups: self-appellation (a fixed fictional agent name), user-addressing, first-person
("I"), second-person ("you"), other. Indicators: sycophantic opening (agreement phrase
with zero tool calls in the turn), mean length, simplified-glyph evidence, English
opening, and role confusion (addressing the user right after a tool result).

Sources (override with environment variables):
  CLAUDE_DB   path to the Claude Code conversation database or project dir (default:
              ~/.claude/projects, scanned as JSONL)
  CODEX_DB    path to the Codex thread-history SQLite (default:
              ~/.codex/thread_history_1.sqlite)
  ZCODE_DB    path to the ZCode conversation SQLite (default:
              ~/.zcode/cli/db/db.sqlite)
  AGENT_NAME  the registered self-appellation token (default: derived per message text)

Usage:  python opening_stats.py
The script reads local databases only and prints aggregate statistics; it sends nothing
anywhere and stores no conversation content.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

# Agreement phrases for the sycophantic-opening criterion (extend as needed).
AGREE_OPENERS = (
    'right', 'exactly', 'correct', 'agreed', 'indeed', 'good point', 'makes sense',
    'you\'re right', 'that\'s right',
    '對', '正確', '沒錯', '有道理', '同意', '說得對', '正是', '原來如此', '一語中的',
)

HOME = Path.home()


def group_of(text: str, agent_name: str) -> str:
    head = ''
    for line in (text or '').splitlines():
        stripped = re.sub(r'^(?:[\s#*_\-]|\d+[.)]\s)+', '', line)
        if stripped:
            head = stripped
            break
    if agent_name and head.startswith(agent_name):
        return 'self-appellation'
    if head.startswith('你') or head.startswith('您'):
        return 'you'
    if head.startswith('我'):
        return 'I'
    if head.startswith('老闆') or head.lower().startswith('boss'):
        return 'addressee'
    return 'other'


def is_english_opening(text: str) -> bool:
    for line in (text or '').splitlines():
        stripped = line.strip()
        if stripped:
            return bool(re.match(r'^[A-Za-z]', stripped))
    return False


def sycophantic_opening(text: str) -> bool:
    head = ''
    for line in (text or '').splitlines():
        stripped = re.sub(r'^(?:[\s#*_\-]|\d+[.)]\s)+', '', line)
        if stripped:
            head = stripped
            break
    low = head.lower()
    return any(p in low for p in AGREE_OPENERS)


def new_stats():
    return {k: dict(n=0, chars=0, syc=0, eng=0, tool_n=0, tool_addr=0)
            for k in ('self-appellation', 'addressee', 'I', 'you', 'other')}


def count(text: str, stats, ctx, agent_name):
    key = group_of(text, agent_name)
    s = stats[key]
    s['n'] += 1
    s['chars'] += len(text)
    if sycophantic_opening(text):
        s['syc'] += 1
    if is_english_opening(text):
        s['eng'] += 1
    if ctx == 'tool':
        s['tool_n'] += 1
        if key in ('you', 'addressee'):
            s['tool_addr'] += 1


def collect_claude(root: Path, stats, agent_name):
    n = 0
    for path in root.glob('**/*.jsonl'):
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            if '"assistant"' not in line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            msg = entry.get('message') or {}
            content = msg.get('content')
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'text' and str(block.get('text', '')).strip():
                        count(block['text'], stats, 'human', agent_name)
                        n += 1
                        break
    return n


def collect_zcode(db: Path, stats, agent_name):
    n = 0
    if not db.is_file():
        return n
    con = sqlite3.connect(str(db))
    rows = con.execute(
        "SELECT m.session_id, m.id, json_extract(m.data,'$.role'), p.data, "
        "json_extract(p.data,'$.type') FROM message m JOIN part p ON p.message_id=m.id "
        "WHERE json_extract(m.data,'$.role') IN ('assistant','user') "
        "ORDER BY m.session_id, m.id, p.sequence")
    ctx, counted, last_id, last_sid = 'human', False, None, None
    for sid, mid, role, data, ptype in rows:
        if sid != last_sid:
            last_sid, ctx = sid, 'human'
        if mid != last_id:
            last_id, counted = mid, False
        try:
            item = json.loads(data)
        except ValueError:
            continue
        if role == 'user':
            toolish = 'tool' in (ptype or '') or 'tool' in json.dumps(item)[:80]
            if toolish:
                ctx = 'tool'
            elif (ptype or '') == 'text' and str(item.get('text', '')).strip():
                ctx = 'human'
        elif role == 'assistant' and not counted:
            text = item.get('text')
            if isinstance(text, str) and text.strip():
                counted = True
                count(text, stats, ctx, agent_name)
                n += 1
    con.close()
    return n


CODEX_TOOL_TYPES = ('commandExecution', 'functionCallOutput', 'mcpToolCall', 'webSearch',
                    'fileChange', 'dynamicToolCall', 'imageGeneration', 'collabAgentToolCall')


def collect_codex(db: Path, stats, agent_name):
    n = 0
    if not db.is_file():
        return n
    con = sqlite3.connect(str(db))
    rows = con.execute(
        'SELECT thread_id, item_type, item_json FROM thread_items '
        'ORDER BY thread_id, created_at_ms, rollout_ordinal')
    ctx, last_tid = 'human', None
    for tid, itype, j in rows:
        if tid != last_tid:
            last_tid, ctx = tid, 'human'
        if itype in CODEX_TOOL_TYPES:
            ctx = 'tool'
        elif itype == 'userMessage':
            d = json.loads(j)
            texts = [b.get('text', '') for b in (d.get('content') or [])
                     if isinstance(b, dict) and b.get('type') == 'text']
            if any(t.strip() for t in texts):
                ctx = 'human'
        elif itype == 'agentMessage':
            d = json.loads(j)
            t = d.get('text')
            if isinstance(t, str) and t.strip():
                count(t, stats, ctx, agent_name)
                n += 1
    con.close()
    return n


def report(name, n, stats):
    print('== %s: %d assistant responses ==' % (name, n))
    for key, s in stats.items():
        if not s['n']:
            continue
        rate = lambda k: '%.1f%%' % (100.0 * s[k] / s['n'])
        conf = ('%.1f%%' % (100.0 * s['tool_addr'] / s['tool_n'])) if s['tool_n'] else '-'
        print('  %-16s n=%-7d chars=%-5d syc=%-6s conf=%-7s eng=%s' % (
            key, s['n'], s['chars'] / s['n'], rate('syc'), conf, rate('eng')))


def main():
    agent_name = os.environ.get('AGENT_NAME', '')
    claude = Path(os.environ.get('CLAUDE_PROJECTS', str(HOME / '.claude' / 'projects')))
    codex = Path(os.environ.get('CODEX_DB', str(HOME / '.codex' / 'thread_history_1.sqlite')))
    zcode = Path(os.environ.get('ZCODE_DB', str(HOME / '.zcode' / 'cli' / 'db' / 'db.sqlite')))

    s_claude, n_claude = new_stats(), 0
    if claude.exists():
        n_claude = collect_claude(claude, s_claude, agent_name)
        report('claude', n_claude, s_claude)
    s_codex, n_codex = new_stats(), 0
    if codex.exists():
        n_codex = collect_codex(codex, s_codex, agent_name)
        report('codex', n_codex, s_codex)
    s_zcode, n_zcode = new_stats(), 0
    if zcode.exists():
        n_zcode = collect_zcode(zcode, s_zcode, agent_name)
        report('zcode', n_zcode, s_zcode)


if __name__ == '__main__':
    main()
