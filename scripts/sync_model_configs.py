#!/usr/bin/env python3
"""Resolve Hugging Face repos, copy config.json, and write architectural notes.

  python3 scripts/sync_model_configs.py
"""

from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "open-models.json"
PAGES = ROOT / "data" / "model-pages"
UA = "plmlist-hf-config/1.0 (+https://plmlist.com)"

ORG_HINTS = {
    "DeepSeek": ["deepseek-ai"],
    "Qwen": ["Qwen"],
    "Google": ["google"],
    "Meta": ["meta-llama", "facebook"],
    "Mistral": ["mistralai"],
    "Z.ai": ["zai-org", "THUDM"],
    "MiniMax": ["MiniMaxAI", "MiniMax"],
    "Moonshot": ["moonshotai"],
    "NVIDIA": ["nvidia"],
    "ByteDance": ["ByteDance-Seed", "ByteDance"],
    "Nous": ["NousResearch"],
    "Xiaomi": ["XiaomiMiMo", "mncai"],
    "OpenAI": ["openai"],
    "Microsoft": ["microsoft"],
    "Cohere": ["CohereForAI", "cohere"],
    "Baidu": ["baidu"],
    "IBM": ["ibm-granite", "ibm"],
    "Liquid AI": ["LiquidAI"],
    "Tencent": ["Tencent-Hunyuan", "Tencent"],
    "Allen AI": ["allenai"],
    "EleutherAI": ["EleutherAI"],
    "InclusionAI": ["InclusionAI"],
    "Nex-AGI": ["Nex-AGI", "nex-agi"],
    "Thinking Machines": ["thinking-machines-lab", "ThinkingMachines"],
    "Meituan": ["meituan-longcat", "Meituan"],
    "LG": ["LGAI-EXAONE", "lg-ai"],
    "Upstage": ["upstage"],
    "StepFun": ["stepfun-ai"],
    "RedNote": ["rednote-hilab"],
    "Alibaba": ["Qwen", "Alibaba-NLP"],
    "RWKV": ["BlinkDL"],
    "Yandex": ["yandex"],
    "BigScience": ["bigscience"],
    "THUDM": ["THUDM"],
    "Cerebras": ["cerebras"],
    "Databricks": ["databricks", "mosaicml"],
    "OpenAssistant": ["OpenAssistant"],
    "CambioML": ["CambioML"],
    "LWM": ["LargeWorldModel"],
    "Stability AI": ["stabilityai"],
    "LMSYS": ["lmsys"],
    "H2O.ai": ["h2oai"],
    "Together": ["togethercomputer"],
    "OpenLM": ["openlm-research"],
    "TII": ["tiiuae"],
    "Salesforce": ["Salesforce"],
    "Inception": ["inceptionai", "core42"],
    "Skywork": ["Skywork"],
    "Hugging Face": ["HuggingFaceH4"],
    "LLM360": ["LLM360"],
    "BSC": ["projecte-aina"],
    "xAI": ["xai-org", "xai"],
    "AI21": ["ai21labs"],
    "TRI": ["tri-ml"],
    "Apple": ["apple"],
    "Snowflake": ["Snowflake"],
    "Fujitsu": ["Fujitsu"],
    "01.AI": ["01-ai"],
    "YuLan": ["yulan-team"],
    "Atla": ["AtlaAI"],
    "BigCode": ["bigcode"],
    "Replit": ["replit"],
    "Deci": ["Deci"],
    "Swiss AI": ["swiss-ai"],
    "Sarvam": ["sarvamai"],
}

