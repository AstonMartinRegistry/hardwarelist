#!/usr/bin/env python3
"""Build locallist.html from liked hardware-setups picks.

Each box shows the person's hardware, model, quant, speed, pp, ts and leftover
message text, plus enrichment links:
  - benchmarklist.com model page + tracked-benchmark count
  - Hugging Face link for the model + quant
  - hardware price source: pcpartpicker trends (tracked cards) or eBay recently sold
"""

from __future__ import annotations

import html
import json
import re
import shutil
import urllib.parse
from pathlib import Path

from paths import DATA, OUTPUT, liked_canvas_data

LIKED = liked_canvas_data()
SETUPS = DATA / "hardware-setups.json"
BL_STATS = DATA / "benchmarklist-stats.json"
EBAY_PRICES = DATA / "ebay-prices.json"
OUT = OUTPUT / "locallist.html"
INDEX_OUT = OUTPUT / "index.html"
HAMSTERS_OUT = OUTPUT / "hamsters.html"
HAMSTERS_HERO = OUTPUT / "hamsters-hero.jpg"
HAMSTERS_HERO_SRC = Path(__file__).resolve().parent.parent / "assets" / "hamsters-hero.jpg"

_EBAY_CACHE: dict | None = None

# model slug (lowercased) -> (benchmarklist page slug, tracked benchmark count, approx?)
BENCHMARKLIST = {
    "qwen3.6-27b": ("qwen-qwen3.6-27b", 50, False),
    "qwen3.6-35b-a3b": ("qwen-qwen3.6-35b-a3b", 45, False),
    "qwen3.5-27b": ("qwen-qwen3.5-27b", 86, False),
    "qwen3.5-9b": ("qwen-qwen3.5-9b", 87, False),
    "qwen-3.5-9b": ("qwen-qwen3.5-9b", 87, False),
    "qwen3.5-35b": ("qwen-qwen3.5-35b-a3b", 58, True),
    "qwen3.5-35b-a3b": ("qwen-qwen3.5-35b-a3b", 58, False),
    "unsloth/3.5 35b q8": ("qwen-qwen3.5-35b-a3b", 58, True),
    "qwen3.5-122b": ("qwen-qwen3.5-122b-a10b", 49, False),
    "qwen3.5-397b": ("qwen-qwen3.5-397b-a17b", 127, False),
    "qwen3-coder-next": ("qwen-qwen3-coder-next", 37, False),
    "qwen3.5-0.8b": ("qwen-qwen3.5-0.8b", 34, False),
    "qwen3-coder-0.8": ("qwen-qwen3.5-0.8b", 34, False),
    "glm-4": ("z-ai-glm-4.5", 49, True),
    "glm 4.5": ("z-ai-glm-4.5", 49, False),
    "glm-4.5": ("z-ai-glm-4.5", 49, False),
    "glm-4.7": ("z-ai-glm-4.7", 93, False),
    "glm-5.2": ("z-ai-glm-5.2", 57, False),
    "minimax-m2.5": ("minimax-minimax-m2.5", 78, False),
    "gemma4-31b": ("google-gemma-4-31b-it", 118, False),
    "gemma 4 31b": ("google-gemma-4-31b-it", 118, False),
    "gemma-4 meromero 31b": ("google-gemma-4-31b-it", 118, True),
    "gemma-4-meromero-31b": ("google-gemma-4-31b-it", 118, True),
    "gemma4-26b": ("google-gemma-4-26b-a4b-it", 63, False),
    "gemma4-12b": ("google-gemma-4-12b-it", 34, False),
    "gemma 4 12b": ("google-gemma-4-12b-it", 34, False),
    "mistral-small-4-119b": ("mistral-small-4", 21, False),
    "mistral-small-4": ("mistral-small-4", 21, False),
}

# pcpartpicker tracked video-card chipsets. detection pattern -> display label.
PCP_CARDS = [
    (r"5090", "GeForce RTX 5090"),
    (r"5080", "GeForce RTX 5080"),
    (r"5070\s*ti", "GeForce RTX 5070 Ti"),
    (r"5070", "GeForce RTX 5070"),
    (r"5060\s*ti", "GeForce RTX 5060 Ti"),
    (r"4090", "GeForce RTX 4090"),
    (r"4080\s*super", "GeForce RTX 4080 SUPER"),
    (r"4080", "GeForce RTX 4080"),
    (r"4070\s*ti\s*super", "GeForce RTX 4070 Ti SUPER"),
    (r"4070\s*ti", "GeForce RTX 4070 Ti"),
    (r"4070\s*super", "GeForce RTX 4070 SUPER"),
    (r"4070", "GeForce RTX 4070"),
    (r"7900\s*xtx", "Radeon RX 7900 XTX"),
    (r"7900\s*xt", "Radeon RX 7900 XT"),
    (r"9070\s*xt", "Radeon RX 9070 XT"),
    (r"9070", "Radeon RX 9070"),
    (r"9060\s*xt", "Radeon RX 9060 XT"),
]

PCP_URL = "https://pcpartpicker.com/trends/price/video-card/"

DISPLAY_MODEL_OVERRIDES = {
    "1525888743716687912": "glm-4.5",
    "1481473520528785511": "qwen3.5-35b-a3b",
    "1478255201516261578": "qwen3.5-35b-a3b",
    "1490016547698118676": "qwen3.5-35b-a3b",
    "1486150987852025966": "qwen3.5-35b-a3b",
    "1478112319484592220": "qwen3.5-0.8b",
    "1496333656883724428": "glm-4.7",
    "1493611004293025915": "gemma4-31b",
    "1516415534948941885": "gemma4-31b",
    "1483510845135917158": "mistral-small-4-119b",
}

