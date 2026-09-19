from __future__ import annotations

import re


_TECHNICAL_TOKEN = re.compile(
    r"[A-Za-z0-9]+(?:[./_\\-][A-Za-z0-9]+)*"
)
_CAMEL_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_WORD_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")


def code_aware_tokens(text: str) -> list[str]:
    """确定性拆分代码/日志 token，不使用 stopwords、stemming 或隐藏 NLP 状态。

    每个 technical compound 既保留 lowercase 原形，也按路径/点/下划线/连字符和
    camelCase 拆出子词；compound 内去重但保留出现顺序。相同函数同时处理 document
    与 query，避免两套 tokenizer 造成无法解释的 lexical mismatch。
    """
    tokens: list[str] = []
    for match in _TECHNICAL_TOKEN.finditer(text):
        raw_compound = match.group(0)
        compound_tokens: list[str] = []
        _append_unique(compound_tokens, raw_compound.casefold())
        slash_parts = re.split(r"[/\\]", raw_compound)
        for slash_part in slash_parts:
            _append_unique(compound_tokens, slash_part.casefold())
            atomic_parts = re.split(r"[._-]", slash_part)
            for atomic_part in atomic_parts:
                if not atomic_part:
                    continue
                _append_unique(compound_tokens, atomic_part.casefold())
                camel = _CAMEL_ACRONYM_BOUNDARY.sub(r"\1 \2", atomic_part)
                camel = _CAMEL_WORD_BOUNDARY.sub(r"\1 \2", camel)
                for subtoken in camel.split():
                    _append_unique(compound_tokens, subtoken.casefold())
        tokens.extend(compound_tokens)
    return tokens


def _append_unique(tokens: list[str], token: str) -> None:
    if token and token not in tokens:
        tokens.append(token)