MANUAL = {
    "deepseek-deepseek-coder-6.7b-base": "deepseek-ai/deepseek-coder-6.7b-base",
    "deepseek-deepseek-llm-67b-base": "deepseek-ai/deepseek-llm-67b-base",
    "deepseek-deepseek-chat": "deepseek-ai/DeepSeek-V3",
    "deepseek-deepseek-chat-v3-0324": "deepseek-ai/DeepSeek-V3-0324",
    "deepseek-deepseek-chat-v3.1": "deepseek-ai/DeepSeek-V3.1",
    "deepseek-deepseek-v3.1-terminus": "deepseek-ai/DeepSeek-V3.1-Terminus",
    "deepseek-deepseek-v3.2": "deepseek-ai/DeepSeek-V3.2",
    "deepseek-deepseek-v3.2-exp": "deepseek-ai/DeepSeek-V3.2-Exp",
    "deepseek-r1": "deepseek-ai/DeepSeek-R1",
    "deepseek-deepseek-r1-0528": "deepseek-ai/DeepSeek-R1-0528",
    "deepseek-deepseek-ocr": "deepseek-ai/DeepSeek-OCR",
    "z-ai-glm-5.2": "zai-org/GLM-5.2",
    "z-ai-glm-4.7": "zai-org/GLM-4.7",
    "z-ai-glm-4.5": "zai-org/GLM-4.5",
    "google-gemma-4-31b-it": "google/gemma-4-31b-it",
    "google-gemma-4-26b-a4b-it": "google/gemma-4-26b-a4b-it",
    "qwen-qwen3.6-27b": "Qwen/Qwen3.6-27B",
    "qwen-qwen3.8-27b": "Qwen/Qwen3.8-27B",
    "qwen-qwen3.8-2.4t-a95b": "Qwen/Qwen3.8-2.4T-A95B",
    "qwen-qwen3.5-27b": "Qwen/Qwen3.5-27B",
    "moonshotai-kimi-k3": "moonshotai/Kimi-K3",
    "minimax-minimax-m2.5": "MiniMaxAI/MiniMax-M2.5",
    "google-t5-large": "google-t5/t5-large",
    "google-flan-t5-xxl": "google/flan-t5-xxl",
    "rwkv-rwkv-4": "BlinkDL/rwkv-4-world",
    "yandex-yalm-100b": "yandex/YaLM-100B",
    "bigscience-bloom": "bigscience/bloom",
    "thudm-chatglm-6b": "THUDM/chatglm-6b",
    "cerebras-cerebras-gpt-1.3b": "cerebras/Cerebras-GPT-1.3B",
    "eleutherai-pythia-12b": "EleutherAI/pythia-12b",
    "databricks-dolly-v2-12b": "databricks/dolly-v2-12b",
    "stabilityai-stablelm-base-alpha-7b": "stabilityai/stablelm-base-alpha-7b",
    "lmsys-fastchat-t5-3b": "lmsys/fastchat-t5-3b-v1.0",
    "h2oai-h2ogpt": "h2oai/h2ogpt-oasst1-512-12b",
    "mosaicml-mpt-7b": "mosaicml/mpt-7b",
    "together-redpajama-incite-7b": "togethercomputer/RedPajama-INCITE-7B-Base",
    "openlm-open-llama-7b": "openlm-research/open_llama_7b",
    "tii-falcon-40b": "tiiuae/falcon-40b",
    "mosaicml-mpt-30b": "mosaicml/mpt-30b",
    "meta-llama-2-7b": "meta-llama/Llama-2-7b-hf",
    "thudm-chatglm2-6b": "THUDM/chatglm2-6b",
    "salesforce-xgen-7b-8k": "Salesforce/xgen-7b-8k-base",
    "inception-jais-13b": "inceptionai/jais-13b",
    "nous-openhermes-7b": "teknium/OpenHermes-2.5-Mistral-7B",
    "mistralai-mistral-7b-v0.1": "mistralai/Mistral-7B-v0.1",
    "thudm-chatglm3-6b": "THUDM/chatglm3-6b",
    "skywork-skywork-13b": "Skywork/Skywork-13B-Base",
    "inception-jais-30b": "inceptionai/jais-30b-chat-v1",
    "huggingface-zephyr-7b": "HuggingFaceH4/zephyr-7b-beta",
    "deepseek-deepseek-llm-7b-base": "deepseek-ai/deepseek-llm-7b-base",
    "mistralai-mistral-7b-instruct-v0.2": "mistralai/Mistral-7B-Instruct-v0.2",
    "mistralai-mixtral-8x7b-v0.1": "mistralai/Mixtral-8x7B-v0.1",
    "llm360-amber": "LLM360/Amber",
    "upstage-solar-10.7b": "upstage/SOLAR-10.7B-v1.0",
    "microsoft-phi-2": "microsoft/phi-2",
    "bsc-flor-6.3b": "projecte-aina/FLOR-6.3B",
    "rwkv-rwkv-5": "BlinkDL/rwkv-5-world",
    "allenai-olmo-7b": "allenai/OLMo-7B",
    "qwen-qwen1.5-7b": "Qwen/Qwen1.5-7B",
    "lwm-lwm-text-chat-128k": "LargeWorldModel/LWM-Text-Chat-128K",
    "google-gemma-7b": "google/gemma-7b",
    "xai-grok-1": "xai-org/grok-1",
    "qwen-qwen1.5-moe-a2.7b": "Qwen/Qwen1.5-MoE-A2.7B",
    "ai21-jamba-v0.1": "ai21labs/Jamba-v0.1",
    "qwen-qwen1.5-32b": "Qwen/Qwen1.5-32B",
    "tri-mamba-7b": "tri-ml/mamba-7b-rw",
    "mistralai-mixtral-8x22b-v0.1": "mistralai/Mixtral-8x22B-v0.1",
    "microsoft-phi-3-mini": "microsoft/Phi-3-mini-4k-instruct",
    "apple-openelm-3b": "apple/OpenELM-3B",
    "snowflake-arctic": "Snowflake/snowflake-arctic-instruct",
    "qwen-qwen1.5-110b": "Qwen/Qwen1.5-110B",
    "rwkv-rwkv-6": "BlinkDL/rwkv-6-world",
    "deepseek-deepseek-v2": "deepseek-ai/DeepSeek-V2",
    "fujitsu-fugaku-llm-13b": "Fugaku-LLM/Fugaku-LLM-13B",
    "tii-falcon-2-11b": "tiiuae/falcon-11B",
    "01ai-yi-1.5-9b": "01-ai/Yi-1.5-9B",
    "deepseek-deepseek-v2-lite": "deepseek-ai/DeepSeek-V2-Lite",
    "microsoft-phi-3-medium": "microsoft/Phi-3-medium-4k-instruct",
    "yulan-yulan-mini": "yulan-team/YuLan-Mini",
    "yulan-yulan-base-12b": "yulan-team/YuLan-Base-12b",
    "yulan-yulan-chat-3-12b": "yulan-team/YuLan-Chat-3-12b",
    "atla-selene-mini": "AtlaAI/Selene-1-Mini-Llama-3.1-8B",
    "bigcode-santacoder": "bigcode/santacoder",
    "salesforce-codegen2-7b": "Salesforce/codegen2-7B",
    "bigcode-starcoder": "bigcode/starcoder",
    "huggingface-starchat-alpha": "HuggingFaceH4/starchat-alpha",
    "replit-replit-code-v1-3b": "replit/replit-code-v1-3b",
    "salesforce-codet5p-6b": "Salesforce/codet5p-6b",
    "salesforce-codegen25-7b": "Salesforce/codegen25-7b-multi",
    "deci-decicoder-1b": "Deci/DeciCoder-1b",
    "meta-codellama-7b": "meta-llama/CodeLlama-7b-hf",
    "openassistant-pythia-12b": "OpenAssistant/oasst-sft-4-pythia-12b-epoch-3.5",
    "cambiaml-dlite-v2-1.5b": "CambioML/dlite-v2-1.5b",
    "swiss-ai-apertus": "swiss-ai/Apertus-70B-2509",
    "google-bert": "google-bert/bert-base-uncased",
    "openai-gpt-1": "openai-community/openai-gpt",
    "eleutherai-gpt-neo-2.7b": "EleutherAI/gpt-neo-2.7B",
    "sarvam-sarvam-m": "sarvamai/sarvam-m",
    "sarvam-sarvam-30b": "sarvamai/sarvam-30b",
    "sarvam-sarvam-105b": "sarvamai/sarvam-105b",
    "huggingface-smolm": "HuggingFaceTB/SmolLM-1.7B",
    "google-xlnet": "xlnet/xlnet-large-cased",
}