SETUP_DISPLAY_OVERRIDES = {
    "1526391187722866858": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "ThinkingCap-Qwen3.6-27B-Q4_K_M",
        "version_url": "https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.6-27B-GGUF",
        "speed": "20t/s",
        "pp": "100t/s",
        "hardware": "RTX Quadro 4000 8GB · AMD BC-250 16GB",
        "price": "$400",
        "memory_total_gb": 24,
        "memory_params_b": 27,
        "memory_gb_per_b": 0.5,
        "hf_config": "hf-configs/qwen3.6-27b-config.json",
        "kv_ctx": 65536,
        "kv_element_bytes": 1,
        "info": "Running with llama.cpp RPC (cuda backend on the RTX, vulkan on the BC-250). llama-server --backend-sampling --n-gpu-layers -1 --rpc 192.168.100.10:50052 --jinja --cache-ram 32768 -fa on --model /opt/models/bottlecapai/ThinkingCap-Qwen3.6-27B-GGUF/ThinkingCap-Qwen3.6-27B-Q4_K_M.gguf --cache-type-k q8_0 --cache-type-v q8_0 --ctx-size 65536 --temp 1.0 --top-p 0.95 --top-k 64 -b 4096 -ub 1024 --spec-type draft-mtp --spec-draft-n-max 2",    },
    "1525810426628145303": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.6-27B-INT8-AutoRound",
        "version_url": "https://huggingface.co/Minachist/Qwen3.6-27B-INT8-AutoRound",
        "speed": "128t/s",
        "pp": "177t/s",
        "hardware": "4× RTX 5060 Ti 16GB",
        "price": "$2400",
        # Minachist INT8-AutoRound ≈ 36.8GB on HF
        "memory_total_gb": 64,
        "memory_params_b": 36.8,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.6-27b-config.json",
        "kv_ctx": 200000,
        "kv_element_bytes": 2,
        "info": (
            "SGLang with Minachist/Qwen3.6-27B-INT8-AutoRound — "
            "8 concurrency, TP=4, MTP, 16K batch tokens, 200K context, "
            "bfloat16 KV cache. 4× RTX 5060 Ti (4 lanes of gen4 per card via "
            "bifurcation, ~8GB/s each). Serving bench: input 177.35 tok/s, "
            "output 127.63 tok/s, mean TTFT 7.5s. Lower TTFT than vLLM at "
            "the same concurrency on this rig."
        ),
    },
    "1517354364006826015": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.5-27B-Q8_0",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-27B-GGUF",
        "speed": "28t/s",
        "pp": "256t/s",
        "hardware": "2× AMD Instinct MI50/MI60 16GB",
        "price": "$400",
        # unsloth Qwen3.5-27B Q8_0 ≈ 28.6GB on HF
        "memory_total_gb": 32,
        "memory_params_b": 28.6,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-27b-config.json",
        "kv_ctx": 16384,
        "kv_element_bytes": 2,
        "info": (
            "llama.cpp on 2× AMD Instinct MI50/MI60, Qwen 27B Q8_0. "
            "Tensor (Full) bench: pp2048 256.29 t/s, tg256 28.45 t/s; "
            "at 16k context pp 233.83 / tg 27.43. Tensor over PCIe 1.0 "
            "drops prefill ~30% (pp 180 → still ok decode). MTP wasn't "
            "a big win on MI50 — compute-bound more than interconnect."
        ),
    },
    "1515925193145581578": {
        "rich": True,
        "quant_bits": "6bit",
        "version_label": "Qwen3.6-35B-A3B-UD-Q6_K_XL",
        "version_url": "https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF",
        "pp": "260t/s",
        "hardware": "2× RTX 3060 12GB",
        "price": "$700",
        "memory_total_gb": 24,
        "memory_params_b": 31.8,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.6-35b-a3b-config.json",
        "kv_ctx": 131072,
        "kv_element_bytes": 2,
        "info": "llama.cpp, Qwen3.6-35B-A3B-UD-Q6_K_XL, MoE offloaded to CPU, -c 131072. Prefill ~260t/s on CUDA0 (PCIe x16 to CPU) vs ~170t/s on CUDA1 (PCIe x8); tg/sec similar on both. Asking whether the x16 vs x8 link explains the pp gap.",    },
    "1515886723773497414": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3.6-35B-A3B-APEX-MTP-I-Compact",
        "version_url": "https://huggingface.co/mudler/Qwen3.6-35B-A3B-APEX-MTP-GGUF/blob/main/Qwen3.6-35B-A3B-APEX-MTP-I-Compact.gguf",
        "speed": "35t/s",
        "hardware": "RTX 3060 12GB · Xeon E5-2650 v4 · 32GB RAM",
        "price": "$850",
        "memory_total_gb": 44,
        "memory_params_b": 17.3,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.6-35b-a3b-config.json",
        "kv_ctx": 90000,
        "kv_element_bytes": 2,
        "info": "llama-server, APEX-MTP-I-Compact.gguf, -ngl all, --n-cpu-moe 15, -c 90000, -b 2048 -ub 1024, -fa on, -ctk/-ctv turbo3_tcq. Reported 35.20 t/s (2.301 tokens in ~65s sample). Asking if that's good for this hybrid GPU+CPU MoE setup.",    },
    "1496550178063384758": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3.6-27B-Q4_M",
        "version_url": "https://huggingface.co/models?search=Qwen3.6-27B-Q4",
        "speed": "30-35t/s",
        "hardware": "RTX 3090 24GB",
        "price": "$1400",
        "memory_total_gb": 24,
        "memory_params_b": 27,
        "memory_gb_per_b": 0.5,
        "kv_pct_of_weights": 20,  # no ctx given — +20% weights as KV allowance
        "info": "llama.cpp, Qwen3.6-27B Q4_M on a 3090 — 30–35 t/s out of the box. No ctx/KV details given.",
    },
    "1491861155201683688": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "qwen3.5-9b.gguf",
        "version_url": "https://huggingface.co/models?search=Qwen3.5-9B-GGUF",
        "hardware": "RTX 3060 (Ion7 / llama.cpp)",
        "price": "—",
        "memory_total_gb": 12,
        "memory_params_b": 9,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-9b-config.json",
        "kv_ctx": 8192,
        "kv_element_bytes": 2,
        "info": "Ion7 LuaJIT runtime on llama.cpp — Qwen3.5-9B Q8, n_gpu_layers=43, n_ctx=8192. Vs llama-cpp-python on RTX 3060: detok 280× faster, gen@full-ctx 1.53×, 37% less RAM. More a runtime demo than a raw hardware flex.",
        "info2": "Heyio\n\nBeen building Ion7 ; a full LLM runtime in LuaJIT, on top of llama.cpp. No Python. No HTTP. No subprocess.\n\n local ion7 = require \"ion7.core\"\nion7.init({ log_level = 0 })\nlocal model = ion7.Model.load(\"qwen3.5-9b.gguf\", { n_gpu_layers = 43 })\nlocal ctx = model:context({ n_ctx = 8192 })\nlocal vocab = model:vocab()\nlocal sampler = ion7.Sampler.chain():top_k(40):temp(0.8):dist():build()\nlocal tokens, n = vocab:tokenize(\"Hello from Lua!\", true, false)\nctx:decode(tokens, n, 0, 0)\nprint(vocab:piece(sampler:sample(ctx:ptr(), -1))) \n\n vs llama-cpp-python (Qwen3.5-9B Q8, RTX 3060): Benchmark results \n\nDetokenization: 280× faster \n\nGeneration at full context: 1.53× \n\nRAM delta: 37% less \n\nKV snapshot: 14ms in-memory \n\n0 malloc per generated token\n\nAlso ships ion7-grammar (token-level constraints, JSON Schema, CRANE/IterGen, DCCD) and ion7-llm (full chat pipeline, prefix cache, sliding window).\n\n All MIT: https://github.com/Ion7-Labs \n\nStill early, would love feedback, opinions, or contributors if any of this resonates with you",
    },
    "1490016547698118676": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3.5-35B-A3B-Q4_K_M",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF",
        "speed": "70t/s",
        "hardware": "NVIDIA DGX Spark 128GB",
        "price": "$4800",
        "memory_total_gb": 128,
        # unsloth Q4_K_M file ≈ 22GB on HF
        "memory_params_b": 22,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "DGX Spark running Qwen3.5-35B Q4_K_M at 70+ t/s full context, alongside Kokoro TTS, Parakeet ASR, z-image-turbo, and qwen-image-edit.",
    },
    "1486723280911073362": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3.5-397B-A17B-Q4_K_M",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-397B-A17B-GGUF/tree/main/Q4_K_M",
        "speed": "13-14t/s",
        "hardware": "RTX PRO 6000 Max-Q 96GB · RTX A6000 48GB · 128GB DDR4",
        "price": "$17000",
        # pool = 96+48 VRAM + 128 DDR4; Q4_K_M shards ≈ 244GB on HF
        "memory_total_gb": 272,
        "memory_params_b": 244,
        "memory_gb_per_b": 1.0,
        # 128K Q8 KV — hybrid: 15 full_attention layers only
        "hf_config": "hf-configs/qwen3.5-397b-config.json",
        "kv_ctx": 131072,
        "kv_element_bytes": 1,
        "info": (
            "Qwen3.5-397B-A17B Q4_K_M (~244GB) with 128K Q8 KV (~1.9GB) squeezed across "
            "PRO 6000 Max-Q 96GB + A6000 48GB + 128GB DDR4 (PCIe Gen3) — ~13–14 t/s."
        ),
    },
    "1486374178062995535": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.5-35B-A3B-8bit",
        "version_url": "https://huggingface.co/mlx-community/Qwen3.5-35B-A3B-8bit",
        "speed": "41t/s",
        "pp": "483t/s",
        "hardware": "MacBook M1 Max 64GB",
        "price": "$2000",
        "memory_total_gb": 64,
        # mlx-community/Qwen3.5-35B-A3B-8bit shards ≈ 37.7GB on HF
        "memory_params_b": 37.7,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-35b-a3b-config.json",
        "kv_ctx": 36371,
        "kv_element_bytes": 2,
        "info": "MLX mlx-community/Qwen3.5-35B-A3B-8bit on M1 Max 64GB. Baseline (no KV quant): prefill 483.3 / decode 41.0 t/s on ~36k prompt. TurboQuant 3.5bit KV tanks decode to 6.6 t/s.",
    },
    "1486150987852025966": {
        "rich": True,
        "quant_bits": "2bit",
        "version_label": "Qwen3.5-35B-A3B-UD-Q2_K_XL",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF/blob/main/Qwen3.5-35B-A3B-UD-Q2_K_XL.gguf",
        "speed": "111t/s",
        "hardware": "RX 9070 XT 16GB",
        "price": "$700",
        "memory_total_gb": 16,
        # unsloth UD-Q2_K_XL ≈ 12.2GB on HF
        "memory_params_b": 12.2,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-35b-a3b-config.json",
        "kv_ctx": 65536,
        "kv_element_bytes": 2,
        "info": "Unsloth UD-Q2_K_XL, 64k context, fully on 16GB RX 9070 XT with no offloading — 111 t/s.",
    },
    "1485015727889977384": {
        "rich": True,
        "quant_bits": "3bit",
        "version_label": "Qwen3.5-122B-A10B-Q3_K_M",
        "version_url": "https://huggingface.co/models?search=Qwen3.5-122B-A10B-GGUF",
        "speed": "14.4t/s",
        "pp": "140t/s",
        "hardware": "RTX 5060 Ti 16GB",
        "price": "$600",
        # Q3_K_M ≈ 58.2GB on HF; single 5060 Ti (offload implied)
        "memory_total_gb": 16,
        "memory_params_b": 58.2,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "llama.cpp + tools. 122B Q3_K_M on single 5060 Ti: 140t/s pp @2.7k / 14.4t/s tg @2k.",
    },
    "1484547555886108884": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3-Coder-Next-Q4_K_M",
        "version_url": "https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF",
        "speed": "14.75t/s",
        "hardware": "RTX 5060 Ti 16GB · 96GB DDR5",
        "price": "$2200",
        # 16GB VRAM + 96GB system RAM; Q4_K_M ≈ 48.5GB on HF
        "memory_total_gb": 112,
        "memory_params_b": 48.5,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "qwen3-coder-next Q4_K_M on 5060 Ti 16GB + 96GB DDR5. ik_llama 14.75t/s vs llama.cpp 8t/s vs krasis 26.5t/s. Side note: krasis OpenAI API issues with openclaw.",
    },
    "1483170334025978119": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3.5-122B-A10B-4bit",
        "version_url": "https://huggingface.co/mlx-community/Qwen3.5-122B-A10B-4bit",
        "speed": "54t/s",
        "pp": "605t/s",
        "hardware": "Apple M3 Ultra 512GB (80 GPU cores)",
        "price": "$10000",
        "memory_total_gb": 512,
        # mlx-community 4bit ≈ 69.6GB on HF
        "memory_params_b": 69.6,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-122b-config.json",
        "kv_ctx": 512,
        "kv_element_bytes": 2,
        "info": "MLX 4bit on M3 Ultra 512GB — ~54 t/s tg at short ctx (~70GB resident), falling to ~32 t/s / 91.7GB at 128k. Also tables an M5 Max 128GB for comparison (faster pp/tg).",
    },
    "1483131779400339668": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3.5-9B-Q_K_M",
        "version_url": "https://huggingface.co/models?search=Qwen3.5-9B-GGUF",
        "speed": "5t/s",
        "hardware": "GTX 1650 4GB",
        "price": "—",
        "memory_total_gb": 4,
        "memory_params_b": 9,
        "memory_gb_per_b": 0.5,
        "info": "Qwen3.5-9B Q_K_M on a 4GB GTX 1650 — works at ~5 t/s (surprised it fits).",
        "info2": "Wait, if the model is too large, how am I able to run Qwen-3.5-9B Q_K_M on my GTX 1650 with 4gb vram? It works, although I only get about 5 tokens per second",
    },
    "1481473892936581210": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3-Coder-Next-NVFP4",
        "version_url": "https://huggingface.co/RedHatAI/Qwen3-Coder-Next-NVFP4",
        "speed": "95t/s",
        "pp": "45000t/s",
        "hardware": "NVIDIA DGX Spark 128GB",
        "price": "$4800",
        "memory_total_gb": 128,
        # RedHatAI NVFP4 ≈ 45GB on HF
        "memory_params_b": 45,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "Qwen3-Coder-Next NVFP4 on DGX Spark — 45000 t/s PP2048, 95 t/s tg512.",
    },
    "1481473520528785511": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.5-35B-A3B-Q8_0",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF",
        "speed": "58t/s",
        "pp": "826t/s",
        "hardware": "2× RTX 5060 Ti 16GB",
        "price": "$1200",
        "memory_total_gb": 32,
        # unsloth Q8_0 ≈ 36.9GB on HF
        "memory_params_b": 36.9,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "Qwen3.5-35B-A3B Q8 on dual 5060 Ti — prompt eval 826 t/s, gen 58 t/s. PP limited by x1 PCIe 4.0 link.",
    },
    "1481466465910521917": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.5-35B-A3B-Q8_0",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF",
        "speed": "94t/s",
        "pp": "4505t/s",
        "hardware": "2× RTX 4090 24GB",
        "price": "$4800",
        "memory_total_gb": 48,
        # unsloth Q8_0 ≈ 36.9GB on HF
        "memory_params_b": 36.9,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "Dual 4090, Q8 KV. 35B-A3B Q8_0: 4505 t/s pp / 94 t/s tg. Also quotes 27B Q8_0 at 1462 pp / 23.45 tg on the same rig.",
    },
    "1481349100120182854": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.5-35B-A3B-Q8_0",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF",
        "speed": "99t/s",
        "pp": "3219t/s",
        "hardware": "2× RTX 4090 24GB",
        "price": "—",
        "memory_total_gb": 48,
        "memory_params_b": 35,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-35b-a3b-config.json",
        "kv_ctx": 128000,
        "kv_element_bytes": 1,
        "info": "Dual 4090, 40k-token prompt, Q8 KV, ctx 128k. 35B-A3B Q8: 3219 t/s pp / 99.33 t/s tg. 27B Q8 on same run: 1462 pp / 23.45 tg.",
        "info2": "Running some new tests with the dual 4090 setup with a 40k token prompt. KV Cache is Q8, Context set to 128k\n unsloth/Qwen3.5-27B-GGUF Q8 1462.37 tokens/s PP 23.45 t/s TG\nunsloth/Qwen3.5-35B-A3B-GGUF Q8 3218.70 tokens/s 99.33 t/s TG",
    },
    "1479198528273383516": {
        "rich": True,
        "quant_bits": "5.5bit",
        "version_label": "Qwen3.5-35B-A3B-MLX-5.5bit",
        "version_url": "https://modelscope.cn/models/inferencerlabs/Qwen3.5-35B-A3B-MLX-5.5bit",
        "speed": "45t/s",
        "hardware": "MacBook Pro M1 Max 64GB",
        "price": "$2000",
        "memory_total_gb": 64,
        # ModelScope 5.5bit ≈ 22.3GB; ~42k ctx, 8bit KV (from post)
        "memory_params_b": 22.3,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-35b-a3b-config.json",
        "kv_ctx": 42000,
        "kv_element_bytes": 1,
        "info": "M1 Max 64GB, ~40–44k context (70-page PDF summarize). Best: inferencerlabs 5.5bit MLX 45 t/s (8bit KV in LM Studio). Also 9bit 39, mlx 6bit 23, GGUF MXFP4 10, UD-Q4_K_XL 20 t/s.",
    },
    "1478441851362213928": {
        "rich": True,
        "quant_bits": "5bit",
        "version_label": "Qwen_Qwen3.5-27B-Q5_K_L",
        "version_url": "https://huggingface.co/bartowski/Qwen_Qwen3.5-27B-GGUF/blob/main/Qwen_Qwen3.5-27B-Q5_K_L.gguf",
        "speed": "52t/s",
        "hardware": "RTX 5090 32GB",
        "price": "$4200",
        "memory_total_gb": 32,
        # bartowski Q5_K_L ≈ 21.7GB on HF
        "memory_params_b": 21.7,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "RTX 5090 — Qwen3.5-27B Q5_K_L at 52 t/s generation (comparison datapoint).",
    },
    "1478340131596271707": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3.5-35B-A3B-MXFP4_MOE",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF",
        "speed": "40t/s",
        "pp": "423t/s",
        "hardware": "Ryzen 7940HS 128GB · eGPU RTX 5060 Ti 16GB",
        "price": "—",
        "memory_total_gb": 144,
        # unsloth MXFP4_MOE ≈ 21.6GB on HF
        "memory_params_b": 21.6,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "ik_llama.cpp vs llama.cpp on MXFP4_MOE, --n-cpu-moe 22, -ngl 999. ik: ~423 t/s pp / ~40 t/s gen (1m30). llama.cpp: 123 pp / 36 gen (6m8) on same 2k Java analysis.",
        "info2": "i guess ik-llamap.cpp ist just different, as the logs are simliar to llama.cpp --verbose but less verbose. Basically prompt processing can also be viewed in real time. But just run a anaylsis on a 2k java lines of code on Ryzen 7940hs 128gb + egpu 5060ti 16gb, and result shocked me:\n\n./bin/llama-cli -m ../../models/qwen3.5/Qwen3.5-35B-A3B-MXFP4_MOE.gguf -p \"Create a list of classes and methods, that should be extracted from VermietungService into these classes. At the current point of time this class is containing functionality from different domain areas. Don't generate code. Don't write code. Use classname and class methods to show the resulting classes. Don't explain anything. $(cat test.java)\" -t 8 -ngl 999 -fa on --no-mmap --n-cpu-moe 22\n\nik-llama.cpp\n[ Prompt: 422,55 t/s | Generation: 39,82 t/s ]\ntotal time: 1m30,384s \nllama.cpp\n[ Prompt: 123,1 t/s | Generation: 36,3 t/s ]\ntotal time: 6m8,379s",
    },
    "1478255201516261578": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.5-35B-A3B-8bit",
        "version_url": "https://huggingface.co/mlx-community/Qwen3.5-35B-A3B-8bit",
        "speed": "39t/s",
        "hardware": "MacBook M1 Max 64GB",
        "price": "$2000",
        "memory_total_gb": 64,
        # mlx-community 8bit ≈ 37.7GB on HF (same as other M1 Max 8bit card)
        "memory_params_b": 37.7,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3.5-35b-a3b-config.json",
        "kv_ctx": 43000,
        "kv_element_bytes": 2,
        "info": "M1 Max 64GB multi-model note. Headline in post: 35B-A3B@8bit 38.54 t/s at ~43k ctx. Also 9B MLX bf16 17.3 and 9B@9bit 26.5 at ~40–44k (row model tagged 9b).",
    },
    "1478112319484592220": {
        "rich": True,
        "quant_bits": "8bit",
        "version_label": "Qwen3.5-0.8B-Q8_0",
        "version_url": "https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF",
        "speed": "12t/s",
        "hardware": "i5-1145G7 (CPU only)",
        "price": "$300",
        "memory_total_gb": 16,
        "memory_params_b": 0.8,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "qwen3.5-0.8b Q8_0 in LM Studio — 12 t/s CPU-only on i5-1145G7.",
    },
    "1468725965420236801": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Qwen3-Coder-Next-Q4_K_M",
        "version_url": "https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF",
        "speed": "26t/s",
        "pp": "307t/s",
        "hardware": "RTX 4070 12GB · 64GB DDR5 · 7950X",
        "price": "$1500",
        # 12GB VRAM + 64GB DDR5; Q4_K_M ≈ 48.5GB on HF; q4 KV @ 40k ctx
        "memory_total_gb": 76,
        "memory_params_b": 48.5,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/qwen3-coder-next-config.json",
        "kv_ctx": 40960,
        "kv_element_bytes": 0.5,
        "info": "llama-server unsloth Coder-Next Q4_K_M, ctx 40k, flash-attn, -ctk/-ctv q4_0, --fit on. 30k-token prompt: 307 t/s pp / 25.54 t/s tg.",
    },
    # --- GLM / Gemma / MiniMax / Mistral (rich + info2 for review) ---
    "1525888743716687912": {
        "rich": True,
        "quant_bits": "3bit",
        "version_label": "GLM-4.5-IQ3_XXS",
        "version_url": "https://huggingface.co/unsloth/GLM-4.5-GGUF",
        "speed": "5t/s",
        "hardware": "2× RX 7900 XTX 24GB · 192GB DDR5",
        "price": "$11000",
        # model ~145GB; pool = 2×24 VRAM + 192 DDR5 = 240GB
        "memory_total_gb": 240,
        "memory_params_b": 145,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/glm-4.5-config.json",
        "kv_ctx": 32768,
        "kv_element_bytes": 2,
        "info": "GLM-4.5 IQ3_XXS (~145GB) on 2× 7900 XTX + 192GB DDR5 — only ~5 t/s; quality not acceptable — first prompt was \"Hello\" and it responded in Chinese.",
    },
    "1496333656883724428": {
        "rich": True,
        "quant_bits": "3bit",
        "version_label": "GLM-4.7-Q3_K_L",
        "version_url": "https://huggingface.co/bartowski/zai-org_GLM-4.7-GGUF",
        "speed": "12t/s",
        "hardware": "2× Radeon AI PRO R9700 32GB · EPYC 7532 · 256GB DDR4-3200",
        "price": "$6000",
        # model ~171GB; pool = 2×32 VRAM + 256 DDR4 = 320GB
        "memory_total_gb": 320,
        "memory_params_b": 171,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/glm-4.7-config.json",
        "kv_ctx": 32768,
        "kv_element_bytes": 2,
        "info": "GLM-4.7 Q3_K_L (~171GB, ~16GB active) on EPYC 7532 + 256GB DDR4 + 2× R9700 — 12 t/s with -ncmoe 0 (attention on GPU, experts in RAM).",
    },
    "1478455512868585682": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "GLM-4.7-Q4_K_M",
        "version_url": "https://huggingface.co/unsloth/GLM-4.7-GGUF",
        "speed": "5.8t/s",
        "hardware": "RTX PRO 6000 96GB · 9950X · 256GB DDR5-6000",
        "price": "$20000",
        # model ~216GB; pool = 96 VRAM + 256 DDR5 = 352GB
        "memory_total_gb": 352,
        "memory_params_b": 216,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/glm-4.7-config.json",
        "kv_ctx": 32768,
        "kv_element_bytes": 2,
        "info": "GLM-4.7 Q4_K_M (~216GB) on 9950X + 256GB DDR5-6000 + RTX PRO 6000 — ~5.8 t/s.",
    },
    "1526289704239235183": {
        "rich": True,
        "quant_bits": "1bit",
        "version_label": "GLM-5.2-UD-IQ1_M",
        "version_url": "https://huggingface.co/unsloth/GLM-5.2-GGUF",
        "speed": "0.2t/s",
        "pp": "0.3t/s",
        "hardware": "RTX 5070 Laptop 8GB · Ryzen AI 7 350 · 32GB RAM",
        "price": "$1500",
        # 744B MoE streamed from NVMe; ~3.7GB VRAM + ~31GB RAM in use
        "memory_total_gb": 40,
        "memory_params_b": 228,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "GLM-5.2 UD-IQ1_M (~228GB) streaming experts from NVMe on a 5070 Laptop 8GB + 32GB RAM — ~0.3 t/s pp / ~0.2 t/s tg (~3.7GB VRAM + ~31GB RAM).",
    },
    "1480320394966859796": {
        "rich": True,
        "quant_bits": "3bit",
        "version_label": "MiniMax-M2.5-Q3_K_M",
        "version_url": "https://huggingface.co/unsloth/MiniMax-M2.5-GGUF",
        "speed": "20t/s",
        "pp": "200t/s",
        "hardware": "RTX PRO 6000 96GB",
        "price": "$12000",
        # model ~109GB; pool = 96GB VRAM
        "memory_total_gb": 96,
        "memory_params_b": 109,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/minimax-m2.5-config.json",
        "kv_ctx": 32768,
        "kv_element_bytes": 2,
        "info": "MiniMax M2.5 Q3 (~109GB) on a single RTX PRO 6000 — 20 t/s tg / 200 t/s pp. Planning to add a 5090 for layer offload.",
    },
    "1493611004293025915": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "gemma-4-31B-it-Q4_K_M",
        "version_url": "https://huggingface.co/unsloth/gemma-4-31B-it-GGUF",
        "speed": "50t/s",
        "pp": "1200t/s",
        "hardware": "2× RTX 3090 24GB",
        "price": "$2800",
        # model ~14.7GB; pool = 2×24 VRAM = 48GB
        "memory_total_gb": 48,
        "memory_params_b": 14.7,
        "memory_gb_per_b": 1.0,
        "kv_pct_of_weights": 20,
        "info": "Gemma 4 31B (~14.7GB) with llama.cpp speculative decoding on 2× 3090 — up to ~50 t/s / ~1200 t/s pp on some tasks (~2× vs Qwen3.5-27B for this user).",
    },
    "1516415534948941885": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "G4-MeroMero-31B-IQ4_XS",
        "version_url": "https://huggingface.co/zerofata/G4-MeroMero-31B-gguf",
        "speed": "14.6t/s",
        "hardware": "RTX 5060 Ti 16GB · RTX 3060 12GB",
        "price": "$950",
        # model ~16.7GB; pool = 16+12 VRAM = 28GB
        "memory_total_gb": 28,
        "memory_params_b": 16.7,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/gemma-4-meromero-31b-config.json",
        "kv_ctx": 32768,
        "kv_element_bytes": 2,
        "info": "Gemma 4 31B MeroMero IQ4_XS (~16.7GB) on KoboldCPP — 5060 Ti + 3060 layer split, 14.6 t/s.",
    },
    "1490462529229557945": {
        "rich": True,
        "quant_bits": "16bit",
        "version_label": "gemma-4-31B-it-BF16",
        "version_url": "https://huggingface.co/google/gemma-4-31B-it",
        "speed": "23t/s",
        "hardware": "RTX PRO 6000 96GB",
        "price": "$12000",
        # model ~63GB; pool = 96GB VRAM
        "memory_total_gb": 96,
        "memory_params_b": 63,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/gemma-4-31b-config.json",
        "kv_ctx": 131072,
        "kv_element_bytes": 2,
        "info": "Gemma 4 31B BF16 (~63GB) on RTX PRO 6000 — 23 t/s at max context, ~10GB VRAM spare, GPU power capped ~440W / 600W.",
    },
    "1515466114493186048": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "gemma-4-12B-it-qat-UD-Q4_K_XL",
        "version_url": "https://huggingface.co/unsloth/gemma-4-12B-it-qat-GGUF",
        "speed": "96t/s",
        "hardware": "ASUS ROG G700 · RTX 5080 16GB · Ultra 7 265KF · 32GB RAM",
        "price": "$3000",
        # model QAT ~6.72GB; pool = 16GB VRAM
        "memory_total_gb": 16,
        "memory_params_b": 6.72,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/gemma-4-12b-config.json",
        "kv_ctx": 32768,
        "kv_element_bytes": 2,
        "info": "google/gemma-4-12b-qat (~6.72GB) on ASUS ROG G700 (RTX 5080 16GB, Ultra 7 265KF, 32GB) — 96 t/s.",
    },
    "1483510845135917158": {
        "rich": True,
        "quant_bits": "4bit",
        "version_label": "Mistral-Small-4-119B-2603-UD-IQ4_XS",
        "version_url": "https://huggingface.co/unsloth/Mistral-Small-4-119B-2603-GGUF",
        "speed": "189.7t/s",
        "pp": "3494t/s",
        "hardware": "RTX PRO 6000 96GB",
        "price": "$12000",
        # model ~58.1GB; pool = 96GB VRAM; fully on GPU (ngl 99)
        "memory_total_gb": 96,
        "memory_params_b": 58.1,
        "memory_gb_per_b": 1.0,
        "hf_config": "hf-configs/mistral-small-4-119b-config.json",
        "kv_ctx": 32768,
        "kv_element_bytes": 2,
        "info": "Mistral Small 4 119B UD-IQ4_XS (~58.1GB) on RTX PRO 6000 — llama-bench pp512 3494 t/s / tg128 190 t/s, no RAM offload.",
    },
}


def display_model(row: dict) -> str:
    rid = row.get("id") or ""
    if rid in DISPLAY_MODEL_OVERRIDES:
        return DISPLAY_MODEL_OVERRIDES[rid]
    return row.get("model") or ""


