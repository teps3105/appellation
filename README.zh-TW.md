# 強制回應開頭自我稱謂的機制研究

[English](README.md) ｜ 繁體中文

強制 LLM 代理以固定自我稱謂開頭的機制研究。橫跨三個代理平台（Claude Code、Codex、
ZCode），實證樣本為 35.8 萬則對話回應的分組統計。

## 論文

| 語言 | 原始碼 | PDF |
|---|---|---|
| English（預設） | [`main.tex`](main.tex) | `xelatex main.tex` → `main.pdf` |
| 繁體中文 | [`main-zh-TW.tex`](main-zh-TW.tex) | `xelatex main-zh-TW.tex` → `main-zh-TW.pdf` |

兩版內容與語料快照相同。PDF 由上述原始碼渲染，不另外散布編譯產物。

## 摘要

代理回應的兩類低品質模式需要壓制。附和指未查證先表態認同。角色混淆指對工具輸出稱「你」。
機制是零成本的：強制每則回應以代理登記的固定自我稱謂開頭，並由四層宿主 hook 守衛保證執行。
實測結果分三點。自我稱謂組 9,255 則附和率為零。第二人稱開頭與附和的強共現跨平台成立，
Codex 40.9%、ZCode 46.6%。角色混淆在對象稱謂組與第二人稱組近乎 100%。

## 復現

`code/opening_stats.py` 從本機對話資料庫重算開頭分組統計。腳本只讀本機資料，不上傳任何內容。

```sh
python code/opening_stats.py                 # 預設平台路徑
AGENT_NAME="YourAgent" python code/opening_stats.py   # 設定登記的代理名
CLAUDE_PROJECTS=... CODEX_DB=... ZCODE_DB=... python code/opening_stats.py
```

需求：Python 3.10+，只用標準庫。腳本輸出聚合統計，不儲存任何對話內容。
研究中的附和分類判準與線上執行守衛共用同一模組，測量與執行不會漂移。

## 引用

若這份研究對你有用，歡迎引用論文：

```bibtex
@misc{shiduki2026appellation,
  author       = {Shiduki},
  title        = {Forcing a Registered Self-Appellation at the Response Opening
                  Reduces LLM-Agent Sycophancy and Role Confusion:
                  Mechanism Design and a Large-Scale Empirical Study Across Agent Platforms},
  year         = {2026},
  howpublished = {\url{https://github.com/teps3105/agent-opening-appellation-study}},
  note         = {Draft; 繁中（main-zh-TW.tex）與英文（main.tex）雙語版}
}
```

## 授權

論文文字以 CC BY 4.0 釋出；復現腳本以 MIT 釋出。
