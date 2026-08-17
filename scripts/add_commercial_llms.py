#!/usr/bin/env python3
"""Merge commercially licensed open LLMs into data/open-models.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "open-models.json"

# One representative checkpoint per family from the commercial-use open LLM list.
# Datasets / evals are omitted.
NEW = [
    ("Google", "google-t5-large", "T5"),
    ("Google", "google-flan-t5-xxl", "Flan-T5"),
    ("RWKV", "rwkv-rwkv-4", "RWKV 4"),
    ("Yandex", "yandex-yalm-100b", "YaLM-100B"),
    ("BigScience", "bigscience-bloom", "BLOOM"),
    ("THUDM", "thudm-chatglm-6b", "ChatGLM"),
    ("Cerebras", "cerebras-cerebras-gpt-1.3b", "Cerebras-GPT"),
    ("OpenAssistant", "openassistant-pythia-12b", "Open Assistant"),
    ("EleutherAI", "eleutherai-pythia-12b", "Pythia"),
    ("Databricks", "databricks-dolly-v2-12b", "Dolly"),
    ("Stability AI", "stabilityai-stablelm-base-alpha-7b", "StableLM-Alpha"),
    ("LMSYS", "lmsys-fastchat-t5-3b", "FastChat-T5"),
    ("CambioML", "cambiaml-dlite-v2-1.5b", "DLite"),
    ("H2O.ai", "h2oai-h2ogpt", "h2oGPT"),
    ("Databricks", "mosaicml-mpt-7b", "MPT-7B"),
    ("Together", "together-redpajama-incite-7b", "RedPajama-INCITE"),
    ("OpenLM", "openlm-open-llama-7b", "OpenLLaMA"),
    ("TII", "tii-falcon-40b", "Falcon"),
    ("Databricks", "mosaicml-mpt-30b", "MPT-30B"),
    ("Meta", "meta-llama-2-7b", "Llama 2"),
    ("THUDM", "thudm-chatglm2-6b", "ChatGLM2"),
    ("Salesforce", "salesforce-xgen-7b-8k", "XGen-7B"),
    ("Inception", "inception-jais-13b", "Jais-13B"),
    ("Nous", "nous-openhermes-7b", "OpenHermes"),
    ("Mistral", "mistralai-mistral-7b-v0.1", "Mistral 7B"),
    ("THUDM", "thudm-chatglm3-6b", "ChatGLM3"),
    ("Skywork", "skywork-skywork-13b", "Skywork"),
    ("Inception", "inception-jais-30b", "Jais-30B"),
    ("Hugging Face", "huggingface-zephyr-7b", "Zephyr"),
    ("DeepSeek", "deepseek-deepseek-llm-7b-base", "DeepSeek LLM 7B"),
    ("Mistral", "mistralai-mistral-7b-instruct-v0.2", "Mistral 7B v0.2"),
    ("Mistral", "mistralai-mixtral-8x7b-v0.1", "Mixtral 8x7B"),
    ("LLM360", "llm360-amber", "LLM360 Amber"),
    ("Upstage", "upstage-solar-10.7b", "SOLAR"),
    ("Microsoft", "microsoft-phi-2", "Phi-2"),
    ("BSC", "bsc-flor-6.3b", "FLOR"),
    ("RWKV", "rwkv-rwkv-5", "RWKV 5"),
    ("Allen AI", "allenai-olmo-7b", "OLMo"),
    ("Qwen", "qwen-qwen1.5-7b", "Qwen1.5"),
    ("LWM", "lwm-lwm-text-chat-128k", "LWM"),
    ("Google", "google-gemma-7b", "Gemma 7B"),
    ("xAI", "xai-grok-1", "Grok-1"),
    ("Qwen", "qwen-qwen1.5-moe-a2.7b", "Qwen1.5 MoE"),
    ("AI21", "ai21-jamba-v0.1", "Jamba 0.1"),
    ("Qwen", "qwen-qwen1.5-32b", "Qwen1.5 32B"),
    ("TRI", "tri-mamba-7b", "Mamba-7B"),
    ("Mistral", "mistralai-mixtral-8x22b-v0.1", "Mixtral 8x22B"),
    ("Microsoft", "microsoft-phi-3-mini", "Phi-3 Mini"),
    ("Apple", "apple-openelm-3b", "OpenELM"),
    ("Snowflake", "snowflake-arctic", "Snowflake Arctic"),
    ("Qwen", "qwen-qwen1.5-110b", "Qwen1.5 110B"),
    ("RWKV", "rwkv-rwkv-6", "RWKV 6"),
    ("DeepSeek", "deepseek-deepseek-v2", "DeepSeek-V2"),
    ("Fujitsu", "fujitsu-fugaku-llm-13b", "Fugaku-LLM"),
    ("TII", "tii-falcon-2-11b", "Falcon 2"),
    ("01.AI", "01ai-yi-1.5-9b", "Yi-1.5"),
    ("DeepSeek", "deepseek-deepseek-v2-lite", "DeepSeek-V2-Lite"),
    ("Microsoft", "microsoft-phi-3-medium", "Phi-3 Medium"),
    ("YuLan", "yulan-yulan-mini", "YuLan-Mini"),
    ("Atla", "atla-selene-mini", "Selene Mini"),
    ("BigCode", "bigcode-santacoder", "SantaCoder"),
    ("Salesforce", "salesforce-codegen2-7b", "CodeGen2"),
    ("BigCode", "bigcode-starcoder", "StarCoder"),
    ("Hugging Face", "huggingface-starchat-alpha", "StarChat Alpha"),
    ("Replit", "replit-replit-code-v1-3b", "Replit Code"),
    ("Salesforce", "salesforce-codet5p-6b", "CodeT5+"),
    ("Salesforce", "salesforce-codegen25-7b", "CodeGen2.5"),
    ("Deci", "deci-decicoder-1b", "DeciCoder"),
    ("Meta", "meta-codellama-7b", "Code Llama"),
]


def compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_name = {p["name"]: p for p in catalog["providers"]}
    existing_ids = {m["id"] for p in catalog["providers"] for m in p["models"]}
    existing_names = {compact(m["name"]) for p in catalog["providers"] for m in p["models"]}

    added = 0
    for provider, mid, name in NEW:
        if mid in existing_ids or compact(name) in existing_names:
            continue
        group = by_name.get(provider)
        if not group:
            group = {"name": provider, "models": []}
            catalog["providers"].append(group)
            by_name[provider] = group
        group["models"].append({"id": mid, "name": name})
        existing_ids.add(mid)
        existing_names.add(compact(name))
        added += 1

    for group in catalog["providers"]:
        group["models"].sort(key=lambda m: m["name"].lower())
    catalog["providers"].sort(key=lambda p: (-len(p["models"]), p["name"].lower()))
    catalog["count"] = sum(len(p["models"]) for p in catalog["providers"])
    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"Added {added} models; catalog now {catalog['count']} across {len(catalog['providers'])} providers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