def provider_of(row: dict) -> str:
    m = display_model(row).lower()
    if "qwen" in m or "unsloth/3" in m:
        return "Qwen"
    if "glm" in m:
        return "GLM"
    if "gemma" in m:
        return "Gemma"
    if "minimax" in m:
        return "MiniMax"
    if "mistral" in m:
        return "Mistral"
    if "gpt" in m or "oss" in m:
        return "OpenAI"
    if "deepseek" in m:
        return "DeepSeek"
    if "kimi" in m:
        return "Moonshot · Kimi"
    if "llama" in m:
        return "Meta · Llama"
    return "Other"


def display_quant_bits(row: dict) -> str:
    rid = row.get("id") or ""
    ov = SETUP_DISPLAY_OVERRIDES.get(rid)
    if ov and ov.get("quant_bits"):
        return ov["quant_bits"]
    return quant_bit_label(row.get("quantization") or "")


def version_display(row: dict, quant: str, model: str) -> tuple[str, str]:
    rid = row.get("id") or ""
    ov = SETUP_DISPLAY_OVERRIDES.get(rid)
    if ov:
        label = ov.get("version_label") or quant or "—"
        url = ov.get("version_url") or hf_link(model, quant)
        return label, url
    label = (quant or "").strip() or "—"
    return label, hf_link(model, quant)


def hf_link(model: str, quant: str) -> str:
    q = " ".join(p for p in [model, quant] if p and p.strip())
    q = re.sub(r"\s+", " ", q).strip()
    return "https://huggingface.co/models?search=" + urllib.parse.quote(q)


def bench_slug(model: str) -> tuple[str | None, bool]:
    key = (model or "").strip().lower()
    if key in BENCHMARKLIST:
        slug, _count, approx = BENCHMARKLIST[key]
        return slug, approx
    return None, True


def fmt_stat_value(metric: str, value, unit: str) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        num = f"{round(value, 1):g}"
    elif isinstance(value, int):
        num = str(value)
    else:
        num = str(value)
    u = (unit or "").lower()
    if u in ("fraction", "percent", "percentage", "%"):
        return f"{num}%"
    if u == "points":
        return f"{num} pts"
    if u == "elo":
        return f"{num} Elo"
    return num


def load_ebay_prices() -> dict:
    global _EBAY_CACHE
    if _EBAY_CACHE is not None:
        return _EBAY_CACHE
    if not EBAY_PRICES.exists():
        _EBAY_CACHE = {}
        return _EBAY_CACHE
    doc = json.loads(EBAY_PRICES.read_text(encoding="utf-8"))
    _EBAY_CACHE = doc.get("items") or {}
    return _EBAY_CACHE


def split_hardware_items(hardware: str) -> list[str]:
    parts = re.split(r"\s*(?:,|/|\+|&| and )\s*", hardware or "")
    skip = {"gbe", "ram", "ddr4", "ddr5", "ssd", "nvme", "pcie", "cpu", "gpu", "igpu"}
    items: list[str] = []
    for part in parts:
        part = re.sub(r"\s+", " ", part).strip(" .;")
        if len(part) < 3 or part.lower() in skip:
            continue
        if re.fullmatch(r"\d+\s*gb", part.lower()):
            continue
        if part not in items:
            items.append(part)
    return items


def ebay_search_url(query: str) -> str:
    return "https://www.ebay.com/sch/i.html?" + urllib.parse.urlencode(
        {"_nkw": query or "gpu", "LH_Sold": "1", "LH_Complete": "1"}
    )


def price_source(hardware: str) -> tuple[str, str]:
    hay = (hardware or "").lower()
    for pat, label in PCP_CARDS:
        if re.search(pat, hay):
            return f"{PCP_URL}#{label}", f"pcpartpicker trends · {label}"
    return ebay_search_url(hardware or "gpu"), "eBay recently sold"


def extract_pp_ts(text: str, tps_values: list[float]) -> tuple[str, str]:
    hay = text or ""
    pp_vals: list[str] = []
    ts_vals: list[str] = []
    for pat in (
        r"(\d+(?:\.\d+)?)\s*(?:tok/s|t/s|tokens/sec|tok/sec|tps)\s*pp\b",
        r"(\d+(?:\.\d+)?)\s*pp/s\b",
        r"(\d+(?:\.\d+)?)\s*pp\b",
        r"pp\s*TPS[^0-9]{0,20}(\d+(?:\.\d+)?)",
    ):
        for m in re.finditer(pat, hay, re.I):
            pp_vals.append(m.group(1))
    for pat in (
        r"(\d+(?:\.\d+)?)\s*(?:tok/s|t/s|tokens/sec|tok/sec|tps)\s*(?:tg|gen|decode|generation)\b",
        r"(?:tg|gen|decode|generation)\s*(\d+(?:\.\d+)?)\s*(?:tok/s|t/s)?",
    ):
        for m in re.finditer(pat, hay, re.I):
            ts_vals.append(m.group(1))
    if tps_values and not ts_vals:
        reasonable = [v for v in tps_values if 0.1 <= v <= 500]
        pick = min(reasonable) if reasonable else min(tps_values)
        ts_vals.append(f"{pick:g}")
    return ", ".join(dict.fromkeys(pp_vals)), ", ".join(dict.fromkeys(ts_vals))


def leftover_message(row: dict) -> str:
    """Prefer manual info override, else keep the original Discord message."""
    ov = SETUP_DISPLAY_OVERRIDES.get(row.get("id") or "", {})
    if ov.get("info"):
        return ov["info"]
    msg = (row.get("message") or "").strip()
    return msg or "—"


def display_hardware(row: dict) -> str:
    ov = SETUP_DISPLAY_OVERRIDES.get(row.get("id") or "", {})
    if ov.get("hardware"):
        return ov["hardware"]
    return row.get("hardware") or "—"


def field(label: str, value: str) -> str:
    return (
        f'<div class="f"><span class="k">{html.escape(label)}</span>'
        f'<span class="v">{html.escape(value)}</span></div>'
    )


def render_quant(row: dict) -> str:
    label = display_quant_bits(row)
    if not label or label == "—":
        return field("quant", "—")
    chips = "".join(
        f'<span class="quant-bit">{html.escape(part.strip())}</span>'
        for part in label.split(",")
        if part.strip()
    )
    return (
        f'<div class="f"><span class="k">quant</span>'
        f'<span class="v quant-bits">{chips}</span></div>'
    )


def quant_bit_label(quant: str) -> str:
    if not quant or not quant.strip():
        return "—"
    parts = re.split(r"[,·/|]+", quant)
    bits: list[str] = []
    for part in parts:
        bit = _single_quant_bit(part.strip())
        if bit and bit not in bits:
            bits.append(bit)
    return ", ".join(bits) if bits else "—"


def _single_quant_bit(raw: str) -> str:
    hay = raw.lower().replace("_", "-").replace(" ", "")
    if not hay or hay in {"-", "none", "n/a"}:
        return ""
    if re.search(r"q2|iq2", hay):
        return "2bit"
    if re.search(r"q3|iq3", hay):
        return "3bit"
    if re.search(r"q4|iq4|int4|fp4|nvfp4|mxfp4|4bit|4-bit", hay):
        return "4bit"
    if re.search(r"q5", hay):
        return "5bit"
    if re.search(r"q6", hay):
        return "6bit"
    if re.search(r"q8|int8|fp8|8bit|8-bit", hay):
        return "8bit"
    if re.search(r"bf16|fp16|f16|float16|16bit|16-bit", hay):
        return "16bit"
    if re.search(r"fp32|unquant|full.?precision|bf16-full", hay):
        return "16bit"
    return ""


INTELLIGENCE_STATS = {
    "AA Intelligence Index",
    "GPQA Diamond",
    "Humanity's Last Exam",
    "SWE-bench Verified",
    "AA-LCR (long context)",
    "Terminal-Bench 2.1",
    "MMMU-Pro",
    "SciCode",
    "LiveCodeBench",
}


def _rankings_tip(model: str, slug: str, data: dict, approx: bool) -> str:
    """Legacy dark tip used by non-curated cards."""
    url = f"https://benchmarklist.com/models/{slug}/"
    stats = data.get("stats") or []
    ow = data.get("open_weight") or {}

    ow_block = ""
    if ow.get("rank") and ow.get("total"):
        ow_block = (
            '<div class="tsec">open-weight</div>'
            '<div class="tr"><span class="tl">Global open-weight rank</span>'
            f'<span class="tv"><span class="rk">#{ow["rank"]}</span> / {ow["total"]}</span></div>'
        )

    intel_rows = []
    for s in stats:
        if s.get("label") not in INTELLIGENCE_STATS:
            continue
        val = fmt_stat_value(s["metric"], s["value"], s["unit"])
        if s.get("rank") and s.get("total"):
            rank = (
                f' <span class="rk">#{s["rank"]}</span>'
                f' / {html.escape(str(s["total"]))}'
            )
        elif s.get("rank"):
            rank = f' <span class="rk">#{s["rank"]}</span>'
        else:
            rank = ""
        intel_rows.append(
            f'<div class="tr"><span class="tl">{html.escape(s["label"])}</span>'
            f'<span class="tv">{html.escape(val)}{rank}</span></div>'
        )
    intel_block = (
        '<div class="tsec">intelligence rankings <span class="tnn">(overall, incl. closed)</span></div>'
        + "".join(intel_rows)
        if intel_rows
        else ""
    )
    approx_note = (
        '<div class="tn">≈ closest benchmarklist match</div>' if approx else ""
    )
    return (
        f'<a class="tiplink" href="{html.escape(url)}" target="_blank" rel="noopener">'
        f'{html.escape(data.get("name") or model)} →</a>'
        f"{approx_note}{ow_block}{intel_block}"
    )


TIP_BENCH_SHORT = {
    "AA Intelligence Index": "AA Index",
    "GPQA Diamond": "GPQA",
    "Humanity's Last Exam": "HLE",
    "SWE-bench Verified": "SWE-bench",
    "AA-LCR (long context)": "AA-LCR",
    "Terminal-Bench 2.1": "Terminal",
    "MMMU-Pro": "MMMU-Pro",
    "SciCode": "SciCode",
    "LiveCodeBench": "LiveCode",
}


def _rankings_tip_rich(model: str, slug: str, data: dict, approx: bool) -> str:
    """Compact dark tip — scannable score · rank rows."""
    url = f"https://benchmarklist.com/models/{slug}/"
    stats = data.get("stats") or []
    ow = data.get("open_weight") or {}
    name = data.get("name") or model

    parts = [
        '<div class="tip-banner">'
        f'<a class="tip-head" href="{html.escape(url)}" target="_blank" rel="noopener">'
        f"{html.escape(name)} →</a>"
        "</div>",
        '<div class="tip-body">',
    ]
    if approx:
        parts.append('<div class="tip-note">closest match</div>')

    if ow.get("rank") and ow.get("total"):
        parts.append(
            '<div class="tip-hero">'
            '<span class="tip-hero-k">open-weight</span>'
            f'<span class="tip-hero-v">#{html.escape(str(ow["rank"]))}'
            f'<span class="tip-hero-t"> / {html.escape(str(ow["total"]))}</span></span>'
            "</div>"
        )

    intel = [s for s in stats if s.get("label") in INTELLIGENCE_STATS]
    if intel:
        parts.append('<div class="tip-list">')
        for s in intel:
            short = TIP_BENCH_SHORT.get(s["label"], s["label"])
            val = fmt_stat_value(s["metric"], s["value"], s["unit"])
            if s.get("rank") and s.get("total"):
                rank_s = f'#{s["rank"]}/{s["total"]}'
            elif s.get("rank"):
                rank_s = f'#{s["rank"]}'
            else:
                rank_s = ""
            parts.append(
                '<div class="tip-row">'
                f'<span class="tip-k">{html.escape(short)}</span>'
                f'<span class="tip-v">{html.escape(val)}'
                + (
                    f' <span class="tip-rank">{html.escape(rank_s)}</span>'
                    if rank_s
                    else ""
                )
                + "</span></div>"
            )
        parts.append("</div>")

    parts.append("</div>")
    return "".join(parts)


def render_rankings(model: str, bl_stats: dict) -> str:
    slug, approx = bench_slug(model)
    if not slug or slug not in bl_stats:
        return (
            '<div class="f"><span class="k">rankings</span><span class="v">'
            'no exact match · '
            '<a class="link-plain" href="https://benchmarklist.com/models/" target="_blank" rel="noopener">browse</a>'
            "</span></div>"
        )

    data = bl_stats[slug]
    ow = data.get("open_weight") or {}

    if ow.get("rank") and ow.get("total"):
        summary = f"open-weight #{ow['rank']} / {ow['total']}"
    else:
        summary = "open-weight rank n/a"

    return (
        '<div class="f"><span class="k">rankings</span>'
        f'<span class="v hovtxt">{html.escape(summary)} <span class="hint">(hover)</span>'
        '<span class="tip">'
        f"{_rankings_tip(model, slug, data, approx)}"
        "</span></span></div>"
    )


def setup_price_value(row: dict, hardware: str) -> float | None:
    """Numeric USD for sorting; None if unknown."""
    ov = SETUP_DISPLAY_OVERRIDES.get(row.get("id") or "", {})
    raw = ov.get("price")
    if raw:
        m = re.search(r"([\d]+(?:\.\d+)?)", str(raw).replace(",", ""))
        if m:
            return float(m.group(1))
    cache = load_ebay_prices()
    total = 0.0
    found = 0
    for item in split_hardware_items(hardware):
        cached = cache.get(item) or {}
        stats = cached.get("stats") or {}
        if cached.get("ok") and stats.get("median") is not None:
            total += float(stats["median"])
            found += 1
    return total if found else None


def setup_rank_value(model: str, bl_stats: dict) -> int | None:
    """Open-weight rank for sorting; None if unknown."""
    slug, _approx = bench_slug(model)
    if not slug or slug not in bl_stats:
        return None
    rank = (bl_stats[slug].get("open_weight") or {}).get("rank")
    try:
        return int(rank) if rank is not None else None
    except (TypeError, ValueError):
        return None


def render_price(hardware: str, row: dict | None = None) -> str:
    """Manual price override, else per-component eBay sold medians."""
    if row is not None:
        ov = SETUP_DISPLAY_OVERRIDES.get(row.get("id") or "", {})
        if ov.get("price"):
            return field("price", ov["price"])

    cache = load_ebay_prices()
    items = split_hardware_items(hardware)
    bits: list[str] = []
    for item in items:
        cached = cache.get(item) or {}
        stats = cached.get("stats") or {}
        url = cached.get("url") or ebay_search_url(item)
        mode = cached.get("mode") or "sold"
        if cached.get("ok") and stats.get("median") is not None:
            label = f"{item}: ${stats['median']:.0f} median"
            if stats.get("count"):
                label += f" (n={stats['count']} {mode})"
            bits.append(
                f'<a class="link-plain" href="{html.escape(url)}" '
                f'target="_blank" rel="noopener">{html.escape(label)}</a>'
            )
        else:
            bits.append(
                f'<a class="link-plain" href="{html.escape(ebay_search_url(item))}" '
                f'target="_blank" rel="noopener">'
                f"{html.escape(item)}: eBay sold</a>"
            )
    if not bits:
        p_url, p_label = price_source(hardware)
        bits.append(
            f'<a class="link-plain" href="{html.escape(p_url)}" '
            f'target="_blank" rel="noopener">{html.escape(p_label)}</a>'
        )
    return (
        '<div class="f"><span class="k">price</span>'
        f'<span class="v price-list">{" · ".join(bits)}</span></div>'
    )


def render_version(full_version: str, hf: str) -> str:
    label = (full_version or "").strip() or "—"
    if label == "—":
        return field("version", "—")
    link = (
        f'<a class="link-plain" href="{html.escape(hf)}" target="_blank" rel="noopener">'
        f"{html.escape(label)}</a>"
    )
    return (
        '<div class="f"><span class="k">version</span>'
        f'<span class="v">{link}</span></div>'
    )


def format_speed(row: dict, ts: str, pp: str) -> str:
    """Prefer manual override; append pp in parentheses when available."""
    ov = SETUP_DISPLAY_OVERRIDES.get(row.get("id") or "", {})
    speed = ov.get("speed")
    if not speed:
        speed = (row.get("speed") or "").strip()
        if speed:
            speed = re.sub(
                r"(?:·\s*)?(?:\d+(?:\.\d+)?\s*tok/s(?:\s*,\s*)?)+$",
                "",
                speed,
            ).strip(" ·") or (row.get("speed") or "").strip()
        elif ts:
            speed = f"{ts} tok/s"
        else:
            speed = "—"
    pp_display = ov.get("pp") or (pp or None)
    if pp_display and speed != "—":
        pp_clean = re.sub(r"\s*pp\s*$", "", pp_display, flags=re.I).strip()
        return f"{speed} ({pp_clean} pp)"
    return speed


def render_info(text: str) -> str:
    body = (text or "").strip() or "—"
    if body == "—":
        return field("info", body)
    # Always clamp + "read more"; JS hides the button when it fits without clamping.
    return (
        '<div class="f"><span class="k">info</span>'
        '<span class="v info-v">'
        f'<span class="info-clamp">{html.escape(body)}</span> '
        '<button type="button" class="read-more-btn" onclick="toggleInfo(this)">read more</button>'
        "</span></div>"
    )


def subhead(label: str = "") -> str:
    """Divider line after rankings. Pass a label only if you want title text."""
    if label:
        return f'<div class="spec-subhead">{html.escape(label)}</div>'
    return '<div class="spec-subhead spec-subhead-line" aria-hidden="true"></div>'


def _fmt_gb(n: float) -> str:
    return f"{n:g}"


def load_hf_text_config(rel_path: str) -> dict:
    path = DATA / rel_path
    cfg = json.loads(path.read_text(encoding="utf-8"))
    return cfg.get("text_config") or cfg