SKIP_REPO = (
    "thebloke",
    "bartowski",
    "gguf",
    "awq",
    "gptq",
    "exl2",
    "iqquant",
    "unsloth",
    "-bnb-",
)

HISTORICAL = [
    {
        "id": "deepseek-deepseek-coder-6.7b-base",
        "name": "DeepSeek-Coder 6.7B",
        "provider": "DeepSeek",
    },
    {
        "id": "deepseek-deepseek-llm-67b-base",
        "name": "DeepSeek LLM 67B",
        "provider": "DeepSeek",
    },
]


def curl_json(url: str, timeout: int = 40) -> object | None:
    proc = subprocess.run(
        ["curl", "-fsSL", "-A", UA, "--max-time", str(timeout), url],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0 or not proc.stdout:
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None


def compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def core_cfg(cfg: dict) -> dict:
    text = cfg.get("text_config")
    if isinstance(text, dict):
        merged = dict(cfg)
        merged.update(text)
        return merged
    return cfg


def num(*vals):
    for v in vals:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return int(v) if float(v).is_integer() else v
    return None


def fmt(n) -> str:
    if n is None:
        return "—"
    if isinstance(n, int) and abs(n) >= 1000:
        return f"{n:,}"
    return str(n)


def attention_kind(heads, kv) -> str | None:
    if heads is None or kv is None:
        return None
    if kv == heads:
        return "multi-head attention (MHA): every query head keeps its own key/value."
    if kv == 1:
        return "multi-query attention (MQA): every query head shares a single key/value."
    return (
        f"grouped-query attention (GQA): {heads} query heads share {kv} key/value groups, "
        f"so the KV cache is about {heads / kv:.0f}× smaller than full MHA."
    )


def ratio_sentence(hidden, heads, head_dim) -> str:
    if hidden and heads:
        d = head_dim or (hidden // heads if heads else None)
        if not d:
            return ""
        n16 = d % 16 == 0
        n32 = d % 32 == 0
        p2 = (d & (d - 1)) == 0
        bits = []
        if n32:
            bits.append("a multiple of 32 (NVIDIA warp-friendly)")
        if n16:
            bits.append("a multiple of 16 (Huawei cube-friendly)")
        if p2:
            bits.append("a power of two (Triton / FlashAttention-friendly)")
        joined = ", and ".join(bits) if bits else "not an obvious 16/32 tiling"
        return (
            f"The ratio test is hidden_size / num_attention_heads = {hidden} / {heads} = {d}. "
            f"{d} is {joined}. From this number alone you cannot name the training chip."
        )
    return ""


def describe(name: str, cfg: dict, hf_url: str | None) -> str:
    c = core_cfg(cfg)
    arch = (c.get("architectures") or [c.get("model_type") or "unknown"])[0]
    hidden = num(c.get("hidden_size"), c.get("n_embd"), c.get("d_model"))
    heads = num(c.get("num_attention_heads"), c.get("n_head"), c.get("num_heads"))
    kv = num(c.get("num_key_value_heads"), c.get("n_kv_heads"), c.get("num_kv_heads"))
    layers = num(c.get("num_hidden_layers"), c.get("n_layer"), c.get("num_layers"))
    inter = num(c.get("intermediate_size"), c.get("n_inner"), c.get("ffn_dim"))
    vocab = num(c.get("vocab_size"))
    ctx = num(c.get("max_position_embeddings"), c.get("max_seq_len"), c.get("seq_length"))
    head_dim = num(c.get("head_dim"), c.get("qk_nope_head_dim"))
    if head_dim is None and hidden and heads:
        head_dim = hidden // heads
    rope_theta = c.get("rope_theta") or c.get("rope_ththeta")
    rope = c.get("rope_scaling")
    dtype = c.get("torch_dtype") or c.get("dtype")
    act = c.get("hidden_act") or c.get("hidden_activation")
    tie = c.get("tie_word_embeddings")
    experts = num(
        c.get("n_routed_experts"),
        c.get("num_experts"),
        c.get("n_experts"),
        c.get("moe_num_experts"),
    )
    topk = num(c.get("num_experts_per_tok"), c.get("moe_top_k"), c.get("num_experts_per_token"))

    paras = []
    paras.append(
        f"Here is how to read the {name} config.json. The architecture class is {arch}, "
        f"which is the transformers (or equivalent) module that wires embeddings, attention, "
        f"the MLP, and the language-modelling head that turns hidden states into next-token logits."
    )
    if hidden:
        extra = ""
        if vocab:
            extra = (
                f" The embedding matrix is therefore {fmt(vocab)} × {fmt(hidden)}: "
                "each token id owns a vector of that width."
            )
        paras.append(
            f"hidden_size is {fmt(hidden)}: that is the width of every residual stream vector.{extra}"
        )
    if heads and hidden:
        paras.append(
            f"num_attention_heads is {heads}, so each head sees {fmt(head_dim)} dimensions "
            f"({fmt(hidden)} / {heads}). "
            + ratio_sentence(hidden, heads, head_dim)
        )
    att = attention_kind(heads, kv)
    if att and kv is not None:
        paras.append(f"num_key_value_heads is {kv}, so this is {att}")
    if layers:
        paras.append(
            f"num_hidden_layers is {layers}: the stack is that many transformer blocks deep."
        )
    if inter and hidden:
        paras.append(
            f"intermediate_size is {fmt(inter)}. In a SwiGLU MLP this is the high-dimensional "
            f"workspace: the {fmt(hidden)}-wide stream is projected up, activated"
            f"{(' with ' + act) if act else ''}, then projected back. "
            "Labs usually round this width to a multiple of 128 or 256 so it tiles on the chip."
        )
    if ctx:
        rope_txt = ""
        if isinstance(rope, dict):
            factor = rope.get("factor") or rope.get("scaling_factor")
            rtype = rope.get("type") or rope.get("rope_type")
            if factor:
                rope_txt = (
                    f" rope_scaling is type {rtype} with factor {factor}, which stretches "
                    "the rotary positions so the advertised window can be larger than the "
                    "span the model originally trained on."
                )
            else:
                rope_txt = f" rope_scaling is present ({json.dumps(rope)[:180]})."
        elif rope in (None, "null"):
            rope_txt = " There is no rope_scaling entry, so the rotary positions are used as-is."
        theta = ""
        if rope_theta is not None:
            theta = (
                f" rope_theta is {rope_theta}: that is the wavelength of the rotary embedding. "
                "A larger theta keeps distant tokens from aliasing after a full rotation."
            )
        paras.append(
            f"max_position_embeddings is {fmt(ctx)} tokens — the context window in the config.{rope_txt}{theta}"
        )
    if vocab:
        tile = ""
        if vocab % 256 == 0:
            tile = f" {fmt(vocab)} is divisible by 256, the usual vocab-tiling grain."
        elif vocab % 128 == 0:
            tile = f" {fmt(vocab)} is divisible by 128."
        paras.append(
            f"vocab_size is {fmt(vocab)}.{tile} bos/eos ids, when present, are just two special "
            "rows in that table; the padded vocab is often larger than the tokenizer’s real inventory."
        )
    if experts:
        extra = f" with top-k {topk}" if topk else ""
        paras.append(
            f"This is a mixture of experts: {fmt(experts)} routed experts{extra}. "
            "The 1991 Jacobs / Jordan / Nowlan / Hinton paper “Adaptive Mixtures of Local Experts” "
            "is the ancestor of this router-plus-specialists idea."
        )
    if tie is False:
        paras.append(
            "tie_word_embeddings is false, so the input embedding matrix and the output LM head "
            "are separate learned matrices rather than a shared transpose."
        )
    elif tie is True:
        paras.append(
            "tie_word_embeddings is true: the same matrix is reused for input embeddings and the LM head."
        )
    if dtype:
        d = str(dtype).lower()
        if "bfloat16" in d or d == "bf16":
            paras.append(
                "torch_dtype is bfloat16. Brain floating point keeps FP32’s exponent range with less "
                "mantissa, which avoids the overflow/underflow of a tiny exponent at the cost of "
                "noisier decimals — and it halves the on-chip footprint versus FP32. NVIDIA A100s "
                "were the first NVIDIA chips with native BF16; Huawei Ascend 910-class parts also "
                "prefer BF16/FP16 on the cube."
            )
        else:
            paras.append(f"torch_dtype is {dtype}.")
    if hf_url:
        paras.append(f"The copy of config.json is from {hf_url}.")
    return "\n\n".join(paras)


def search_hf(query: str) -> list[str]:
    url = "https://huggingface.co/api/models?search=" + urllib.parse.quote(query) + "&limit=12"
    data = curl_json(url)
    if not isinstance(data, list):
        return []
    ids = []
    for row in data:
        mid = row.get("modelId") or row.get("id")
        if mid:
            ids.append(mid)
    return ids


def guess_repos(provider: str, name: str) -> list[str]:
    cleaned = re.sub(r"^[^:]+:\s*", "", name).strip()
    slug = cleaned.replace(" ", "-")
    alts = {
        slug,
        slug.replace(".", "-"),
        cleaned.replace(" ", ""),
        name.replace(" ", "-"),
    }
    out = []
    for org in ORG_HINTS.get(provider, []):
        for a in alts:
            if a:
                out.append(f"{org}/{a}")
    return out


def pick_repo(provider: str, name: str, model_id: str) -> str | None:
    if model_id in MANUAL:
        return MANUAL[model_id]
    for guess in guess_repos(provider, name):
        if fetch_config(guess):
            return guess
    hints = ORG_HINTS.get(provider, [])
    seen: list[str] = []
    for hid in search_hf(name) + search_hf(re.sub(r"^[^:]+:\s*", "", name)):
        if hid not in seen:
            seen.append(hid)
    time.sleep(0.08)
    qcompact = compact(name)
    scored = []
    for hid in seen:
        low = hid.lower()
        if any(s in low for s in SKIP_REPO):
            continue
        org, _, rest = hid.partition("/")
        score = 0.0
        if any(h.lower() == org.lower() for h in hints):
            score += 3
        rc = compact(rest)
        if qcompact and (qcompact in rc or rc in qcompact):
            score += 2
        scored.append((score, hid))
    scored.sort(reverse=True)
    if scored and scored[0][0] >= 2:
        return scored[0][1]
    return None


_CFG_CACHE: dict[str, dict | None] = {}


def fetch_config(repo: str) -> dict | None:
    if repo in _CFG_CACHE:
        return _CFG_CACHE[repo]
    for rev in ("main", "master"):
        url = f"https://huggingface.co/{repo}/resolve/{rev}/config.json"
        data = curl_json(url, timeout=50)
        if isinstance(data, dict) and data:
            _CFG_CACHE[repo] = data
            return data
    _CFG_CACHE[repo] = None
    return None


def handwritten(model_id: str) -> str | None:
    if model_id == "deepseek-deepseek-coder-6.7b-base":
        return (
            "The first open source model to come out of DeepSeek was DeepSeek-Coder. They mention in the paper that "
            "“Our experiments utilize clusters outfitted with NVIDIA A100 and H800 GPUs.”\n\n"
            "First, let us dissect what all of this means. To start, the LlamaForCausalLM class comes from the transformers "
            "library that puts together the logic behind the llama model. It is the heart of the llama architecture that handles "
            "the embeddings, attention mechanisms, the hidden states, and the language modelling head that returns the predicted "
            "tokens. The bos_token_id and the eos_token_id relate to the vocab size. In the model’s tokenizer.json there are 32021 "
            "token ids, and those attributes are just the ids of the bos (beginning of sequence) and eos (end of sequence) tokens. "
            "So then why is the vocab_size 32256? Due to tiling and to keep it divisible by 256. To contrast, the original Llama 2-7b "
            "base model of DeepSeek coder had a vocab size of 32000. Next, the hidden_size is the dimension of the vectors that each "
            "token is embedded into. So the embedding matrix has a size of 32256 × 4096, the vocab size paired with the hidden size. "
            "To put it plainly each id of the vocab gets its own vector. The intermediate_size is the step that projects the 4096 "
            "dimension vectors to 11008 dimensions to execute the SwiGLU activation function. It acts as a high dimensional workspace "
            "where stored weights are compared to other tokens to extract richer contextual patterns before being reduced back to 4096 "
            "dimensions. Next, the num_attention_heads is important because it cuts up the 4096 dimension vectors into 32 separate heads, "
            "each working with 128 dimensions. 128 is both divisible by 16 and by 32 and can be converted to a base 2 number, so from this "
            "information alone you cannot conclude exactly which hardware was used to train it. num_key_value_heads is also 32, meaning "
            "each head gets its own key value. This means the model uses multi-head attention (MHA) instead of grouped query attention (GQA) "
            "or multi-query attention (MQA). The max_position_embeddings is also related to the rope_scaling. The max_position_embeddings is "
            "the context window of the model. However, during training, the original Llama 2 model only ever saw input text that was at most "
            "4096 tokens long, so the question is how did DeepSeek manage to get the model to understand beyond this 4096 space? DeepSeek found "
            "that you can increase the context window by just scaling down an inflated context window. Real position just gets compressed back "
            "into 4096 positions. That is why rope_scaling is being scaled by a factor of 4.0. The larger context window is also the reason why "
            "rope_theta was increased from the original 10k in Llama 2 to 100k. RoPE dictates how much each token is rotated. A full rotation would "
            "happen in Llama 2’s case after 10k tokens. If a token becomes fully rotated, it would look identical to the start token, meaning the "
            "model loses its ability to distinguish how far tokens are from each other.\n\n"
            "tie_word_embeddings: false means the input embedding matrix and the output language model head are separate learned matrices. "
            "pretraining_tp: 1 is a default setting regarding tensor-parallelism used during pretraining. A value of 1 means no tensor-parallel "
            "sharding was applied. Lastly, bfloat16 (brain floating point) was developed at Google Brain in 2019 to keep the same exponent range "
            "as floating point 32 with less precision. For deep learning, not having the exponent range leads to underflows and overflows that "
            "produce infinities or zeros, which produce more issues than imprecise decimals. This saves on-chip memory. A100s were the first chips "
            "from NVIDIA that natively supported bfloat16, which aligns with what DeepSeek published: that A100s were used for training."
        )
    if model_id == "deepseek-deepseek-llm-67b-base":
        return (
            "DeepSeek’s LLM came in both 7B and 67B variants. First, let us perform the ratio test: total hidden_size is 8192 and "
            "num_attention_heads is 64. Divide both and we get again 128. While this is not conclusive as to which chip was used for training, "
            "we know NVIDIA chips were used from the repo’s README, which says “for DeepSeek LLM 7B, we utilize 1 NVIDIA A100-PCIE-40GB GPU for "
            "inference,” and the 67B used 8. Notice hidden_size increased to 8192. The context window was left at 4096, meaning there is no "
            "rope_scaling needed. num_key_value_heads decreasing down to 8 means the model uses grouped-query attention (GQA) instead of MHA. "
            "Storing a full KV pair per attention head for each token becomes huge; by reducing the stored KV sets from 64 to 8, you shrink the "
            "cache by 8×, making the model much faster to run.\n\n"
            "The formula used to come up with intermediate_size is 8/3 × hidden_size, then scaled up to a hardware-friendly number. "
            "8192 × 8/3 = 21,845.33, then rounded up to the nearest multiple of 128 would be 21888 (128 × 171), but 22016 was chosen instead "
            "(128 × 172). That rounding goes back to Llama 2’s FFN class, where SwiGLU hidden size is forced to a multiple of 256.\n\n"
            "Vocab size increased from 32256 to 102400. DeepSeek used a custom-trained tokenizer: “we set the number of conventional tokens in "
            "the vocabulary at 100000… we augmented the final vocabulary with 15 special tokens, bringing the total size to 100015… we configured "
            "the model’s vocabulary size to 102400 for training.” 102400 is 256 × 400. With 8 A100s used to inference the 67B, 102400 / 8 = 12800, "
            "and 12800 / 256 = 50, so the vocab still tiles after being split across the eight GPUs."
        )
    return None


def insert_historical(catalog: dict) -> None:
    for group in catalog.get("providers") or []:
        if group.get("name") != "DeepSeek":
            continue
        have = {m["id"] for m in group["models"]}
        extra = [h for h in HISTORICAL if h["id"] not in have]
        if extra:
            group["models"] = [{"id": h["id"], "name": h["name"]} for h in extra] + group["models"]
        break
    catalog["count"] = sum(len(p["models"]) for p in catalog.get("providers") or [])


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--missing-only",
        action="store_true",
        help="skip models that already have a model-pages JSON",
    )
    args = ap.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    insert_historical(catalog)
    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    PAGES.mkdir(parents=True, exist_ok=True)

    jobs = []
    for group in catalog["providers"]:
        for m in group["models"]:
            jobs.append((group["name"], m))
    if args.missing_only:
        jobs = [(p, m) for p, m in jobs if not (PAGES / f"{m['id']}.json").exists()]

    ok = 0
    miss = 0
    for i, (provider, m) in enumerate(jobs, 1):
        mid = m["id"]
        out = PAGES / f"{mid}.json"
        print(f"[{i}/{len(jobs)}] {m['name']}")
        repo = pick_repo(provider, m["name"], mid)
        cfg = fetch_config(repo) if repo else None
        hf_url = f"https://huggingface.co/{repo}/blob/main/config.json" if repo else None
        note = handwritten(mid)
        if cfg and not note:
            note = describe(m["name"], cfg, hf_url)
        if not cfg:
            miss += 1
            note = note or (
                f"No public Hugging Face config.json was found for {m['name']}. "
                "Some directory entries are API names, distilled checkpoints, or repos without a root config."
            )
        else:
            ok += 1
        payload = {
            "id": mid,
            "name": m["name"],
            "provider": provider,
            "hf_repo": repo,
            "hf_url": hf_url,
            "config": cfg,
            "description": note,
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        time.sleep(0.08)

    print(f"Wrote {ok} configs, {miss} missing, {len(jobs)} pages → {PAGES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