def kv_cache_bytes_from_hf(
    text_cfg: dict, ctx: int, element_bytes: float
) -> dict:
    """
    KV Cache (Bytes) = 2 × L × N_kv × d_head × N_ctx × B_element

    For hybrid Qwen3.5/3.6, L is full_attention layers only (linear_attention
    does not use a standard dense KV cache of this form).
    """
    layers = text_cfg.get("layer_types") or []
    if layers:
        n_layers = sum(1 for t in layers if t == "full_attention")
    else:
        n_layers = int(text_cfg.get("num_hidden_layers") or 0)
    n_kv = int(text_cfg.get("num_key_value_heads") or 0)
    head_dim = text_cfg.get("head_dim")
    if head_dim is None:
        hidden = int(text_cfg.get("hidden_size") or 0)
        n_heads = int(text_cfg.get("num_attention_heads") or 1)
        head_dim = hidden // n_heads
    head_dim = int(head_dim)
    raw = 2 * n_layers * n_kv * head_dim * int(ctx) * float(element_bytes)
    return {
        "bytes": raw,
        "gib": raw / (1024**3),
        "gb": raw / 1e9,
        "n_layers": n_layers,
        "n_kv": n_kv,
        "head_dim": head_dim,
        "ctx": int(ctx),
        "element_bytes": float(element_bytes),
    }


def _short_version_label(label: str) -> str:
    """One display name: prefer concrete file/quant over org/repo."""
    s = (label or "").strip()
    if not s or s == "—":
        return "—"
    # "org/repo FileName" → FileName
    if " " in s:
        s = s.rsplit(" ", 1)[-1]
    if "/" in s:
        s = s.rsplit("/", 1)[-1]
    return s


def rich_field(label: str, value_html: str) -> str:
    """Label/value row; value may contain trusted HTML (links)."""
    return (
        f'<div class="rf"><span class="rl">{html.escape(label)}</span>'
        f'<span class="rv">{value_html}</span></div>'
    )


def render_memory_field(ov: dict) -> str:
    """Weights + exact KV cache (from HF arch) over total VRAM, with fill bar."""
    total = ov.get("memory_total_gb")
    params = ov.get("memory_params_b")
    per = ov.get("memory_gb_per_b")
    if total is None or params is None or per is None:
        return ""
    used = float(params) * float(per)  # weight footprint (GB)
    total_f = float(total)

    kv_gib = None
    kv_title = ""
    if ov.get("hf_config") and ov.get("kv_ctx"):
        try:
            tc = load_hf_text_config(ov["hf_config"])
            kv = kv_cache_bytes_from_hf(
                tc,
                int(ov["kv_ctx"]),
                float(ov.get("kv_element_bytes") or 2),
            )
            kv_gib = kv["gib"]
            kv_title = (
                f"KV = 2×{kv['n_layers']}L×{kv['n_kv']}kv×{kv['head_dim']}d"
                f"×{kv['ctx']}ctx×{kv['element_bytes']:g}B"
                f" = {kv['gib']:g} GiB"
                " (full_attention layers from HF config)"
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            kv_gib = None
    elif ov.get("kv_pct_of_weights") is not None:
        # Rough allowance when ctx/cache type aren't stated (e.g. +20% of weights)
        pct_w = float(ov["kv_pct_of_weights"])
        kv_gib = used * (pct_w / 100.0)
        kv_title = f"KV ≈ {pct_w:g}% of weight footprint (estimate)"

    with_kv = used + (kv_gib if kv_gib is not None else 0.0)
    pct = min(100.0, (used / total_f) * 100.0) if total_f else 0.0
    pct_kv = min(100.0, (with_kv / total_f) * 100.0) if total_f else 0.0
    used_s = _fmt_gb(used)
    total_s = _fmt_gb(total_f)
    if kv_gib is not None:
        kv_s = _fmt_gb(kv_gib)
        allow_html = (
            f'<span class="mem-allow" title="{html.escape(kv_title)}">'
            f" +kv {html.escape(kv_s)}</span>"
        )
        aria = "memory weights plus kv cache"
    else:
        allow_html = ""
        aria = "memory used"
    value = (
        f'<span class="mem-ratio">'
        f'<span class="mem-used">{html.escape(used_s)}</span>'
        f"{allow_html}"
        f'<span class="mem-sep"> / </span>'
        f'<span class="mem-total">{html.escape(total_s)} GB</span>'
        f"</span>"
        f'<div class="mem-bar" role="meter" aria-label="{aria}" '
        f'aria-valuemin="0" aria-valuemax="{html.escape(total_s)}" '
        f'aria-valuenow="{html.escape(used_s)}">'
        f'<div class="mem-bar-allow" style="width:{pct_kv:.1f}%"></div>'
        f'<div class="mem-bar-fill" style="width:{pct:.1f}%"></div>'
        f"</div>"
    )
    return rich_field("memory", value)


def render_rich_rank(model: str, bl_stats: dict) -> str:
    slug, approx = bench_slug(model)
    if not slug or slug not in bl_stats:
        return rich_field("rank", "—")
    data = bl_stats[slug]
    ow = data.get("open_weight") or {}
    if not (ow.get("rank") and ow.get("total")):
        return rich_field("rank", "—")
    tip = _rankings_tip_rich(model, slug, data, approx)
    bl_url = f"https://benchmarklist.com/models/{slug}/"
    value = (
        f'<span class="hovtxt">'
        f'<span class="rank-n">#{html.escape(str(ow["rank"]))}</span>'
        f'<span class="rank-t"> / {html.escape(str(ow["total"]))}</span>'
        f' <span class="rank-note">open-weight</span>'
        f'<span class="tip tip-rich">{tip}</span></span>'
        f' <a class="rank-src" href="{html.escape(bl_url)}" '
        f'target="_blank" rel="noopener">benchmarklist</a>'
    )
    return rich_field("rank", value)


def render_rich_version(version_label: str, version_url: str) -> str:
    short = _short_version_label(version_label)
    if short == "—":
        return rich_field("version", "—")
    if version_url:
        value = (
            f'<a class="link-plain" href="{html.escape(version_url)}" '
            f'target="_blank" rel="noopener" title="{html.escape(version_label)}">'
            f"{html.escape(short)}</a>"
        )
    else:
        value = html.escape(short)
    return rich_field("version", value)


def render_rich_info(text: str, label: str = "info") -> str:
    body = (text or "").strip() or "—"
    if body == "—":
        return ""
    # Always clamp + "read more"; JS hides the button when it fits on one line.
    return rich_field(
        label,
        '<span class="info-v">'
        f'<span class="info-clamp">{html.escape(body)}</span> '
        '<button type="button" class="read-more-btn" onclick="toggleInfo(this)">read more</button>'
        "</span>",
    )


def render_rich_box(row: dict, bl_stats: dict, ov: dict) -> str:
    """
    Minimal composition:
    identity → model facts → run facts (memory bar as sole graphic) → detail
    """
    model = display_model(row) or "(unspecified)"
    quant = row.get("quantization") or ""
    hardware = display_hardware(row)
    version_label, version_url = version_display(row, quant, model)
    search_key = " ".join(p for p in [model, quant, hardware] if p).lower()
    quant_label = display_quant_bits(row)
    price = ov.get("price") or "—"
    extra = leftover_message(row)
    specs = row.get("specs") or {}
    hay = f"{row.get('speed') or ''}\n{row.get('message') or ''}"
    pp, ts = extract_pp_ts(hay, specs.get("tps_values") or [])
    speed = format_speed(row, ts, pp)
    # Quieter speed: "20t/s · 100t/s pp" → keep override formatting
    if ov.get("speed") and ov.get("pp"):
        speed = f'{ov["speed"]} · {ov["pp"]} pp'
    elif ov.get("speed"):
        speed = ov["speed"]
    elif ov.get("pp"):
        speed = f'{ov["pp"]} pp'

    hw_html = html.escape(hardware).replace(", ", " · ")
    price_n = setup_price_value(row, hardware)
    price_attr = f'{price_n:g}' if price_n is not None else ""
    rank_n = setup_rank_value(model, bl_stats)
    rank_attr = str(rank_n) if rank_n is not None else ""

    parts = [
        f'<div class="setup setup-rich" data-search="{html.escape(search_key, quote=True)}" '
        f'data-price="{html.escape(price_attr, quote=True)}" '
        f'data-rank="{html.escape(rank_attr, quote=True)}">',
        f'<div class="model-box"><span class="model-name">{html.escape(model)}</span></div>',
        '<div class="results-box">',
        '<div class="rich-stack">',
        rich_field("quant", html.escape(quant_label or "—")),
        render_rich_version(version_label, version_url),
        render_rich_rank(model, bl_stats),
        '<div class="rich-rule" aria-hidden="true"></div>',
        rich_field("hardware", hw_html),
        rich_field("price", html.escape(price)),
        render_memory_field(ov),
        rich_field("speed", html.escape(speed)),
        render_rich_info(extra),
        render_rich_info(ov.get("info2") or "", "info2"),
        "</div>",
        "</div>",
        "</div>",
    ]
    return "".join(parts)


def render_box(row: dict, bl_stats: dict) -> str:
    ov = SETUP_DISPLAY_OVERRIDES.get(row.get("id") or "", {})
    if ov.get("rich"):
        return render_rich_box(row, bl_stats, ov)

    specs = row.get("specs") or {}
    hay = f"{row.get('speed') or ''}\n{row.get('message') or ''}"
    pp, ts = extract_pp_ts(hay, specs.get("tps_values") or [])
    extra = leftover_message(row)

    model = display_model(row) or "(unspecified)"
    quant = row.get("quantization") or ""
    hardware = display_hardware(row)
    version_label, version_url = version_display(row, quant, model)
    search_key = " ".join(p for p in [model, quant, hardware] if p).lower()
    price_n = setup_price_value(row, hardware)
    price_attr = f'{price_n:g}' if price_n is not None else ""
    rank_n = setup_rank_value(model, bl_stats)
    rank_attr = str(rank_n) if rank_n is not None else ""

    parts = [
        f'<div class="setup" data-search="{html.escape(search_key, quote=True)}" '
        f'data-price="{html.escape(price_attr, quote=True)}" '
        f'data-rank="{html.escape(rank_attr, quote=True)}">',
        f'<div class="model-box"><span class="model-name">{html.escape(model)}</span></div>',
        '<div class="results-box">',
        '<div class="spec-block">',
        render_quant(row),
        render_version(version_label, version_url),
        render_rankings(model, bl_stats),
        "</div>",
        subhead(),
        '<div class="spec-block">',
        field("hardware", hardware),
        render_price(hardware, row),
        field("speed", format_speed(row, ts, pp)),
        render_info(extra),
        "</div>",
        "</div>",
        "</div>",
    ]
    return "".join(parts)


STYLE = """
:root {
  --copper1:#b87333; --copper2:#7a3f16; --ink:#111; --line:#d8d2c8; --black:#000;
  --copper-g1:#f2d4a8; --copper-g2:#e8b070; --copper-g3:#b87333; --copper-g4:#965520; --copper-g5:#5c3010;
  /* Instrument panel (first-card language) */
  --rich-ink:#141414; --rich-mute:#8a8a8a; --rich-line:#ececec;
  --rich-panel:#fafafa; --rich-radius:8px; --page-inset:14px;
  /* Vertical rhythm: brand breathes, tools sit closer to content */
  --space-brand-to-tools: 40px;
  --space-tools-to-cards: 22px;
  --space-section: 18px; /* match .grid gap — even card rhythm across providers */
}
* { box-sizing: border-box; }
body {
  font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--ink); background: #fff; margin: 0; padding: 28px 24px 40px;
  display: flex; flex-direction: column; gap: 0;
}
.header-box {
  border: none; padding: 18px var(--page-inset) 10px;
  text-align: center;
  margin-bottom: var(--space-brand-to-tools);
}
.header-copy h1 { margin: 0; font-size: 56px; letter-spacing: 1px; line-height: 1.05; }
.tagline-row {
  margin-top: 14px;
  display: flex; flex-direction: column; flex-wrap: wrap;
  align-items: center; justify-content: center;
  gap: 12px;
}
.tagline {
  margin: 0; font-size: 13px; color: #444;
  text-decoration: underline;
}
a.tagline:hover { color: #111; }
/* Top bar: black chips + gradient-grain count badges + icon-only filter */
.chrome {
  margin: 0 var(--page-inset) var(--space-tools-to-cards);
  background: none;
  border: none;
  border-radius: 0;
  padding: 0;
  display: flex; flex-wrap: wrap; gap: 10px 14px;
  align-items: center;
}
.navlinks {
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center; flex: 1;
  min-width: 0;
}
.navlink {
  --cat: #888;
  position: relative;
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 400; color: #d8d8d8;
  text-decoration: none; letter-spacing: .01em;
  border-radius: 8px;
  padding: 6px 6px 6px 12px; line-height: 1.2;
  background: var(--rich-ink);
  transition: background-color .15s ease, color .15s ease;
}
.navlink .nav-label { text-transform: none; font-weight: 400; }
.navlink:hover { background: #232323; color: #fff; }
.navlink.is-active {
  color: #fff;
  background: #232323;
  box-shadow: none;
}
.navlink.is-active .nav-label { font-weight: 400; }
.navlink .navn {
  position: relative; overflow: hidden;
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; height: 20px; padding: 0 6px;
  border-radius: 6px;
  background-image: linear-gradient(
    105deg,
    var(--cat) 0%,
    color-mix(in srgb, var(--cat) 78%, #fff) 70%,
    color-mix(in srgb, var(--cat) 55%, #fff) 100%
  );
}
.navlink .navn::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  opacity: 0.85; mix-blend-mode: overlay;
  background-size: 70px 70px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.navlink .navn::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(90deg, transparent 45%, rgba(255,255,255,.32) 100%);
  mix-blend-mode: soft-light;
}
.navlink .navn-num {
  position: relative; z-index: 1;
  font-size: 10px; font-weight: 600; color: #fff;
  font-variant-numeric: tabular-nums;
}
.navlink.nav-qwen { --cat: #2f6fed; }
.navlink.nav-glm { --cat: #7c3aed; }
.navlink.nav-gemma { --cat: #0f9d58; }
.navlink.nav-minimax { --cat: #e67e22; }
.navlink.nav-mistral { --cat: #e11d48; }
.navlink.nav-other { --cat: #b87333; }
.navlink.is-off {
  color: #8a8a8a;
}
.navlink.is-off:hover { color: #b0b0b0; }
.navlink.is-off .navn {
  filter: grayscale(1);
  background-image: linear-gradient(
    105deg,
    #3a3a3a 0%,
    #5a5a5a 70%,
    #2e2e2e 100%
  );
}
.navlink.is-off .navn-num { color: #e6e6e6; }
.nav-clear {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; flex-shrink: 0;
  margin-left: 2px; padding: 0;
  border: none; border-radius: 8px; cursor: pointer;
  background: transparent; color: #888;
  font-size: 18px; line-height: 1; font-weight: 400;
  transition: color .15s ease, background-color .15s ease;
}
.nav-clear:hover { color: #111; background: #f0f0f0; }
.nav-clear.is-all-off { color: #111; }
.chrome-tools {
  display: flex; align-items: stretch; gap: 8px;
  margin-left: auto;
}
.filter-menu { position: relative; display: flex; z-index: 200; }
.filter-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px; flex-shrink: 0;
  border: none; border-radius: 8px; cursor: pointer;
  background: var(--rich-ink); color: #d8d8d8;
  transition: background-color .15s ease, color .15s ease;
}
.filter-btn:hover { background: #232323; color: #fff; }
.filter-btn[aria-expanded="true"] {
  background: #232323; color: #fff;
  box-shadow: inset 0 0 0 1.5px #4a4a4a;
}
.filter-dropdown {
  position: absolute; right: 0; top: calc(100% + 6px); z-index: 210;
  display: flex; flex-direction: column; gap: 2px;
  min-width: 196px; padding: 6px;
  border: none; border-radius: 8px;
  color: #e8e8e8;
  background: var(--rich-ink);
  box-shadow: 0 16px 40px rgba(0,0,0,.32);
}
.filter-dropdown[hidden] { display: none; }
.filter-group {
  font-size: 10px; letter-spacing: .08em; text-transform: uppercase;
  color: #777; padding: 8px 9px 3px;
}
.filter-group:first-child { padding-top: 4px; }
.filter-rule {
  height: 1px; margin: 5px 6px; background: rgba(255,255,255,.1);
  border: 0;
}
.filter-option {
  position: relative;
  display: block; width: 100%; text-align: left;
  font-family: inherit; font-size: 12px; letter-spacing: .01em;
  color: #cfcfcf; background: none; border: none; border-radius: 6px;
  padding: 8px 10px; cursor: pointer;
  overflow: hidden;
  transition: color .12s ease, background-color .12s ease;
}
.filter-option:hover { background: rgba(255,255,255,.08); color: #fff; }
.filter-option.is-selected {
  color: #fff;
  isolation: isolate;
  background-image: linear-gradient(
    105deg,
    #141414 0%,
    color-mix(in srgb, #141414 70%, #3a3a3a) 60%,
    color-mix(in srgb, #141414 45%, #5a5a5a) 100%
  );
}
.filter-option.is-selected::before {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  opacity: .8; mix-blend-mode: overlay;
  background-size: 120px 120px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.filter-option.is-selected::after {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background: linear-gradient(90deg, transparent 40%, rgba(255,255,255,.22) 100%);
  mix-blend-mode: soft-light;
}
.search-shell {
  position: relative;
  display: flex; align-items: center; gap: 8px;
  min-width: min(220px, 55vw); flex: 0 1 260px; height: 34px;
  border: 1px solid #ddd; border-radius: 8px;
  padding: 0 10px; background: #fff;
  box-shadow: none;
  transition: border-color .2s ease;
}
.search-shell:focus-within {
  border-color: #bbb;
  box-shadow: none;
}
.search-shell .search-ico {
  display: inline-flex; align-items: center; justify-content: center;
  color: #aaa; flex-shrink: 0; pointer-events: none;
  transition: color .2s ease;
}
.search-shell:focus-within .search-ico { color: var(--rich-ink); }
.search-clear {
  display: none; align-items: center; justify-content: center;
  border: none; background: none; color: #aaa;
  font-size: 14px; line-height: 1; cursor: pointer; padding: 0;
  transition: color .15s ease;
}
.search-clear:hover { color: var(--rich-ink); }
.search-shell.has-value .search-clear { display: inline-flex; }
#model-search {
  flex: 1; min-width: 0;
  font-family: inherit; font-size: 12px; font-weight: 400;
  border: none; outline: none;
  padding: 0;
  background: transparent; color: var(--rich-ink);
  box-shadow: none;
}
#model-search:focus { outline: none; box-shadow: none; }
#model-search::placeholder { color: #b0b0b0; font-weight: 400; }
#model-search::-webkit-search-cancel-button { display: none; }
.link-plain {
  display: inline; font-size: inherit; color: var(--ink); text-decoration: underline;
  background: none; border: none; padding: 0; cursor: pointer;
}
.link-plain:hover { color: #444; }
.cats {
  display: flex;
  flex-direction: column;
  gap: var(--space-section);
}
.cat { scroll-margin-top: 24px; }
.cathead {
  --cat: #b87333;
  position: relative; overflow: hidden;
  font-size: 15px; letter-spacing: .5px; margin: 0;
  border: none; padding: 8px 12px; color: #fff; border-radius: 8px;
  background-image: linear-gradient(
    105deg,
    var(--cat) 0%,
    color-mix(in srgb, var(--cat) 72%, #fff) 55%,
    color-mix(in srgb, var(--cat) 35%, #fff) 100%
  );
}
.cathead.cat-qwen { --cat: #2f6fed; }
.cathead.cat-glm { --cat: #7c3aed; }
.cathead.cat-gemma { --cat: #0f9d58; }
.cathead.cat-minimax { --cat: #e67e22; }
.cathead.cat-mistral { --cat: #e11d48; }
.cathead.cat-other { --cat: #b87333; }
.cathead::before {
  content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .22;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  mix-blend-mode: soft-light;
}
.cathead::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(90deg, transparent 40%, rgba(255,255,255,.28) 100%);
}
.cathead > * { position: relative; z-index: 1; }
.cathead .catn { color: rgba(255,255,255,.85); font-size: 12px; margin-left: 4px; }
.cat-results { border: none; padding: 0 var(--page-inset); }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
@media (max-width: 960px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .chrome {
    flex-direction: column-reverse;
    align-items: stretch;
    gap: 10px;
  }
  .navlinks { flex: none; width: 100%; }
  .chrome-tools {
    margin-left: 0;
    width: 100%;
  }
  .chrome-tools .search-shell {
    flex: 1 1 auto;
    min-width: 0;
  }
  /* Filter sits on the left in this layout — open menu to the right */
  .filter-dropdown {
    left: 0;
    right: auto;
  }
}
@media (max-width: 600px) {
  :root { --page-inset: 0; }
  body { padding: 16px 18px 28px; }
  .header-box { padding-left: 0; padding-right: 0; }
  .chrome { margin-left: 0; margin-right: 0; gap: 8px; }
  .navlinks { gap: 5px; }
  .grid { grid-template-columns: 1fr; gap: 14px; }
}
.setup { display: flex; flex-direction: column; gap: 0; }
.model-box {
  --cat: #888;
  position: relative; overflow: hidden;
  border: none; padding: 8px 12px; font-size: 13px;
  font-weight: 600; word-break: break-word; color: #fff;
  border-radius: 8px 8px 0 0;
  background-image: linear-gradient(
    105deg,
    var(--cat) 0%,
    color-mix(in srgb, var(--cat) 72%, #fff) 55%,
    color-mix(in srgb, var(--cat) 35%, #fff) 100%
  );
}
.cat.cat-qwen .model-box, .setup.cat-qwen .model-box { --cat: #2f6fed; }
.cat.cat-glm .model-box, .setup.cat-glm .model-box { --cat: #7c3aed; }
.cat.cat-gemma .model-box, .setup.cat-gemma .model-box { --cat: #0f9d58; }
.cat.cat-minimax .model-box, .setup.cat-minimax .model-box { --cat: #e67e22; }
.cat.cat-mistral .model-box, .setup.cat-mistral .model-box { --cat: #e11d48; }
.cat.cat-other .model-box, .setup.cat-other .model-box { --cat: #b87333; }
.model-box::before {
  content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .22;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  mix-blend-mode: soft-light;
}
.model-box::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(90deg, transparent 40%, rgba(255,255,255,.28) 100%);
}
.model-box .model-name { position: relative; z-index: 1; }
.results-box {
  border: none; padding: 12px;
  background: #f7f7f7; border-radius: 0 0 8px 8px;
}
.spec-subhead {
  border-top: 1px solid #e0e0e0; margin: 10px -12px 8px; padding: 6px 12px 0;
  font-size: 12px; letter-spacing: .4px; color: #666;
}
.spec-subhead-line { padding: 0; margin: 10px -12px 8px; height: 0; }
.f { display: flex; gap: 8px; margin: 3px 0; font-size: 13px; }
.f .k { min-width: 74px; color: #666; flex-shrink: 0; }
.f .v { flex: 1; min-width: 0; word-break: break-word; white-space: pre-wrap; }
.f .hint { color: var(--copper1); font-size: 11px; }
.info-clamp {
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2;
  overflow: hidden; white-space: normal;
}
.info-v.expanded .info-clamp {
  display: block; -webkit-line-clamp: unset; overflow: visible;
}
.read-more-btn {
  font-family: inherit; font-size: 12px; color: #666; background: none;
  border: none; padding: 0; margin-top: 4px; cursor: pointer; text-decoration: underline;
}
.read-more-btn:hover { color: #111; }
.quant-bits { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; white-space: normal; }
.quant-bit {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 2.4em; height: 2.4em; padding: 0 8px;
  border: 1.5px solid #bbb; border-radius: 999px;
  font-size: 12px; color: #333; background: none; line-height: 1;
}
/* First card — quiet instrument panel */
.setup-rich {
  --cat: #888;
  --rich-ink: #141414;
  --rich-mute: #8a8a8a;
  --rich-line: #ececec;
}
.cat.cat-qwen .setup-rich, .setup-rich.cat-qwen { --cat: #2f6fed; }
.cat.cat-glm .setup-rich, .setup-rich.cat-glm { --cat: #7c3aed; }
.cat.cat-gemma .setup-rich, .setup-rich.cat-gemma { --cat: #0f9d58; }
.cat.cat-minimax .setup-rich, .setup-rich.cat-minimax { --cat: #e67e22; }
.cat.cat-mistral .setup-rich, .setup-rich.cat-mistral { --cat: #e11d48; }
.cat.cat-other .setup-rich, .setup-rich.cat-other { --cat: #b87333; }
.setup-rich .model-box {
  padding: 10px 14px;
  letter-spacing: .02em;
  background-image: linear-gradient(
    105deg,
    var(--cat) 0%,
    color-mix(in srgb, var(--cat) 78%, #fff) 70%,
    color-mix(in srgb, var(--cat) 55%, #fff) 100%
  );
}
.setup-rich .model-box::before {
  display: block;
  opacity: 0.85;
  mix-blend-mode: overlay;
  background-size: 140px 140px;
  background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.setup-rich .model-box::after {
  display: block;
  background: linear-gradient(90deg, transparent 45%, rgba(255,255,255,.32) 100%);
  mix-blend-mode: soft-light;
}
.setup-rich .model-name {
  font-weight: 500;
  font-size: 13px;
}
.setup-rich .results-box {
  background: #fafafa;
  padding: 14px 14px 12px;
}
.setup-rich .rich-stack {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.setup-rich .rf {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 10px;
  align-items: baseline;
  font-size: 12px;
  line-height: 1.35;
}
.setup-rich .rl {
  color: var(--rich-mute);
  font-size: 10px;
  letter-spacing: .08em;
  text-transform: uppercase;
  font-weight: 400;
}
.setup-rich .rv {
  color: var(--rich-ink);
  min-width: 0;
  word-break: break-word;
}
.setup-rich .rv .link-plain {
  font-size: 12px;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}
.setup-rich .rich-rule {
  height: 1px;
  background: var(--rich-line);
  margin: 4px 0 2px;
}
.setup-rich .rank-n { font-variant-numeric: tabular-nums; }
.setup-rich .rank-t { color: var(--rich-mute); font-variant-numeric: tabular-nums; }
.setup-rich .rank-note {
  color: var(--rich-mute); font-size: 10px; letter-spacing: .04em;
  margin-left: 2px;
}
.setup-rich .rank-src {
  font-size: 10px; letter-spacing: .04em; color: var(--rich-mute);
  text-decoration: underline; text-underline-offset: 2px;
}
.setup-rich .rank-src:hover { color: var(--cat); }
.setup-rich,
.setup-rich .results-box,
.setup-rich .rich-stack,
.setup-rich .rf { overflow: visible; }
.setup-rich:hover,
.setup-rich:focus-within { z-index: 40; position: relative; }
body.filter-open .setup-rich:focus-within { z-index: auto; }
body.filter-open .tip-rich { display: none !important; }
.setup-rich .mem-ratio {
  display: block;
  font-variant-numeric: tabular-nums;
}
.setup-rich .mem-used { font-weight: 500; }
.setup-rich .mem-sep,
.setup-rich .mem-total { color: #555; }
.setup-rich .mem-allow {
  color: var(--cat);
  font-size: 11px;
}
.setup-rich .mem-bar {
  position: relative;
  margin-top: 6px;
  width: 100%;
  height: 3px;
  border-radius: 0;
  background: #e6e6e6;
  overflow: hidden;
}
.setup-rich .mem-bar-allow,
.setup-rich .mem-bar-fill {
  position: absolute; left: 0; top: 0; bottom: 0;
  border-radius: 0;
}
.setup-rich .mem-bar-allow {
  background: color-mix(in srgb, var(--cat) 32%, #fff);
}
.setup-rich .mem-bar-fill {
  background: var(--cat);
  z-index: 1;
}
.setup-rich .info-clamp { -webkit-line-clamp: 1; white-space: pre-wrap; }
.setup-rich .read-more-btn {
  font-size: 11px;
  letter-spacing: 0;
  text-transform: none;
  color: var(--rich-mute);
  text-decoration: none;
  border-bottom: 1px solid #ccc;
}
.setup-rich .read-more-btn:hover { color: var(--rich-ink); border-bottom-color: #999; }
.hovtxt { position: relative; cursor: help; display: inline; }
.tip {
  display: none; position: absolute; left: 0; top: 100%; z-index: 20;
  min-width: 260px; max-width: 340px; margin-top: 6px; padding: 10px 12px;
  background: #1c1712; color: #f2e9df; border: 1px solid var(--copper2);
  border-radius: 6px; font-size: 12px; box-shadow: 0 6px 20px rgba(0,0,0,.35);
}
.hovtxt:hover .tip:not(.tip-rich) { display: block; }
.setup-rich .tip-rich { display: none; }
.setup-rich .tip-rich.is-open { display: block; }
.tip .tiplink { color: #e6b483; text-decoration: none; font-weight: 600; display: block; margin-bottom: 6px; }
.tip .tr { display: flex; justify-content: space-between; gap: 12px; padding: 2px 0; }
.tip .tl { color: #cbb9a6; }
.tip .tv { color: #fff; }
.tip .rk { color: #b87333; }
.tip .tn { color: #a98f74; font-size: 11px; margin-top: 6px; }
.tip .tsec { color: #e6b483; font-size: 11px; text-transform: uppercase; letter-spacing: .5px; margin: 8px 0 3px; border-top: 1px solid #3a2c1f; padding-top: 6px; }
.tip .tsec:first-of-type { border-top: none; }
.tip .tnn { color: #a98f74; text-transform: none; letter-spacing: 0; }
/* Rich tip — dark ink sheet, grain banner, compact rows */
.setup-rich .hovtxt { border-bottom: none; }
.setup-rich .tip-rich {
  position: fixed; left: 0; top: 0; right: auto; margin: 0;
  width: 260px; max-height: min(72vh, 420px); overflow: hidden;
  z-index: 120; padding: 0; border: none; border-radius: 8px;
  background: var(--rich-ink); color: #e8e8e8;
  box-shadow: 0 16px 40px rgba(0,0,0,.32);
  opacity: 0; transform: translateY(4px);
  transition: opacity .12s ease, transform .12s ease;
  pointer-events: none;
}
.setup-rich .tip-rich.is-open {
  display: block; opacity: 1; transform: none; pointer-events: auto;
}
.setup-rich .tip-rich .tip-banner {
  position: relative; overflow: hidden;
  padding: 10px 12px;
  background-image: linear-gradient(
    105deg,
    #141414 0%,
    color-mix(in srgb, #141414 70%, #3a3a3a) 60%,
    color-mix(in srgb, #141414 45%, #5a5a5a) 100%
  );
}
.setup-rich .tip-rich .tip-banner::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  opacity: .8; mix-blend-mode: overlay;
  background-size: 120px 120px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.setup-rich .tip-rich .tip-banner::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(90deg, transparent 40%, rgba(255,255,255,.22) 100%);
  mix-blend-mode: soft-light;
}
.setup-rich .tip-rich .tip-head {
  position: relative; z-index: 1;
  display: block; font-size: 12px; font-weight: 500; color: #fff;
  text-decoration: none; letter-spacing: .02em;
}
.setup-rich .tip-rich .tip-head:hover { color: #fff; text-decoration: underline; }
.setup-rich .tip-rich .tip-body {
  padding: 10px 12px 11px;
  max-height: min(58vh, 340px); overflow-y: auto;
}
.setup-rich .tip-rich .tip-note {
  margin: 0 0 8px; font-size: 10px; color: #888;
  letter-spacing: .04em; text-transform: uppercase;
}
.setup-rich .tip-rich .tip-hero {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 10px; margin-bottom: 10px; padding-bottom: 9px;
  border-bottom: 1px solid #2e2e2e;
}
.setup-rich .tip-rich .tip-hero-k {
  font-size: 10px; letter-spacing: .08em; text-transform: uppercase; color: #888;
}
.setup-rich .tip-rich .tip-hero-v {
  font-size: 16px; font-weight: 600; color: #fff;
  font-variant-numeric: tabular-nums; letter-spacing: -.02em;
}
.setup-rich .tip-rich .tip-hero-t {
  font-size: 12px; font-weight: 500; color: #9a9a9a;
}
.setup-rich .tip-rich .tip-list { display: flex; flex-direction: column; gap: 5px; }
.setup-rich .tip-rich .tip-row {
  display: grid; grid-template-columns: 1fr auto; gap: 10px;
  align-items: baseline;
}
.setup-rich .tip-rich .tip-k {
  font-size: 11px; color: #9a9a9a; min-width: 0;
}
.setup-rich .tip-rich .tip-v {
  font-size: 11px; color: #eee; font-variant-numeric: tabular-nums;
  text-align: right; white-space: nowrap;
}
.setup-rich .tip-rich .tip-rank {
  color: #777; margin-left: 4px;
}
.copper {
  font-family: inherit; font-size: 14px; cursor: pointer;
  border: none; background: #fff; color: var(--ink);
  padding: 9px 22px;
}
.copper:hover { background: #f5f5f5; }
#submit {
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: .02em;
  text-transform: none;
  padding: 8px 14px;
  border: none;
  border-radius: var(--rich-radius);
  background: var(--rich-ink);
  color: #fff;
  cursor: pointer;
  line-height: 1.2;
  flex-shrink: 0;
}
#submit:hover { background: #2a2a2a; }
/* Submit modal — same black panel language as filter dropdown */
.submit-modal {
  position: fixed; inset: 0; z-index: 400;
  display: flex; align-items: center; justify-content: center;
  padding: 24px 16px;
}
.submit-modal[hidden] { display: none; }
.submit-backdrop {
  position: absolute; inset: 0;
  background: rgba(0,0,0,.55);
}
.submit-panel {
  position: relative; z-index: 1;
  width: min(440px, 100%);
  max-height: min(88vh, 720px);
  display: flex; flex-direction: column;
  border-radius: 8px;
  color: #e8e8e8;
  background: var(--rich-ink);
  box-shadow: 0 16px 40px rgba(0,0,0,.32);
  overflow: hidden;
}
.submit-head {
  position: relative; overflow: hidden; isolation: isolate;
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 14px;
  flex-shrink: 0;
  background-image: linear-gradient(
    105deg,
    #141414 0%,
    color-mix(in srgb, #141414 70%, #3a3a3a) 60%,
    color-mix(in srgb, #141414 45%, #5a5a5a) 100%
  );
}
.submit-head::before {
  content: ""; position: absolute; inset: 0; z-index: 0; pointer-events: none;
  opacity: .8; mix-blend-mode: overlay;
  background-size: 120px 120px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.submit-head::after {
  content: ""; position: absolute; inset: 0; z-index: 0; pointer-events: none;
  background: linear-gradient(90deg, transparent 40%, rgba(255,255,255,.22) 100%);
  mix-blend-mode: soft-light;
}
.submit-head > * { position: relative; z-index: 1; }
.submit-head h2 {
  margin: 0; font-size: 13px; font-weight: 500;
  letter-spacing: .02em; color: #fff;
}
.submit-x {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; padding: 0;
  border: none; border-radius: 6px; cursor: pointer;
  background: #141414; color: #b0b0b0;
  font-size: 18px; line-height: 1;
}
.submit-x:hover { color: #fff; background: #222; }
.submit-form {
  overflow: auto; padding: 0 8px 12px;
  display: flex; flex-direction: column; gap: 2px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.submit-form::-webkit-scrollbar { display: none; width: 0; height: 0; }
.submit-group {
  font-size: 10px; letter-spacing: .08em; text-transform: uppercase;
  color: #777; padding: 10px 9px 4px;
}
.submit-group:first-child { padding-top: 2px; }
.submit-field {
  display: flex; flex-direction: column; gap: 4px;
  padding: 6px 8px 8px;
}
.submit-label {
  font-size: 11px; color: #9a9a9a; letter-spacing: .01em;
}
.submit-hint {
  font-size: 10px; color: #666; margin: 0;
}
.submit-field input,
.submit-field textarea {
  font-family: inherit; font-size: 12px;
  color: #e8e8e8; background: #1c1c1c;
  border: none; border-radius: 6px;
  padding: 8px 10px; outline: none;
  width: 100%; box-sizing: border-box;
  transition: background-color .12s ease;
}
.submit-field input::placeholder,
.submit-field textarea::placeholder { color: #555; }
.submit-field input:focus,
.submit-field textarea:focus {
  background: #222;
}
.submit-field textarea {
  min-height: 72px; resize: none; line-height: 1.4;
}
.submit-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 2px;
}
.submit-provider { position: relative; }
.submit-provider-btn {
  --cat: #555;
  position: relative; isolation: isolate; overflow: hidden;
  display: flex; align-items: center; gap: 8px;
  width: 100%; text-align: left;
  font-family: inherit; font-size: 12px;
  color: #888; background: #1c1c1c;
  border: none; border-radius: 6px; cursor: pointer;
  padding: 8px 10px;
}
.submit-provider-btn:hover { background: #222; color: #cfcfcf; }
.submit-provider-btn.is-set {
  color: #fff;
  background-image: linear-gradient(
    105deg,
    var(--cat) 0%,
    color-mix(in srgb, var(--cat) 78%, #fff) 70%,
    color-mix(in srgb, var(--cat) 55%, #fff) 100%
  );
}
.submit-provider-btn.is-set::before {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  opacity: .85; mix-blend-mode: overlay;
  background-size: 70px 70px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.submit-provider-btn.is-set::after {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background: linear-gradient(90deg, transparent 45%, rgba(255,255,255,.32) 100%);
  mix-blend-mode: soft-light;
}
.submit-provider-btn > * { position: relative; z-index: 1; }
.submit-provider-menu {
  position: absolute; left: 0; right: 0; top: calc(100% + 4px); z-index: 5;
  display: flex; flex-direction: column; gap: 2px;
  padding: 6px; border-radius: 8px;
  background: #111;
  box-shadow: 0 16px 40px rgba(0,0,0,.4);
}
.submit-provider-menu[hidden] { display: none; }
.submit-provider-opt {
  --cat: #888;
  position: relative; isolation: isolate; overflow: hidden;
  display: flex; align-items: center; gap: 8px;
  width: 100%; text-align: left;
  font-family: inherit; font-size: 12px;
  color: #cfcfcf; background: none;
  border: none; border-radius: 6px; cursor: pointer;
  padding: 8px 10px;
}
.submit-provider-opt:hover { background: rgba(255,255,255,.08); color: #fff; }
.submit-provider-opt.is-selected {
  color: #fff;
  background-image: linear-gradient(
    105deg,
    var(--cat) 0%,
    color-mix(in srgb, var(--cat) 78%, #fff) 70%,
    color-mix(in srgb, var(--cat) 55%, #fff) 100%
  );
}
.submit-provider-opt.is-selected::before {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  opacity: .85; mix-blend-mode: overlay;
  background-size: 70px 70px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.submit-provider-opt.is-selected::after {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background: linear-gradient(90deg, transparent 45%, rgba(255,255,255,.32) 100%);
  mix-blend-mode: soft-light;
}
.submit-provider-opt > * { position: relative; z-index: 1; }
.submit-provider-swatch {
  position: relative; overflow: hidden; flex-shrink: 0;
  width: 14px; height: 14px; border-radius: 3px;
  background-image: linear-gradient(
    105deg,
    var(--cat) 0%,
    color-mix(in srgb, var(--cat) 78%, #fff) 70%,
    color-mix(in srgb, var(--cat) 55%, #fff) 100%
  );
}
.submit-provider-swatch::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  opacity: .85; mix-blend-mode: overlay;
  background-size: 40px 40px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.submit-provider-swatch::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(90deg, transparent 45%, rgba(255,255,255,.32) 100%);
  mix-blend-mode: soft-light;
}
.submit-provider-other[hidden] { display: none; }
.submit-provider-other {
  margin-top: 6px;
}
.submit-actions {
  padding: 10px 8px 4px; flex-shrink: 0;
}
.submit-go {
  position: relative; isolation: isolate; overflow: hidden;
  display: block; width: 100%;
  font-family: inherit; font-size: 12px; font-weight: 500;
  letter-spacing: .02em; color: #fff;
  border: none; border-radius: 6px; cursor: pointer;
  padding: 10px 12px;
  background-image: linear-gradient(
    105deg,
    #141414 0%,
    color-mix(in srgb, #141414 70%, #3a3a3a) 60%,
    color-mix(in srgb, #141414 45%, #5a5a5a) 100%
  );
}
.submit-go::before {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  opacity: .8; mix-blend-mode: overlay;
  background-size: 120px 120px; background-repeat: repeat;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.8 -0.45'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.submit-go:hover { color: #fff; filter: brightness(1.12); }
body.submit-open { overflow: hidden; }
body.submit-open .tip-rich { display: none !important; }
"""

SUBMIT_MODAL = """
<div id="submit-modal" class="submit-modal" hidden>
  <div class="submit-backdrop" data-close-submit></div>
  <div class="submit-panel" role="dialog" aria-modal="true" aria-labelledby="submit-title">
    <div class="submit-head">
      <h2 id="submit-title">Submit your setup</h2>
      <button type="button" class="submit-x" data-close-submit aria-label="close">×</button>
    </div>
    <form id="submit-form" class="submit-form">
      <div class="submit-group">Model</div>
      <div class="submit-field">
        <span class="submit-label">Provider</span>
        <div class="submit-provider" id="submit-provider">
          <button type="button" class="submit-provider-btn" id="submit-provider-btn"
            aria-haspopup="listbox" aria-expanded="false">
            <span class="submit-provider-text">Select family</span>
          </button>
          <div class="submit-provider-menu" id="submit-provider-menu" role="listbox" hidden>
            <button type="button" class="submit-provider-opt" role="option" data-value="qwen" data-label="Qwen" style="--cat:#2f6fed">
              <span class="submit-provider-swatch" aria-hidden="true"></span><span>Qwen</span>
            </button>
            <button type="button" class="submit-provider-opt" role="option" data-value="glm" data-label="GLM" style="--cat:#7c3aed">
              <span class="submit-provider-swatch" aria-hidden="true"></span><span>GLM</span>
            </button>
            <button type="button" class="submit-provider-opt" role="option" data-value="gemma" data-label="Gemma" style="--cat:#0f9d58">
              <span class="submit-provider-swatch" aria-hidden="true"></span><span>Gemma</span>
            </button>
            <button type="button" class="submit-provider-opt" role="option" data-value="minimax" data-label="MiniMax" style="--cat:#e67e22">
              <span class="submit-provider-swatch" aria-hidden="true"></span><span>MiniMax</span>
            </button>
            <button type="button" class="submit-provider-opt" role="option" data-value="mistral" data-label="Mistral" style="--cat:#e11d48">
              <span class="submit-provider-swatch" aria-hidden="true"></span><span>Mistral</span>
            </button>
            <button type="button" class="submit-provider-opt" role="option" data-value="other" data-label="Other" style="--cat:#b87333">
              <span class="submit-provider-swatch" aria-hidden="true"></span><span>Other</span>
            </button>
          </div>
          <input type="hidden" name="provider" id="submit-provider-value" value="">
          <input class="submit-provider-other" name="provider_other" id="submit-provider-other"
            autocomplete="off" placeholder="Family name" hidden>
        </div>
      </div>
      <label class="submit-field">
        <span class="submit-label">Name</span>
        <input name="model" required autocomplete="off" placeholder="qwen3.6-35b-a3b">
      </label>
      <label class="submit-field">
        <span class="submit-label">Quantization</span>
        <input name="quant" required autocomplete="off" placeholder="4bit">
      </label>
      <label class="submit-field">
        <span class="submit-label">Version</span>
        <input name="version" required autocomplete="off" placeholder="Qwen3.6-35B-A3B-UD-Q6_K_XL">
      </label>
      <label class="submit-field">
        <span class="submit-label">Context length</span>
        <input name="kv_ctx" inputmode="numeric" autocomplete="off" placeholder="65536">
        <p class="submit-hint">Tokens you actually run — used for the +kv bar</p>
      </label>
      <label class="submit-field">
        <span class="submit-label">Link</span>
        <input name="version_url" type="url" autocomplete="off" placeholder="https://huggingface.co/…">
      </label>

      <div class="submit-group">Hardware</div>
      <label class="submit-field">
        <span class="submit-label">Specs</span>
        <input name="hardware" required autocomplete="off" placeholder="2× RTX 3090 24GB">
      </label>
      <label class="submit-field">
        <span class="submit-label">Price</span>
        <input name="price" required autocomplete="off" placeholder="1400">
      </label>

      <div class="submit-group">Speed</div>
      <div class="submit-row">
        <label class="submit-field">
          <span class="submit-label">Decode (t/s)</span>
          <input name="speed" required autocomplete="off" placeholder="35">
        </label>
        <label class="submit-field">
          <span class="submit-label">Prefill (t/s)</span>
          <input name="pp" autocomplete="off" placeholder="200">
        </label>
      </div>

      <div class="submit-group">Info</div>
      <label class="submit-field">
        <span class="submit-label">How you run it</span>
        <textarea name="info" required placeholder="Engine, flags, offload, concurrency, anything extreme…"></textarea>
      </label>
      <label class="submit-field">
        <span class="submit-label">Email</span>
        <input name="email" type="email" autocomplete="email" placeholder="you@example.com">
        <p class="submit-hint">Helpful for benchmark purposes</p>
      </label>

      <div class="submit-actions">
        <button type="submit" class="submit-go">Submit</button>
      </div>
    </form>
  </div>
</div>
"""

SUBMIT_JS = """
function locallistSubmit() {
  const modal = document.getElementById('submit-modal');
  if (!modal) return;
  modal.hidden = false;
  document.body.classList.add('submit-open');
  if (typeof window.locallistResetSubmitProvider === 'function') {
    window.locallistResetSubmitProvider();
  }
  document.getElementById('submit-provider-btn')?.focus();
}
function locallistCloseSubmit() {
  const modal = document.getElementById('submit-modal');
  if (!modal) return;
  modal.hidden = true;
  document.body.classList.remove('submit-open');
}
(function () {
  const modal = document.getElementById('submit-modal');
  const form = document.getElementById('submit-form');
  if (!modal || !form) return;

  const urlInput = form.querySelector('[name="version_url"]');
  const modelInput = form.querySelector('[name="model"]');
  const quantInput = form.querySelector('[name="quant"]');
  const versionInput = form.querySelector('[name="version"]');
  const providerRoot = document.getElementById('submit-provider');
  const providerBtn = document.getElementById('submit-provider-btn');
  const providerMenu = document.getElementById('submit-provider-menu');
  const providerValue = document.getElementById('submit-provider-value');
  const providerOther = document.getElementById('submit-provider-other');
  const providerText = providerBtn?.querySelector('.submit-provider-text');
  const providerOpts = [...(providerMenu?.querySelectorAll('.submit-provider-opt') || [])];

  function closeProviderMenu() {
    if (!providerMenu || !providerBtn) return;
    providerMenu.hidden = true;
    providerBtn.setAttribute('aria-expanded', 'false');
  }
  function openProviderMenu() {
    if (!providerMenu || !providerBtn) return;
    providerMenu.hidden = false;
    providerBtn.setAttribute('aria-expanded', 'true');
  }
  function setProvider(value, label, color, opts) {
    if (!providerValue || !providerBtn || !providerText) return;
    const focusOther = !opts || opts.focusOther !== false;
    providerValue.value = value || '';
    providerText.textContent = label || 'Select family';
    providerBtn.classList.toggle('is-set', Boolean(value));
    if (value && color) providerBtn.style.setProperty('--cat', color);
    else providerBtn.style.removeProperty('--cat');
    providerOpts.forEach((opt) => {
      opt.classList.toggle('is-selected', opt.dataset.value === value);
    });
    const isOther = value === 'other';
    if (providerOther) {
      providerOther.hidden = !isOther;
      providerOther.required = isOther;
      if (!isOther) providerOther.value = '';
      if (isOther && focusOther) providerOther.focus();
    }
  }
  function resetProvider() {
    setProvider('', 'Select family', '');
    closeProviderMenu();
  }
  window.locallistResetSubmitProvider = resetProvider;

  function guessProvider(hay) {
    const s = String(hay || '').toLowerCase();
    if (s.includes('qwen')) return ['qwen', 'Qwen', '#2f6fed'];
    if (/\\bglm\\b/.test(s) || s.includes('glm-') || s.includes('chatglm')) return ['glm', 'GLM', '#7c3aed'];
    if (s.includes('gemma')) return ['gemma', 'Gemma', '#0f9d58'];
    if (s.includes('minimax')) return ['minimax', 'MiniMax', '#e67e22'];
    if (s.includes('mistral')) return ['mistral', 'Mistral', '#e11d48'];
    return ['other', 'Other', '#b87333'];
  }
  function quantToken(hay) {
    const s = String(hay || '');
    return (
      s.match(/\\bUD-(?:IQ|Q)[0-9][A-Za-z0-9_]*/i) ||
      s.match(/\\b(?:IQ|Q)[0-9][A-Za-z0-9_]*/i) ||
      s.match(/\\b(?:BF16|FP16|FP8|F16|F32|INT8|NF4)\\b/i) ||
      s.match(/(?:^|[_-])(\\d+)bit(?:$|[_-])/i)
    );
  }
  function quantBitsFromHay(hay) {
    const m = quantToken(hay);
    if (!m) return '';
    const t = m[1] ? m[1] + 'bit' : m[0];
    const q = t.match(/^(?:UD-)?(?:IQ|Q)(\\d)/i);
    if (q) return q[1] + 'bit';
    if (/bf16|fp16|f16/i.test(t)) return 'BF16';
    if (/fp8/i.test(t)) return 'FP8';
    if (/int8/i.test(t)) return '8bit';
    if (/^\\d+bit$/i.test(t)) return t.toLowerCase();
    return t;
  }
  function guessModel(repo, file) {
    let s = (file ? file.split('/').pop() : repo) || '';
    s = s.replace(/\\.gguf$/i, '').replace(/-GGUF$/i, '');
    s = s.replace(/^zai-org_/i, '').replace(/^Qwen_/i, '');
    s = s.replace(/[-_.](?:UD-)?(?:IQ|Q)\\d[A-Za-z0-9_]*$/i, '');
    s = s.replace(/[-_.](?:BF16|FP16|FP8|F16|F32|INT8|NF4)$/i, '');
    return s.replace(/_/g, '-').replace(/\\s+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '').toLowerCase();
  }
  function parseHfUrl(raw) {
    const s = String(raw || '').trim();
    if (!s) return null;
    let u;
    try { u = new URL(s); } catch (_) { return null; }
    if (!/(^|\\.)huggingface\\.co$/i.test(u.hostname) && !/(^|\\.)hf\\.co$/i.test(u.hostname)) return null;
    const parts = u.pathname.replace(/\\/+$/, '').split('/').filter(Boolean);
    if (parts.length < 2) return null;
    const org = parts[0];
    const repo = parts[1];
    let file = '';
    const fileIdx = parts.findIndex((p) => p === 'blob' || p === 'resolve');
    if (fileIdx >= 0 && parts[fileIdx + 2]) {
      file = decodeURIComponent(parts.slice(fileIdx + 2).join('/'));
    }
    const hay = [repo, file].filter(Boolean).join(' ');
    let version = ((file ? file.split('/').pop() : repo) || '').replace(/\\.gguf$/i, '');
    if (!file) {
      version = version.replace(/-GGUF$/i, '').replace(/^zai-org_/i, '').replace(/^Qwen_/i, '');
    }
    const quant = quantBitsFromHay(hay);
    const model = guessModel(repo, file);
    const [provider, providerLabel, color] = guessProvider(hay + ' ' + model);
    return { org, repo, file, model, quant, version, provider, providerLabel, color };
  }
  function applyParsed(parsed) {
    if (!parsed) return;
    if (modelInput && parsed.model) modelInput.value = parsed.model;
    if (quantInput && parsed.quant) quantInput.value = parsed.quant;
    if (versionInput && parsed.version) versionInput.value = parsed.version;
    if (parsed.provider) {
      setProvider(parsed.provider, parsed.providerLabel, parsed.color, { focusOther: false });
      if (parsed.provider === 'other' && providerOther && parsed.model) {
        providerOther.value = parsed.model;
      }
    }
  }
  function clearParsedFromLink() {
    [modelInput, quantInput, versionInput].forEach((el) => {
      if (el) el.value = '';
    });
    resetProvider();
  }
  let hfTimer = null;
  let hfFetchGen = 0;
  async function enrichFromApi(parsed) {
    if (!parsed?.org || !parsed?.repo) return parsed;
    const gen = ++hfFetchGen;
    try {
      const res = await fetch(
        'https://huggingface.co/api/models/' +
          encodeURIComponent(parsed.org) + '/' +
          encodeURIComponent(parsed.repo)
      );
      if (!res.ok || gen !== hfFetchGen) return parsed;
      const data = await res.json();
      const siblings = Array.isArray(data.siblings) ? data.siblings : [];
      const ggufs = siblings
        .map((s) => s.rfilename || '')
        .filter((n) => /\\.gguf$/i.test(n));
      if (!parsed.file && ggufs.length === 1) {
        parsed.file = ggufs[0];
        parsed.version = ggufs[0].split('/').pop().replace(/\\.gguf$/i, '');
        const hay = [parsed.repo, parsed.file].join(' ');
        if (!parsed.quant) parsed.quant = quantBitsFromHay(hay);
        if (!parsed.model) parsed.model = guessModel(parsed.repo, parsed.file);
      } else if (!parsed.quant && ggufs.length) {
        for (const n of ggufs) {
          const q = quantBitsFromHay(n);
          if (q) { parsed.quant = q; break; }
        }
      }
      if (data.modelId || data.id) {
        const [provider, providerLabel, color] = guessProvider(
          [parsed.repo, parsed.file, data.modelId || data.id, ...(data.tags || [])].join(' ')
        );
        parsed.provider = provider;
        parsed.providerLabel = providerLabel;
        parsed.color = color;
      }
    } catch (_) {
      /* offline / CORS — local parse is enough */
    }
    return parsed;
  }
  async function onHfUrlChange() {
    const raw = urlInput?.value || '';
    const parsed = parseHfUrl(raw);
    if (!String(raw).trim()) {
      clearParsedFromLink();
      return;
    }
    if (!parsed) return;
    applyParsed(parsed);
    const rich = await enrichFromApi(parsed);
    if (parseHfUrl(urlInput?.value || '')?.repo !== parsed.repo) return;
    applyParsed(rich);
  }
  function scheduleHfParse() {
    clearTimeout(hfTimer);
    hfTimer = setTimeout(onHfUrlChange, 280);
  }
  urlInput?.addEventListener('input', scheduleHfParse);
  urlInput?.addEventListener('blur', onHfUrlChange);
  urlInput?.addEventListener('change', onHfUrlChange);

  providerBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    providerMenu?.hidden ? openProviderMenu() : closeProviderMenu();
  });
  providerOpts.forEach((opt) => {
    opt.addEventListener('click', (e) => {
      e.stopPropagation();
      const color = getComputedStyle(opt).getPropertyValue('--cat').trim() || opt.style.getPropertyValue('--cat');
      setProvider(opt.dataset.value || '', opt.dataset.label || opt.textContent.trim(), color);
      closeProviderMenu();
    });
  });
  document.addEventListener('click', (e) => {
    if (!providerRoot || providerMenu?.hidden) return;
    if (!providerRoot.contains(e.target)) closeProviderMenu();
  });

  modal.querySelectorAll('[data-close-submit]').forEach((el) => {
    el.addEventListener('click', locallistCloseSubmit);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || modal.hidden) return;
    if (providerMenu && !providerMenu.hidden) {
      closeProviderMenu();
      return;
    }
    locallistCloseSubmit();
  });

  function withUnit(raw, unit) {
    const s = String(raw || '').trim();
    if (!s) return '';
    if (/[a-zA-Z%/]/.test(s)) return s;
    return s + unit;
  }
  function withMoney(raw) {
    const s = String(raw || '').trim();
    if (!s) return '';
    if (s.startsWith('$')) return s;
    return '$' + s.replace(/,/g, '');
  }
  function withBit(raw) {
    const s = String(raw || '').trim();
    if (!s) return '';
    if (/bit/i.test(s) || /bf16|fp16|fp8/i.test(s)) return s;
    if (/^\\d+(\\.\\d+)?$/.test(s)) return s + 'bit';
    return s;
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const providerKey = String(fd.get('provider') || '').trim();
    if (!providerKey) {
      providerBtn?.focus();
      return;
    }
    const providerOtherVal = String(fd.get('provider_other') || '').trim();
    if (providerKey === 'other' && !providerOtherVal) {
      providerOther?.focus();
      return;
    }
    const num = (key) => {
      const v = String(fd.get(key) || '').trim();
      if (!v) return null;
      const n = Number(v);
      return Number.isFinite(n) ? n : null;
    };
    const payload = {
      model: String(fd.get('model') || '').trim(),
      provider: providerKey === 'other' ? providerOtherVal : providerKey,
      quant_bits: withBit(fd.get('quant')),
      version_label: String(fd.get('version') || '').trim(),
      version_url: String(fd.get('version_url') || '').trim(),
      hardware: String(fd.get('hardware') || '').trim(),
      kv_ctx: num('kv_ctx'),
      speed: withUnit(fd.get('speed'), 't/s'),
      pp: withUnit(fd.get('pp'), 't/s'),
      price: withMoney(fd.get('price')),
      info: String(fd.get('info') || '').trim(),
      email: String(fd.get('email') || '').trim(),
      rich: true,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    const slug = (payload.model || 'setup').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'setup';
    a.href = URL.createObjectURL(blob);
    a.download = 'locallist-' + slug + '.json';
    a.click();
    URL.revokeObjectURL(a.href);
    form.reset();
    resetProvider();
    locallistCloseSubmit();
  });
})();
function toggleInfo(btn) {
  const wrap = btn.closest('.info-v');
  if (!wrap) return;
  const open = wrap.classList.toggle('expanded');
  btn.textContent = open ? 'read less' : 'read more';
  if (!open) refreshInfoButtons(wrap);
}
function refreshInfoButtons(root) {
  const scope = root || document;
  const wraps = root && root.classList?.contains('info-v')
    ? [root]
    : [...scope.querySelectorAll('.info-v')];
  wraps.forEach((wrap) => {
    const clamp = wrap.querySelector('.info-clamp');
    const btn = wrap.querySelector('.read-more-btn');
    if (!clamp || !btn || wrap.classList.contains('expanded')) return;
    // One-line (rich) / two-line (plain) clamp: only show control when truncated.
    btn.hidden = clamp.scrollHeight <= clamp.clientHeight + 1;
  });
}
document.addEventListener('DOMContentLoaded', () => refreshInfoButtons());
window.addEventListener('resize', () => refreshInfoButtons());
"""

SEARCH_JS = """
(function () {
  const input = document.getElementById('model-search');
  const shell = document.querySelector('.search-shell');
  const clearBtn = document.querySelector('.search-clear');
  if (!input) return;

  function applySearch() {
    const q = input.value.trim().toLowerCase();
    if (shell) shell.classList.toggle('has-value', q.length > 0);
    if (typeof window.locallistApplyFilters === 'function') {
      window.locallistApplyFilters();
    }
  }

  input.addEventListener('input', applySearch);
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      applySearch();
      input.focus();
    });
  }
  window.locallistApplySearch = applySearch;
})();
"""

PRICE_FILTER_JS = """
(function () {
  const btn = document.getElementById('filter-btn');
  const dropdown = document.getElementById('filter-dropdown');
  if (!btn || !dropdown) return;
  const options = [...dropdown.querySelectorAll('.filter-option')];
  const providerLinks = [...document.querySelectorAll('.navlink')];
  const clearBtn = document.getElementById('nav-clear');
  const searchInput = document.getElementById('model-search');
  const flat = document.getElementById('cat-sorted');
  const flatGrid = flat?.querySelector('.grid');
  let sortMode = '';

  function homeSections() {
    return [...document.querySelectorAll('section.cat:not(#cat-sorted)')];
  }

  function numAttr(el, key) {
    const raw = el.dataset[key];
    if (raw === undefined || raw === '') return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  }

  // Tag each card with home category + order (colors stay when flattened)
  let gord = 0;
  homeSections().forEach((cat) => {
    const slug = [...cat.classList].find((c) => c.startsWith('cat-') && c !== 'cat');
    [...cat.querySelectorAll('.setup')].forEach((s, i) => {
      s.dataset.home = cat.id;
      s.dataset.ord = String(i);
      s.dataset.gord = String(gord++);
      if (slug) s.classList.add(slug);
    });
  });

  function cmpNullable(a, b, asc) {
    if (a === null && b === null) return 0;
    if (a === null) return 1;
    if (b === null) return -1;
    return asc ? a - b : b - a;
  }

  function sortSetups(setups, mode) {
    if (!mode) {
      setups.sort((a, b) => Number(a.dataset.gord || 0) - Number(b.dataset.gord || 0));
      return;
    }
    if (mode === 'price-asc' || mode === 'price-desc') {
      const asc = mode === 'price-asc';
      setups.sort((a, b) => {
        const c = cmpNullable(numAttr(a, 'price'), numAttr(b, 'price'), asc);
        return c !== 0 ? c : Number(a.dataset.gord || 0) - Number(b.dataset.gord || 0);
      });
      return;
    }
    if (mode === 'rank-asc' || mode === 'rank-desc') {
      const asc = mode === 'rank-asc';
      setups.sort((a, b) => {
        const c = cmpNullable(numAttr(a, 'rank'), numAttr(b, 'rank'), asc);
        return c !== 0 ? c : Number(a.dataset.gord || 0) - Number(b.dataset.gord || 0);
      });
    }
  }

  function applySort(mode) {
    sortMode = mode || '';
    document.body.classList.toggle('is-sorted', Boolean(sortMode));
    if (!sortMode) {
      homeSections().forEach((cat) => {
        const grid = cat.querySelector('.grid');
        if (!grid) return;
        const setups = [...document.querySelectorAll(`.setup[data-home="${cat.id}"]`)];
        setups.sort((a, b) => Number(a.dataset.ord || 0) - Number(b.dataset.ord || 0));
        setups.forEach((s) => grid.appendChild(s));
      });
    } else if (flatGrid) {
      const setups = [...document.querySelectorAll('.setup')];
      sortSetups(setups, sortMode);
      setups.forEach((s) => flatGrid.appendChild(s));
    }
    applyFilters();
  }

  function providerEnabled(homeId) {
    if (!homeId) return true;
    const link = document.querySelector(`.navlink[href="#${homeId}"]`);
    return !link || !link.classList.contains('is-off');
  }

  function applyFilters() {
    const y = window.scrollY;
    const q = (searchInput?.value || '').trim().toLowerCase();
    document.querySelectorAll('.setup').forEach((setup) => {
      const hay = (setup.dataset.search || setup.querySelector('.model-box')?.textContent || '').toLowerCase();
      const matchSearch = !q || hay.includes(q);
      const matchProv = providerEnabled(setup.dataset.home);
      setup.style.display = matchSearch && matchProv ? '' : 'none';
    });
    if (sortMode && flat) {
      homeSections().forEach((cat) => { cat.style.display = 'none'; });
      const any = [...flat.querySelectorAll('.setup')].some((s) => s.style.display !== 'none');
      flat.style.display = any ? '' : 'none';
    } else {
      if (flat) flat.style.display = 'none';
      homeSections().forEach((cat) => {
        const any = [...cat.querySelectorAll('.setup')].some((s) => s.style.display !== 'none');
        cat.style.display = any ? '' : 'none';
      });
    }
    // Hiding sections shrinks the page; keep scroll from clamping to the bottom.
    requestAnimationFrame(() => {
      const max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      if (y > max) window.scrollTo(0, 0);
    });
  }
  window.locallistApplyFilters = applyFilters;

  function allProvidersOff() {
    return providerLinks.length > 0 && providerLinks.every((l) => l.classList.contains('is-off'));
  }
  function syncClearBtn() {
    if (!clearBtn) return;
    const allOff = allProvidersOff();
    clearBtn.classList.toggle('is-all-off', allOff);
    clearBtn.setAttribute('aria-label', allOff ? 'select all providers' : 'deselect all providers');
    clearBtn.title = allOff ? 'select all' : 'deselect all';
  }

  // Provider chips toggle category on/off (number goes B&W when off)
  providerLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      link.classList.toggle('is-off');
      applyFilters();
      syncClearBtn();
    });
  });

  // × toggles deselect-all / reselect-all
  clearBtn?.addEventListener('click', () => {
    const allOff = allProvidersOff();
    providerLinks.forEach((l) => l.classList.toggle('is-off', !allOff));
    applyFilters();
    syncClearBtn();
  });
  syncClearBtn();

  function openMenu() {
    dropdown.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    document.body.classList.add('filter-open');
    document.querySelectorAll('.tip-rich.is-open').forEach((tip) => {
      tip.classList.remove('is-open');
      tip.style.visibility = '';
    });
  }
  function closeMenu() {
    dropdown.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('filter-open');
  }

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.hidden ? openMenu() : closeMenu();
  });
  document.addEventListener('click', (e) => {
    if (!dropdown.hidden && e.target !== btn && !dropdown.contains(e.target)) closeMenu();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMenu();
  });
  options.forEach((opt) => {
    opt.addEventListener('click', () => {
      options.forEach((o) => o.classList.toggle('is-selected', o === opt));
      applySort(opt.dataset.sort || '');
      closeMenu();
    });
  });
  applyFilters();
})();
"""

NAV_SPY_JS = """
(function () {
  const links = [...document.querySelectorAll('.navlink')];
  if (!links.length) return;
  const sections = links
    .map((a) => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);
  if (!sections.length) return;

  function setActive(id) {
    links.forEach((a) => {
      a.classList.toggle('is-active', a.getAttribute('href') === '#' + id);
    });
  }

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) setActive(visible.target.id);
    },
    { rootMargin: '-45% 0px -45% 0px', threshold: [0, 0.1, 0.5, 1] }
  );
  sections.forEach((s) => observer.observe(s));
  setActive(sections[0].id);
})();
"""

TIP_JS = """
(function () {
  function placeTip(wrap, tip) {
    tip.classList.add('is-open');
    tip.style.visibility = 'hidden';
    const r = wrap.getBoundingClientRect();
    const tw = tip.offsetWidth || 260;
    const th = tip.offsetHeight || 200;
    const pad = 10;
    let top = r.bottom + 8;
    let left = r.left;
    if (top + th > window.innerHeight - pad) top = Math.max(pad, r.top - th - 8);
    if (left + tw > window.innerWidth - pad) left = Math.max(pad, window.innerWidth - tw - pad);
    if (left < pad) left = pad;
    tip.style.top = top + 'px';
    tip.style.left = left + 'px';
    tip.style.visibility = '';
  }
  function closeTip(tip) {
    tip.classList.remove('is-open');
    tip.style.visibility = '';
  }
  document.querySelectorAll('.setup-rich .hovtxt').forEach((wrap) => {
    const tip = wrap.querySelector('.tip-rich');
    if (!tip) return;
    let hideTimer = null;
    const show = () => {
      if (document.body.classList.contains('filter-open')) return;
      clearTimeout(hideTimer);
      placeTip(wrap, tip);
    };
    const hide = () => {
      hideTimer = setTimeout(() => closeTip(tip), 120);
    };
    wrap.addEventListener('mouseenter', show);
    wrap.addEventListener('mouseleave', hide);
    tip.addEventListener('mouseenter', () => {
      clearTimeout(hideTimer);
      tip.classList.add('is-open');
    });
    tip.addEventListener('mouseleave', hide);
    window.addEventListener('scroll', () => {
      if (tip.classList.contains('is-open')) placeTip(wrap, tip);
    }, { passive: true });
  });
})();
"""


def cat_slug(name: str) -> str:
    return "cat-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _glm_version_key(row: dict) -> tuple[int, int]:
    """Parse glm-X.Y so higher versions sort first when reversed."""
    m = re.search(r"(\d+)\.(\d+)", display_model(row).lower())
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


def _qwen_sort_key(row: dict) -> tuple[int, int, int, float]:
    """
    Qwen order (desc): series → size → coder last.
    e.g. 3.6-35b → 3.6-27b → 3.5-397b → … → 3.5-0.8b → coder-next
    """
    m = display_model(row).lower()
    size_m = re.search(r"(\d+(?:\.\d+)?)\s*b\b", m)
    size = float(size_m.group(1)) if size_m else 0.0
    ver = re.search(r"qwen\s*(\d+)\.(\d+)", m)
    if ver:
        return (1, int(ver.group(1)), int(ver.group(2)), size)
    if "coder" in m:
        # below mainline 3.x series; next > bare coder via size proxy
        next_boost = 1.0 if "next" in m else 0.0
        return (0, 3, 0, next_boost)
    return (0, 0, 0, size)


def _quant_bit_value(row: dict) -> float:
    """Numeric bit depth from display label (8bit → 8, 5.5bit → 5.5)."""
    m = re.search(r"(\d+(?:\.\d+)?)", display_quant_bits(row) or "")
    return float(m.group(1)) if m else 0.0


def grouped(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(provider_of(r), []).append(r)

    def _by_key(key_fn):
        # model identity → higher bit first → newer posts
        return lambda r: (
            key_fn(r),
            _quant_bit_value(r),
            r.get("month") or "",
            r.get("id") or "",
        )

    for name, rs in groups.items():
        if name == "GLM":
            key_fn = _glm_version_key
        elif name == "Qwen":
            key_fn = _qwen_sort_key
        else:
            key_fn = lambda r: display_model(r).lower()
        rs.sort(key=_by_key(key_fn), reverse=True)

    def sort_key(item: tuple[str, list[dict]]) -> tuple[int, int, str]:
        name, rs = item
        return (name == "Other", -len(rs), name)

    return sorted(groups.items(), key=sort_key)


FUNNEL_SVG = (
    '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">'
    '<path d="M2 3.2h12L9.4 8.3v4.9l-2.8 1.4V8.3L2 3.2z" '
    'stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" stroke-linecap="round"/>'
    "</svg>"
)
SEARCH_SVG = (
    '<svg class="search-ico" width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">'
    '<circle cx="7" cy="7" r="4.25" stroke="currentColor" stroke-width="1.3"/>'
    '<path d="M10.2 10.2L13.5 13.5" stroke="currentColor" stroke-width="1.3" '
    'stroke-linecap="round"/>'
    "</svg>"
)


def build_chrome(order: list[tuple[str, list[dict]]]) -> str:
    """Category chips + icon-only price filter + search."""
    boxes = "".join(
        f'<a class="navlink nav-{cat_slug(name).removeprefix("cat-")}" '
        f'href="#{cat_slug(name)}">'
        f'<span class="nav-label">{html.escape(name)}</span>'
        f'<span class="navn"><span class="navn-num">{len(rs)}</span></span></a>'
        for name, rs in order
    )
    return (
        f'<div class="chrome">'
        f'<div class="navlinks">{boxes}'
        f'<button type="button" class="nav-clear" id="nav-clear" '
        f'aria-label="deselect all providers" title="deselect all">×</button>'
        f'</div>'
        f'<div class="chrome-tools">'
        f'<div class="filter-menu">'
        f'<button type="button" id="filter-btn" class="filter-btn" '
        f'aria-haspopup="true" aria-expanded="false" aria-label="sort setups">'
        f"{FUNNEL_SVG}</button>"
        f'<div class="filter-dropdown" id="filter-dropdown" role="menu" hidden>'
        f'<div class="filter-group">Price</div>'
        f'<button type="button" class="filter-option" data-sort="price-asc" role="menuitem">'
        f"Ascending</button>"
        f'<button type="button" class="filter-option" data-sort="price-desc" role="menuitem">'
        f"Descending</button>"
        f'<div class="filter-group">Model rank</div>'
        f'<button type="button" class="filter-option" data-sort="rank-asc" role="menuitem">'
        f"Ascending</button>"
        f'<button type="button" class="filter-option" data-sort="rank-desc" role="menuitem">'
        f"Descending</button>"
        f'<hr class="filter-rule">'
        f'<button type="button" class="filter-option is-selected" data-sort="" role="menuitem">'
        f"Default order</button>"
        f"</div></div>"
        f'<div class="search-shell">'
        f"{SEARCH_SVG}"
        f'<input id="model-search" type="search" placeholder="search" '
        f'aria-label="search setups">'
        f'<button type="button" class="search-clear" aria-label="clear search">×</button>'
        f"</div></div></div>"
    )


def build_sections(order: list[tuple[str, list[dict]]], bl_stats: dict) -> str:
    out = []
    for name, rs in order:
        boxes = "\n".join(render_box(r, bl_stats) for r in rs)
        slug = cat_slug(name).removeprefix("cat-")
        out.append(
            f'<section class="cat cat-{slug}" id="{cat_slug(name)}">'
            f'<div class="cat-results">'
            f'<div class="grid">{boxes}</div></div></section>'
        )
    return "\n".join(out)


def build_html(rows: list[dict], bl_stats: dict) -> str:
    order = grouped(rows)
    chrome = build_chrome(order)
    sections = build_sections(order, bl_stats)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>locallist</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{STYLE}</style>
</head>
<body>
<div class="header-box">
<div class="header-copy">
<h1>locallist</h1>
<div class="tagline-row">
<a class="tagline" href="hamsters.html">“The hamsters go brrrrr”</a>
<button id="submit" type="button" onclick="locallistSubmit()">Submit your setup</button>
</div>
</div>
</div>
{chrome}
<div class="cats">
{sections}
<section class="cat cat-sorted" id="cat-sorted" style="display:none" aria-label="sorted setups">
<div class="cat-results"><div class="grid"></div></div>
</section>
</div>
{SUBMIT_MODAL}
<script>{SUBMIT_JS}{SEARCH_JS}{PRICE_FILTER_JS}{NAV_SPY_JS}{TIP_JS}</script>
</body>
</html>
"""


def build_hamsters_html() -> str:
    """Essay page linked from the locallist tagline."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The hamsters go brrrrr</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root { --ink:#111; --rich-ink:#141414; --mute:#888; }
* { box-sizing: border-box; }
body {
  font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--ink); background: #fff; margin: 0;
  padding: 28px 24px 60px;
}
.shell { max-width: 40rem; margin: 0 auto; }
.back {
  display: inline-block; font-size: 12px; color: var(--mute);
  text-decoration: none; margin-bottom: 28px;
}
.back:hover { color: var(--ink); }
.header-box { text-align: center; margin-bottom: 0; }
.header-box h1 {
  margin: 0;
  font-size: clamp(26px, 5.5vw, 40px);
  font-weight: 400;
  letter-spacing: 1px;
  line-height: 1.1;
}
.subheader {
  margin: 14px 0 0;
  font-size: 13px; line-height: 1.55; color: #444;
}
.hero {
  display: block; width: 100%; height: auto;
  margin: 28px 0 24px;
}
.thread {
  margin: 0 0 1.4em;
}
.thread .quote {
  margin: 0;
  font-size: 13px; line-height: 1.55; color: #444;
  font-style: italic;
}
.thread .reply {
  position: relative;
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: 13px; line-height: 1.55; color: #444;
  font-style: italic;
}
.thread .reply::before {
  content: "";
  position: absolute;
  left: 0;
  top: -8px;
  width: 12px;
  height: calc(0.7em + 8px);
  border-left: 1px solid #444;
  border-bottom: 1px solid #444;
  border-bottom-left-radius: 10px;
  pointer-events: none;
}
.essay .byline {
  margin: 0 0 1.4em;
  font-size: 12px; color: var(--mute);
}
.essay .rule {
  border: 0; border-top: 1px solid #e0e0e0;
  margin: 0 0 1.6em;
}
.essay .body p {
  margin: 0 0 1.15em;
  font-size: 13px; line-height: 1.55; color: #444;
}
.essay .body h2 {
  margin: 1.8em 0 0.85em;
  font-size: 16px; font-weight: 400; letter-spacing: 1px; line-height: 1.4;
  color: #111;
}
.essay .body h2:first-child { margin-top: 0; }
@media (max-width: 600px) {
  body { padding: 16px 18px 40px; }
  .hero { margin: 22px 0 20px; }
}
</style>
</head>
<body>
<div class="shell">
  <a class="back" href="locallist.html">← locallist</a>
  <header class="header-box">
    <h1>The hamsters go brrrrr</h1>
    <p class="subheader">A year inside the Discord server where people spend their life savings to run a 27b model instead of paying Anthropic $20 dollars a month.</p>
  </header>
  <img class="hero" src="hamsters-hero.jpg" alt="A DIY multi-GPU rack on a wire shelf, tangled in power cables" width="1024" height="768">
  <article class="essay">
    <div class="thread">
      <p class="quote">“In the next 2 weeks, assuming I can figure out how to mount everything onto some kind of frame, I should have as many as 30 V340Ls (60 GPUs) connected to a single server.”</p>
      <p class="reply">“Hall of fame material”</p>
    </div>
    <p class="byline">Edited by Daniel Kiss</p>
    <hr class="rule">
    <div class="body">
      <p>Ready or not, personal local language models (the smaller, more private, more efficient kind) are coming to the people.</p>
      <p>Should the frontier labs be worried? Not immediately. But the band of revolutionaries taking charge are coming from bedrooms all over the world, wiring 220-volt outlets by hand at 2am. Thousands of these makeshift GPU-burning data-centre enthusiasts have clustered in a Discord server named LocalLLM, where the collective wisdom is to not ask permission from OpenAI or Anthropic to access intelligence. This is their story: a year’s worth of chatter and banter, directly from those who turned their hobby into a religion.</p>
      <h2>July 2025 — “It’s time to get serious”</h2>
      <p>“It’s time to get serious.” Six thumbs-up and one frowning face. This is how it all started almost a year ago on the 14th of July. What they meant by serious we will never know, but it foreshadows the storm that soon followed: the frantic new open-weight model releases, the benchmarks, and the rise of GPU prices. Serious it became…</p>
      <p>The silence was broken a week later, when a curious passerby asked for recommendations on a local coding agent. It did not have to be smart, but most importantly it had “to fit reasonably in 24GB of VRAM.” The answer came later in July: a recommendation for DeepSeek Coder V2 Lite at Q4_K_M with a 30k context window, good enough for autocomplete in VS Code. Space, memory, RAM, compute — whatever you want to call it — would become the community’s most sacred constraint. It did not matter how good the models were if you could not run them on consumer hardware. Enchanted by the promise of infinite intelligence, people upgraded their Macs, repurposed their gaming setups just to get a taste of what it would feel like to truly own your own model, and of course talk about them.</p>
      <h2>August 2025 — “WE MUST CONSTRUCT ADDITIONAL PYLONS!”</h2>
      <p>August saw some unglamorous house cleaning. The first mods were appointed; channels for models, hardware, use-cases, and home-labbing were brought into existence. The trickle of hellos slowly became conversations, and Reddit’s r/LocalLLaMA moderators started showing up as regular participants. TrentBot began cross-posting r/LocalLLaMA’s “rising” threads into #general and within two days people were asking for it to be caged.</p>
      <p>GPT-5 arrived on August 8th to an unenthused audience, Sonnet 4 still ate their lunch on coding, and corporate benchmarking was dismissed: “if it’s OpenAI I’m going to disregard it like a crazy person screaming in the train station.” Suspicion compounded when several members suspected they were quietly being served 4o. Chat transcripts of the model insisting otherwise were shared: “here you can see it gaslighting me, lmao.” When gpt-oss-20b and 120b arrived mid-month, the community worked on reverse-engineering it: a member discovered that OpenAI’s own Harmony prompt-format repo was broken and rebuilt it themselves, telling the channel, “Nobody has Harmony prompting working right. OpenAI’s own Harmony repo isn’t even right.” That do-it-yourself instinct governed the LocalLLM community. People came from all over to approach technology with their own eyes rather than rely on the wisdom of those above them.</p>
      <p>Members really did come from all over. A member with the handle CoralAnchor, already living in a kind of internal exile after his Reddit account got shadowbanned for the crime of editing a comment through a VPN, started offering benchmark data like a man smuggling contraband across a border: “Since all my poor posts got annihilated when my account got shadow banned, I’ll have to send you to github mirrors, but here are some speed numbers for the M2 Ultra and M3 Ultra.”</p>
      <p>However, the real excitement that month came from BlueFalcon, newly minted folk hero. He announced on August 17th that he was running something like two hundred simultaneous coding agents off a single RTX 4090 using gpt-oss-20b through vLLM’s live-batching, hitting nine thousand tokens a second, a cartoonish number that went semi-viral on Reddit and dragged the whole Discord into a week of agent-orchestration theology. BlueFalcon delivered this triumph the way a man delivers a toast at his own wedding, unable to resist the bit: “WE MUST CONSTRUCT ADDITIONAL PYLONS,” with an honest admission that “tool calling in oss-20b is broken.” CoralAnchor, watching from the exile bench, replied, “I keep coming back to the idea that I’d probably have a nervous breakdown at having to code review that much stuff.”</p>
      <p>The debate over hardware would also become prevalent. People either went the CPU (Apple) or GPU (any random graphics card you had lying around) route. BlueFalcon summed up the Mac-versus-Nvidia debate in one line that month: “Apple computers have the RAM capacity, but not enough compute power; NVIDIA is the opposite.”</p>
      <p>By month’s end the model conversation had rotated again. DeepSeek V3.1 landed with a member warning its GGUF quants would occupy his compute for twenty hours, Hermes 4 arrived from Nous Research, and a member’s rapid-fire GLM finetunes brought out humour going back to the “Wizard-Alpaca-Vicuna-Koala-Chronos-Nous-Puffin-13b.ggml” days.</p>
      <h2>September 2025 — “I like watching the hamsters go brrrrr”</h2>
      <p>By September, the rhythm of the LocalLLM server had settled and model releases started to flow. On September 3rd, Kimi-K2-Instruct-0905 was released and the same day gpt-oss-120b was crowned top open-source model on Artificial Analysis’s intelligence index.</p>
      <p>Then there was MossyBadger, whose late-September buying spree turned #general into a live hardware opera: multiple RTX 6000 Pro Blackwell workstation cards, roughly $45,000 spent by month’s end, and a stated plan to hit four Blackwell 96GB cards by Christmas. “Yo. Where do I buy an H200?” kicked it off and ended with a reality check: “It’s all fun and games until you try to wire the 220 outlet yourself.” In between, CoralAnchor, the server’s resident exiled benchmark priest, talked him down from the datacenter card with an argument that the H200’s real advantage is parallel throughput for many users, not raw speed for one guy alone in a room, so “an individual user would get far more bang for the buck at that price buying 3 of the RTX 6000 96GB.” A spectator chimed in: “You could literally get a used car for that price.” Another member, StaticMagnet, encouraging the whole spectacle to unfold, offered the concluding hardware prayer, noting this was “purely for my entertainment… I like watching the hamsters go brrrrrr.” This wasn’t about productivity anymore; this was about the hamsters.</p>
      <p>The month’s model chatter was primarily about Alibaba’s dominance. Qwen releases outpaced everything else with the release of Omni Captioner, Thinking, and Instruct; then Qwen3-Max hit third on the Text Arena leaderboard; then a roadmap teasing million-to-hundred-million-token context and ten-trillion-parameter ambitions was announced. MossyBadger vowed to “shitpost Qwen” once the dust settled. GLM 4.6 was also released at the end of the month and became the coding and agent model people actually wanted to switch to. A member admitted “if it can actually match sonnet 4 i’ll switch, tired of being robbed by Anthropic,” a feeling shared by StaticMagnet, who was burning $250 a week on Anthropic credits. There was disappointment when no Air variant was announced for VRAM-constrained users — “no air no joy” — but within hours a community mlx-6bit quant appeared because the hamsters just keep running.</p>
      <p>In September, the consensus was that if you wanted raw capability you went to the cloud providers, but to “tinker and learn” you went local. Issues of privacy were also raised: “anything going to a proprietary AI should be considered semi-public.” A standout highlight was a member impulsively deciding to start a Kimi K2 fan club with the launch of r/kimimania and publishing a Kimi-themed story the same week.</p>
      <h2>October 2025 — “guys it’s a woke communist server”</h2>
      <p>In October, the GLM hype train continued. The GGUF dropped on the 1st and by the 6th, it had already hit #1 trending on Hugging Face. The community deduced it was about eight times cheaper than Claude Sonnet 4.5 and, on tool-call accuracy, competitive with Sonnet, GPT-5, and Grok. This was a big win for open-source.</p>
      <p>StaticMagnet spent the first days of October assembling a four-card RTX 6000 Pro Blackwell rig atop a Threadripper 7995WX, 512GB of DDR5, and 16TB of NVMe. “God I hate scalpers,” he wrote, “The fact that there are order limits on Blackwells and I can’t even get how many I need for a build because people would buy them all up to resell.” Mid-build he ordered two more cards anyways. By the 7th, he was reporting GLM-4.6 at 8-bit running with EAGLE speculative decoding and FP8: “OMFG I’m getting ~50tok/sec on GLM 4.6 8bit.” This figure was quite good given 44 t/s was achieved on an 8×H200 cluster. GLM 4.6 has about 357B parameters. Even at Q8_0 quantization from Unsloth (a local UI for training and running local models) on 4× Blackwell 6K Pros, it would only leave about 5GB of VRAM for KV Cache, the equivalent of 13,300 input tokens or a 20-page double-spaced history essay. StaticMagnet gave his personal economics: “Someone help me with the math. I spent $64k to save $20/mo on ChatGPT. Am I winning yet?” — “You only need like 266 years to recoup your investment.”</p>
      <p>VelvetComet, another member, tested GLM-4.6 for finding pitfalls with his idea and reported it passed brilliantly but “THE SYCOPHANCY!!!! It’s like at the GPT-4o/4.1 era sycophancy levels.” Another member tested sensitive mental-health prompts, and sided with the incumbent: “it’s part of why I like claude in terms of closed models.” Closed models still had an edge with their harnesses.</p>
      <p>Not everyone was shelling out thousands on GPUs. CoralAnchor debunked how Mac buyers were deceived by total tokens-per-second without realizing the long prompt processing speeds. Others argued multi-GPU consumer setups (3060s, 3090s, a 4070 Ti paired with a 2070) over tensor-split configs, and quants were also debated: mxfp4 versus fp8 versus int4/NVFP4. SillyTavern roleplay sessions also broke when OpenRouter pulled DeepSeek 3.1’s free tier and dragged one person into a long debugging spiral. StaticFalcon translated an entire web novel and wrote “the quality is so much better than Google Translate.” October also saw the release of DeepSeek-OCR, MiniMax-M2, and Granite 4.0. To end, a member tossed in “let’s be honest guys it’s a woke communist server,” which detonated days of argument over communism and capitalism, VelvetComet adding “I actually lived under commies. I’m originally from Russia and born in 1977.” MoltenCactus summarized the state of LocalLLM aptly: “this server’s got range, llm to commies to umamusume.”</p>
      <h2>November 2025 — “they gotta negotiate supply like OPEC”</h2>
      <p>November’s wound was NVIDIA’s DGX Spark, the datacenter that could now sit on everyone’s desk with 128GB of memory for the low, low price of $5k. For three days, from November 3rd through the 5th, the channel performed an autopsy on the machine. Pros were the CUDA ecosystem, which made the box still feel safer than AMD’s Strix Halo, but fears of a cheaper and faster Spark 2.0 on the horizon led many to ponder. The benchmark on performance was as always “how many (insert your favourite hardware) does it take to = a claude plan?”</p>
      <p>The problem was that November was the month the RAM markets turned upside down. A 192GB DDR4 kit which cost $900 in late October pushed past $3000 by the end of the month. “They gotta negotiate supply like OPEC,” a member wrote. Another member also noticed something odd: every RTX 5090 for rent on vast.ai had seemingly disappeared within a few hours. The “just build a rig” optimism was being crushed by strange outside forces.</p>
      <p>It wasn’t just the markets. Signs of real fear over job security also emerged. VelvetGlacier wrote regarding all the fine-tuning and agentic workflows that “my career is being quickly eaten by agents. I’d rather be the person doing the agents, and still employed.” More cynicism ensued: “get on this ai bubble money... learn enough to get a job in the industry, get overpaid while you really learn how to do it, and then hopefully you can keep it up and outlast the other people trying to do the same thing.” The community joked “I did not know deepseek was a skill.”</p>
      <p>Kimi K2 Thinking landing on the 7th of November kept the general channel buzzing for two weeks — the first trillion-parameter open-weight model ever released. The community fired back to the model’s widely shared $4.6 million training-cost claim: “Obviously that doesn’t include the cost of chips or building a datacenter. That’s their electricity bill for the training run.” Nevertheless, GLM 4.6 still held its ground for VRAM-constrained builds. The launch of Google Gemini 3 Pro turned attention to cloud models before a Cloudflare outage that same week vindicated self-hosting.</p>
      <p>ArliAI’s GLM-4.5-Air-Derestricted and gpt-oss-20b-Derestricted, using a “norm-preserving biprojected abliteration” method, also drew reactions. MellowCactus humorously commented “what a relief, I need to update my meth recipe.”</p>
    </div>
  </article>
</div>
</body>
</html>
"""


def main() -> None:
    liked_doc = json.loads(LIKED.read_text(encoding="utf-8"))
    liked_ids = [mid for mid, on in liked_doc.get("liked", {}).items() if on]
    by_id = {r["id"]: r for r in json.loads(SETUPS.read_text(encoding="utf-8"))["setups"]}
    rows = [by_id[mid] for mid in liked_ids if mid in by_id]
    rows.sort(key=lambda r: (r.get("month", ""), r.get("id", "")), reverse=True)
    bl_stats = json.loads(BL_STATS.read_text(encoding="utf-8")) if BL_STATS.exists() else {}
    html = build_html(rows, bl_stats)
    OUT.write_text(html, encoding="utf-8")
    INDEX_OUT.write_text(html, encoding="utf-8")
    HAMSTERS_OUT.write_text(build_hamsters_html(), encoding="utf-8")
    if HAMSTERS_HERO_SRC.exists():
        shutil.copy2(HAMSTERS_HERO_SRC, HAMSTERS_HERO)
        print(f"Wrote {HAMSTERS_HERO}")
    print(f"Wrote {OUT} ({len(rows)} setups)")
    print(f"Wrote {INDEX_OUT}")
    print(f"Wrote {HAMSTERS_OUT}")


if __name__ == "__main__":
    main()
