import {
  BarChart,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  LineChart,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

const HW_DATA = {
  "months": [
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07"
  ],
  "monthLabels": [
    "07/25",
    "08/25",
    "09/25",
    "10/25",
    "11/25",
    "12/25",
    "01/26",
    "02/26",
    "03/26",
    "04/26",
    "05/26",
    "06/26",
    "07/26"
  ],
  "slugs": [
    "rtx-5090",
    "rtx-3090",
    "rtx-5060-ti",
    "rtx-4090",
    "rtx-5060",
    "rtx-6000-ada",
    "rtx-pro-6000-blackwell",
    "m5",
    "strix-halo",
    "dgx-spark",
    "macbook",
    "rtx-3060",
    "m4",
    "gb10"
  ],
  "slugTotals": [
    778,
    756,
    471,
    287,
    280,
    236,
    234,
    197,
    145,
    139,
    137,
    136,
    124,
    122
  ],
  "matrix": [
    [
      0,
      3,
      19,
      7,
      14,
      20,
      39,
      30,
      103,
      152,
      158,
      148,
      85
    ],
    [
      0,
      14,
      16,
      23,
      14,
      20,
      35,
      36,
      70,
      214,
      131,
      130,
      53
    ],
    [
      0,
      1,
      2,
      6,
      1,
      4,
      8,
      11,
      53,
      101,
      52,
      118,
      114
    ],
    [
      0,
      25,
      5,
      3,
      11,
      6,
      5,
      26,
      52,
      73,
      31,
      28,
      22
    ],
    [
      0,
      1,
      1,
      3,
      1,
      5,
      8,
      9,
      28,
      26,
      12,
      93,
      93
    ],
    [
      0,
      2,
      3,
      14,
      4,
      3,
      24,
      18,
      32,
      66,
      30,
      28,
      12
    ],
    [
      0,
      1,
      3,
      3,
      3,
      5,
      26,
      28,
      45,
      43,
      33,
      23,
      21
    ],
    [
      0,
      0,
      4,
      3,
      4,
      0,
      0,
      7,
      51,
      49,
      38,
      35,
      6
    ],
    [
      0,
      1,
      1,
      5,
      12,
      7,
      18,
      10,
      23,
      26,
      26,
      13,
      3
    ],
    [
      0,
      0,
      0,
      3,
      5,
      4,
      5,
      7,
      15,
      50,
      19,
      21,
      10
    ],
    [
      0,
      4,
      5,
      0,
      8,
      4,
      6,
      4,
      25,
      29,
      21,
      15,
      16
    ],
    [
      0,
      2,
      4,
      3,
      0,
      1,
      5,
      5,
      16,
      41,
      33,
      15,
      11
    ],
    [
      0,
      0,
      2,
      4,
      9,
      3,
      1,
      2,
      16,
      27,
      24,
      22,
      14
    ],
    [
      0,
      0,
      1,
      0,
      1,
      15,
      2,
      1,
      29,
      9,
      37,
      20,
      7
    ]
  ],
  "meta": {
    "messages": 16028,
    "mapped": 9821,
    "slugs_total": 72
  }
} as const;

const SPEED_DATA = {
  "months": [
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07"
  ],
  "monthLabels": [
    "08/25",
    "09/25",
    "10/25",
    "11/25",
    "12/25",
    "01/26",
    "02/26",
    "03/26",
    "04/26",
    "05/26",
    "06/26",
    "07/26"
  ],
  "tpsMedian": [
    47.0,
    14.0,
    42.0,
    14.0,
    20.0,
    30.0,
    50.0,
    40.0,
    35.0,
    50.0,
    50.0,
    35.0
  ],
  "tpsCount": [
    47,
    105,
    118,
    39,
    64,
    140,
    473,
    1349,
    2062,
    1050,
    833,
    371
  ],
  "ttftMedianMs": [
    200.0,
    0,
    30.09,
    0,
    0,
    250.0,
    794.0,
    50000.0,
    40018.0,
    0,
    4226.91,
    1743.13
  ],
  "ttftCount": [
    2,
    0,
    2,
    0,
    0,
    2,
    7,
    5,
    10,
    0,
    3,
    11
  ],
  "meta": {
    "messages": 3140,
    "with_metrics": 1359,
    "tps_values": 6651,
    "ttft_values": 42,
    "overall_tps_median": 40.0
  }
} as const;

const SETUP_DATA = {
  "count": 886,
  "by_tier": {
    "full": 179,
    "hw_speed": 269,
    "hw_speed_model": 206,
    "hw_speed_benchmark": 192,
    "inferred_model": 24,
    "inferred": 16
  },
  "setups": [
    {
      "month": "2026-07",
      "tier": "full",
      "model": "glm-5.2",
      "hardware": "4x dgx sparks",
      "quantization": "INT4 and FP8 kv cache",
      "speed": "20 tokens a second \u00b7 20 tok/s",
      "message": "per that caculator 4x dgx sparks is 20 tokens a second with GLM5.2 with INT4 and FP8 kv cache?\n\nDoes that sound right?"
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.6-35b-a3b",
      "hardware": "2x RTX Pro 6000 Max-Q (96GB), 8x RTX 3090 (24GB), 2x RTX 5090 (32GB), 128GB DDR5 RAM, Threadripper 9960x",
      "quantization": "8bit quant",
      "speed": "tps of 400-500 \u00b7 400 tok/s",
      "message": "Not a very useful metric because it depends on context, prefill dominates in some circumstances, etc... but I think I got an aggregate tps of 400-500 at one point with the 8bit quant of qwen 3.6 35b a3b."
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "glm-5.2",
      "hardware": "4x Dgx sparks",
      "quantization": "NVFP4",
      "speed": "20 tokens a second \u00b7 20 tok/s, 20 tok/s",
      "message": "Anything faster than 20 tokens a second would be worth it.\n\nI saw someone getting 20 tokens a second with NVFP4 with glm5.2 with 4x Dgx sparks. But that\u2019s 16k instead of 10k"
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.5-27b",
      "hardware": "two 5060 ti's",
      "quantization": "q8",
      "speed": "14tk/s \u00b7 14 tok/s, 14 tok/s, 14 tok/s",
      "message": "Qwen 27b dense will run at like 14tk/s with two 5060 ti's on q8 (best case scenario)"
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "4x 5060 ti",
      "quantization": "INT8-Autoround",
      "speed": "Output token throughput (tok/s): 274.26 \u00b7 5354.11ms TTFT, 1961.24ms TTFT",
      "message": "did a benchmark at 8 concurrency with INT8-Autoround with unquantized KV cache of Qwen3.6-27B.\n\nWith the 4x 5060 ti's.\n\n ============ Serving Benchmark Result ============\nSuccessful requests: 150 \nFailed requests: 0 \nMaximum request concurrency: 8 \nBenchmark duration (s): 2240.18 \nTotal input tokens: 3307200 \nTotal generated tokens: 614400 \nRequest throughput (req/s): 0.07 \nOutput token throughput (tok/s): 274.26 \nPeak output token throughput (tok/s): 104.00 \nPeak concurrent requests: 10.00 \nTotal token throughput (tok/s): 1750.57 \n---------------Time to First Token----------------\nMean TTFT (ms): 5354.11 \nMedian TTFT (ms): 1961.24 \nP90 TTFT (ms): 18384.43 \nP95 TTFT (ms): 27653.41 \nP99 TTFT (ms): 47726.86 \n-----Time per Output Token (excl. 1st token)------\nMean TPOT (ms): 27.37 \nMedian TPOT (ms): 26.59 \nP90 TPOT (ms): 32.38 \nP95 TPOT (ms): 33.65 \nP99 TPOT (ms): 42.01 \n---------------Inter-token Latency----------------\nMean ITL (ms): 93.72 \nMedian ITL (ms): 80.81 \nP90 ITL (ms): 82.84 \nP95 ITL (ms): 83.98 \nP99 ITL (ms): 706.95 \n----------------End-to-end Latency----------------\nMean E2EL (ms): 117432.48 \nMedian E2EL (ms): 112275.04 \nP90 E2EL (ms): 138500.87 \nP95 E2EL (ms): 165912.41 \nP99 E2EL (ms): 192595.94 \n---------------Speculative Decoding---------------\nAcceptance rate (%): 80.74 \nAcceptance length: 3.42 \nDrafts: 180831 \nDraft tokens: 542493 \nAccepted tokens: 438027 \nPer-position acceptance (%):\n Position 0: 90.73 \n Position 1: 80.14 \n Position 2: 71.36 \n=================================================="
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "around 29gb for the model itself",
      "quantization": "Q6_K",
      "speed": "2800t/s \u00b7 2800 tok/s, 1200 tok/s, 80 tok/s, 2800 tok/s",
      "message": "[Qwen3.6 27B MTP Q6]\nmodel = C:\\Users\\maxkr\\.lmstudio\\models\\unsloth\\Qwen3.6-27B-MTP-GGUF\\Qwen3.6-27B-Q6_K.gguf\nctx-size = 131072\nspec-type = draft-mtp\nspec-draft-n-max = 3\n\ntemperature = 0.6\ntop-p = 0.95\ntop-k = 20\nmin-p = 0.0\npresence-penalty = 0.0\nrepeat-penalty = 1.0\n\nfitt = 2048\nctk = q8_0\nctv = q8_0\n\nreasoning = on\nreasoning-budget = 16384\nchat-template-kwargs = {\"preserve_thinking\": true} \n\nThis config (parallel = 1 as well, but thats further up in the config), for agentic coding it starts around 2800t/s PP, drops to ~1200t/s around 100k. Token Gen is around 80t/s for chatting where MTP does functionally nothing, up to 130-140 where it does basically everything. averages around 110-115 for toolcalls of writing code\n\n/edit: this also uses around 29gb for the model itself, with windows overhead etc. that means i have ~1gb free, which is enough for videos + chrome etc, and veeeeeeeeery light games."
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "minimax-m2.7",
      "hardware": "20G ram and 4G vram",
      "quantization": "Q4",
      "speed": "2-5 tok per sec",
      "message": "I was able to run minimax 2.7 Q4\nHeavily NVMe mmap\n\n20G ram and 4G vram\n\nGot 2-5 tok per sec\n\nLooks perfect to me\nAnother big llm in my pockets"
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "5090",
      "quantization": "q6",
      "speed": "120t/s \u00b7 120 tok/s, 120 tok/s, 120 tok/s",
      "message": "steal a 5090 and use qwen3.6 27b q6 +MTP at 120t/s"
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "Deepseek flash",
      "hardware": "Xeon 2696 v2, 160GB ECC DDR3 RAM, p100 16GB, 3060 12GB, 3050 6GB",
      "quantization": "Q4",
      "speed": "4 t/s \u00b7 4 tok/s, 4 tok/s",
      "message": "Yo. I got a dual Xeon 2696 v2, 160GB ECC DDR3 RAM. 3 GPUs (p100 16GB, 3060 12GB, 3050 6GB no power connector). Dual PSU, one connects p100 and 3060, other one for CPUs and motherboard. I'm able to load Deepseek flash Q4 and get 4 t/s. But for some reason my computer crashes randomly. Can anyone help?"
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.5-35b",
      "hardware": "cuda 13.3",
      "quantization": "Q5 K M to Q6 XL",
      "speed": "10-12 t/ks faster",
      "message": "What a good day I upgrade from Q 5 K M to Q6 XL on the new unsloth MTP model for qwen 35b with cuda 13.3 and the newest turboquant and i average about 10-12 t/ks faster and saved 4.3 vram."
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "4x 5060 ti's",
      "quantization": "INT8",
      "speed": "Input token throughput (tok/s): 177.35 \u00b7 200 tok/s \u00b7 7504.07ms TTFT, 7382.56ms TTFT",
      "message": "Interesting, I tried using SG lang for Minachist/Qwen3.6-27B-INT8-Autoround with :\n\n8 concurrency\n\nTP=4\n\nMTP\n\n16K batch tokens\n\n200K context\n\nBfloat16 KV Cache\n\n4x 5060 ti's (4 lanes of gen 4 per card - bifurcation (8Gb/s bandwidth) per card\n\nAnd TTFT (prefill + token gen) was much lower than with VLLM at 8 concurrency.\n\nFrom memory prefill/ttft was horrible at 8 concurrency with VLLM at 15+ seconds.\n\nsglang seems to be showing better benchmarks overall\n\n```\n\n============ Serving Benchmark Result ============\nBackend: sglang-oai\nTraffic request rate: inf \nMax request concurrency: 8 \nSuccessful requests: 200 \nBenchmark duration (s): 348.87 \nTotal input tokens: 61870 \nTotal input text tokens: 61870 \nTotal generated tokens: 44525 \nTotal generated tokens (retokenized): 44476 \nRequest throughput (req/s): 0.57 \nInput token throughput (tok/s): 177.35 \nOutput token throughput (tok/s): 127.63 \nPeak output token throughput (tok/s): 76.00 \nPeak concurrent requests: 11 \nTotal token throughput (tok/s): 304.97 \nConcurrency: 7.84 \nAccept length: 2.50 \n----------------End-to-End Latency----------------\nMean E2E Latency (ms): 13679.23 \nMedian E2E Latency (ms): 12234.78 \nP90 E2E Latency (ms): 23320.88 \nP95 E2E Latency (ms): 28160.07 \nP99 E2E Latency (ms): 34531.84 \n---------------Time to First Token----------------\nMean TTFT (ms): 7504.07 \nMedian TTFT (ms): 7382.56 \nP90 TTFT (ms): 11857.75 \nP95 TTFT (ms): 12946.72 \nP99 TTFT (ms): 16279.74 \n-----Time per Output Token (excl. 1st token)------\nMean TPOT (ms): 31.24 \nMedian TPOT (ms): 26.88 \nP90 TPOT (ms): 40.12 \nP95 TPOT (ms): 51.57 \nP99 TPOT (ms): 133.01 \n---------------Inter-Token Latency----------------\nMean ITL (ms): 27.90 \nMedian ITL (ms): 18.30 \nP90 ITL (ms): 31.83 \nP95 ITL (ms): 54.90 \nP99 ITL (ms): 196.80 \nMax ITL (ms): 3217.83 \n==================================================\n```"
    },
    {
      "month": "2026-07",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "RTX Quadro 4000, AMD BC-250, GbE",
      "quantization": "Q4_K_M, q8_0",
      "speed": "~100t/s pp, ~20t/s generation \u00b7 100 tok/s, 20 tok/s, 100 tok/s, 20 tok/s",
      "message": "Got qwen3.6 27b on a kind of fairly weird/sketchy setup; RTX Quadro 4000 + 1x AMD BC-250 (40CU, 1.8Ghz) connected via GbE haha xP\n\nSurprisingly seems to mostly work xD\nWith llama.cpp RPC (cuda backend on the RTX, vulkan on the BC-250)\n\n...though performance isn't really great (still, better than running on CPU ig).\nI get about ~100t/s pp and ~20t/s generation with this:\n llama-server --backend-sampling --n-gpu-layers -1 --rpc 192.168.100.10:50052 --jinja --cache-ram 32768 -fa on --model /opt/models/bottlecapai/ThinkingCap-Qwen3.6-27B-GGUF/ThinkingCap-Qwen3.6-27B-Q4_K_M.gguf --cache-type-k q8_0 --cache-type-v q8_0 --ctx-size 65536 --temp 1.0 --top-p 0.95 --top-k 64 -b 4096 -ub 1024 --spec-type draft-mtp --spec-draft-n-max 2 \n\nnot sure if you have more ideas/things worth trying haha.\nI have another BC-250 I can connect, but I suspect it won't help with tok/s (since this is pipeline parallelism)"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "27b dense",
      "hardware": "partial offload",
      "quantization": "",
      "speed": "",
      "message": "in my experience any partial offload on 27b dense will crater tps"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "LTX2.3 22b",
      "hardware": "mac mini m4",
      "quantization": "",
      "speed": "32min for 8s video",
      "message": "Im using LTX2.3 22b distilled on my mac mini m4, with default settings, 8 seconds of video takes me around 32min"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "minimax-m2.7",
      "hardware": "256gb 2133mhz DDR4 + 5090 x16 PCIe gen3",
      "quantization": "q6-k",
      "speed": "6tps \u00b7 6 tok/s",
      "message": "I'm going to try an experiment: minimax-m2.7 q6 on a 256gb 2133mhz ddr4 + 5090 x16 pcie gen3. I wonder if it will load and what partial offload tg vs pure cpu tg, it going to take 10 hours to dl the gguf. I'm going to guess 6tps"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b",
      "hardware": "gpu",
      "quantization": "",
      "speed": "40-60 tokens per sec (with gpu) to 25-30 tokens per sec (CPU only) \u00b7 60 tok/s, 30 tok/s",
      "message": "i used the same model (qwen 3.6 35B), so not quite what you said, but performance is down from 40-60 tokens per sec (with gpu) to 25-30 tokens per sec (CPU only)"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "glm-5.2",
      "hardware": "4x 3090s",
      "quantization": "",
      "speed": "9.4tps \u00b7 9.4 tok/s",
      "message": "guess this glm5.2 setup is going to be in testing all night, decent performance so far for ~190GB DDR4 2133 and 4x 3090s though (9.4tps / 131k context)"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b",
      "hardware": "2.2\u202fgb",
      "quantization": "",
      "speed": "50 t/s, 3 sec per image \u00b7 50 tok/s, 50 tok/s",
      "message": "When the two are loaded Qwen3.6 35b takes about 50 t/s and sd1.5 about 3 sec per image. Sd spikes at 2.2 gb"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "5070 Ti 16GB",
      "quantization": "",
      "speed": "20 tok/s for 27B \u00b7 20 tok/s",
      "message": "my 5070 Ti 16GB is foaming at this, 20 tok/s for 27B https://www.reddit.com/r/LocalLLaMA/comments/1txpqru/maybe_kv_cache_offload_to_ram_isnt_bad/"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "5070 Ti",
      "quantization": "",
      "speed": "8 tok/s \u00b7 8 tok/s",
      "message": "I think last time I ran 27B I got 8 tok/s in LM Studio, same 5070 Ti"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "8B",
      "hardware": "3900x",
      "quantization": "bf16-full",
      "speed": "100k gflops, 5000 token prefill",
      "message": "chatgpt reckons the ballpark GFLOPS for 5000 token prefill on an 8B model is 100k gflops. my 3900x can do theoretically do 1.5 FP32 TFLOP/s. I don't know about computer starved. In territory i'm not sure about though"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b-a3b",
      "hardware": "2080ti",
      "quantization": "",
      "speed": "100+ tok",
      "message": "2080ti 35b gets 100+ tok"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b-a3b",
      "hardware": "3060ti",
      "quantization": "",
      "speed": "39 tps \u00b7 39 tok/s",
      "message": "I'm running qwen3.6 35b-a3b MTP at 39 tps stable on my 3060ti"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "IQ3_XXS",
      "hardware": "RX 7900 XTX, 192GB DDR5",
      "quantization": "iq3-xxs",
      "speed": "5 tok/s \u00b7 5 tok/s",
      "message": "I have two RX 7900 XTX, and 192GB of DDR5, and was only able to hit 5 tok/s at IQ3_XXS\n\nAnd the quality of output was not what I would consider \"acceptable\". My first prompt was \"Hello\" and it responded in chinese"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "3080 10gb",
      "quantization": "",
      "speed": "2 t/s, 60t/s pp, 5t/s decode \u00b7 2 tok/s, 60 tok/s, 5 tok/s, 2 tok/s",
      "message": "my \u201crig\u201d is fucked lol. all i have is a pc w 3080 10gb which does like 2 t/s on 27b and a 32gb m4 mac mini which doesn\u2019t have the ram to run it really. i\u2019m using rpc to split across them both and get like 60t/s pp and 5t/s decode"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "glm-5.2",
      "hardware": "6x RTX 5090",
      "quantization": "",
      "speed": "6.84 tok/s \u00b7 6.84 tok/s",
      "message": "Detailed GPU experiment: GLM-5.2 on 6x RTX 5090 \u2014 full expert residency across VRAM+RAM reaches 6.84 tok/s single-request decode."
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b",
      "hardware": "k40",
      "quantization": "",
      "speed": "20-25 tokens per second \u00b7 25 tok/s",
      "message": "Tbf, larger models work in \u201cemail mode\u201d. On my k40\u2019s that I modded im getting about 20-25 tokens per second generation speed for qwen 3.6 for example, the 35B one. Like its useable enough for me"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_model",
      "model": "glm-5.2",
      "hardware": "RTX 5070 Laptop (8 GB), Ryzen AI 7 350, 32 GB RAM",
      "quantization": "",
      "speed": "~0.3 tok/s, ~0.2 tok/s \u00b7 0.3 tok/s, 0.2 tok/s",
      "message": "Hey,\n\nI finally got GLM 5.2 (UD-IQ1_M) to run locally.\n\nHardware:\n\nRTX 5070 Laptop (8 GB)\nRyzen AI 7 350\n32 GB RAM\nSamsung Gen4 NVMe SSD\n\nCurrent performance:\n\nPrompt: ~0.3 tok/s\nGeneration: ~0.2 tok/s\n\nResource usage:\n\n~3.7 GB VRAM\n~31 GB RAM\nSSD at 100% utilization\nCPU around 50-60%\n\nI spent quite a while testing different configurations:\n\nGPU layers\nthread count\ncache sizes\ninternal NVMe vs external HDD\nreasoning on/off\n\nThe bottleneck appears to be streaming experts rather than GPU compute.\n\nIt's honestly pretty crazy seeing a 744B MoE actually run on a consumer laptop, even if it's slow.\n\nHas anyone managed to squeeze noticeably higher throughput from similar hardware?"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "3090",
      "quantization": "",
      "speed": "~3000+ ts prefill \u00b7 3000 tok/s",
      "message": "... these prefill numbers are still wack. I have ~3000+ ts prefill on a 3090"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "dual channel memory and cpu",
      "quantization": "",
      "speed": "20-25 tokens per second \u00b7 25 tok/s",
      "message": "I mean yes, but I dont know about 20-25 tokens per second on a dual channel memory and cpu though."
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "dgx spark clusters",
      "quantization": "",
      "speed": "<10 tokens a sec \u00b7 10 tok/s",
      "message": "I thought dgx spark clusters were <10 tokens a sec"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "9070 xt + 3070 Ti, 9070 xt + 7800 xt",
      "quantization": "",
      "speed": "550-700 t/s to 250-450 t/s \u00b7 700 tok/s, 450 tok/s, 700 tok/s, 450 tok/s",
      "message": "So I'm testing and 9070 xt + 3070 Ti on vukan and finding this to have much faster prefill than 9070 xt + 7800 xt on vulkan.\n\n550-700 t/s to 250-450 t/s.\n\n Even tensor splitting the same 14.5 GB on 9070 xt and 7gb on the 7800 xt is showing poorer results than with the 3070 ti."
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "5060ti",
      "quantization": "",
      "speed": "21 tokens per second \u00b7 21 tok/s",
      "message": "hmmm, with llamma.cpp and 20 layers on the gpu, i'm getting 21 tokens per second on the 5060ti"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "24GB of VRAM, 3090",
      "quantization": "Q4_K_M, Q5",
      "speed": "45\u201350 t/s with dense models, 110 t/s with MoE models \u00b7 50 tok/s, 110 tok/s, 50 tok/s, 110 tok/s",
      "message": "And the reason for the KV cache setting is that I'm trying to stick with the Q4_K_M model\u2014since, for me, Q5 makes the context size unfeasible. I have 24GB of VRAM; I get 45\u201350 t/s with dense models, whereas I'm achieving 110 t/s with MoE models on my 3090"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "5060ti",
      "quantization": "",
      "speed": "40-60 tokens/sec \u00b7 60 tok/s",
      "message": "sorry for the direct ping, with 20 experts on the 5060ti and 20 on the GPU, i'm getting 40-60 tokens/sec. I've done some back of the napkin (ai hallucinated) math and it doesn't seem like i'm utilizing my memory bandwidth at all. (seems like i can hit 80gb/s of the 170 gb/s theoretical bandwidth with my current virtualization / bios settings; and of that 80gb/s i use like 2gb/s during inference) Does that sound right for you?"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "5070 Ti",
      "quantization": "",
      "speed": "25+ t/s \u00b7 25 tok/s",
      "message": "I have 5070 Ti so I should be getting like 25+ t/s with MTP shouldn't I"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "4x 5060 ti\u2019s",
      "quantization": "INT8-Autoround",
      "speed": "60 tokens a second \u00b7 60 tok/s",
      "message": "I would think it would be higher. Especially with MTP. I GET 60 tokens a second with 4x 5060 ti\u2019s at INT8-Autoround with unquantified kv cache and MTP"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "rtx 5070",
      "quantization": "",
      "speed": "50tps \u00b7 50 tok/s",
      "message": "cant say its faster then other models of same arch its around 50tps on rtx 5070"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "5060 Ti",
      "quantization": "",
      "speed": "35 tok/s \u00b7 35 tok/s",
      "message": "theoretically I should get like 35 tok/s because I have double the bandwidth of that 5060 Ti"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "4x3090",
      "quantization": "",
      "speed": "7t/s \u00b7 7 tok/s, 7 tok/s, 7 tok/s",
      "message": "I get just 7t/s with 4x3090 and 8 chan dd4"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "PCIe 2.0 x1 is only 500MB/s",
      "quantization": "",
      "speed": "500MB/s, 10tps target \u00b7 10 tok/s",
      "message": "PCIE 2.0 x1 is only 500MB/s. @ 10tps target that's 50MB per token not counting overhead, not thinking about how much latency that adds... etc"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "RX 7800 xt",
      "quantization": "",
      "speed": "80t/s, 68t/s \u00b7 80 tok/s, 68 tok/s, 80 tok/s, 68 tok/s",
      "message": "same but on an RX 7800 xt I get 80t/s(2650Mhz), 68t/s(2000Mhz)"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "4x 5060 ti",
      "quantization": "nvfp4",
      "speed": "t/s at 1,4,8,12,16 concurrency \u00b7 1 tok/s",
      "message": "running some benchmarks with 4x 5060 ti's with P2P and PP=4 with that new unsloth/nvfp4. Testing prefill and t/s at 1,4,8,12,16 concurrency"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "CPU offload",
      "quantization": "",
      "speed": "40 to 70tps \u00b7 70 tok/s",
      "message": "CPU offload. It's a Moe model so you would get still good speed like 40 to 70tps depending on ur pc"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "m4 macbook air with 16gb memory",
      "quantization": "",
      "speed": "40 tok/s \u00b7 40 tok/s",
      "message": "I have a m4 macbook air with 16gb memory, I don't think could get 40 tok/s"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "6 5090s",
      "quantization": "",
      "speed": "7tk/s \u00b7 7 tok/s, 7 tok/s, 7 tok/s",
      "message": "6 5090s and it couldn't even reach 7tk/s"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "EPYC 7443 (24C/48T, Zen3 AVX2) \u00b7 430 GB RAM",
      "quantization": "",
      "speed": "1tok/s \u00b7 1 tok/s, 1 tok/s",
      "message": "\"EPYC 7443 (24C/48T, Zen3 AVX2) \u00b7 Linux \u00b7 430 GB RAM \u00b7 NVMe RAID-Z1 via TrueNAS VM\" - this gets 1tok/s on colibri. the rest of the benches don't look too hot either. at least it' possible though"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "partial CPU offload",
      "quantization": "",
      "speed": "output speed",
      "message": "How can i partial CPU offload the mtp version while getting still the best output speed ?"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "16gb vram",
      "quantization": "",
      "speed": "slooooow",
      "message": "trying to keep it beneath 16gb vram usage and its slooooow now"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "nvidia",
      "quantization": "",
      "speed": "50% faster",
      "message": "Vulkan on nvidia vs cuda is no comparison. Cuda is like 50% faster"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "ddr4 and 12400f",
      "quantization": "",
      "speed": "numbers are still better",
      "message": ".. I guess? but with n-cpu-moe I know for a fact those numbers are still better on my PC, like far better. Making me wonder what else he's doing. I have ddr4 and 12400f, nothing high end, shitty budget motherboard too"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "rx6900xt",
      "quantization": "",
      "speed": "far better",
      "message": "probably? I can't speak for cuda, didn't test it extensively, but on my rx6900xt ROCM was awful and Vulkan was far better"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "3090",
      "quantization": "",
      "speed": "prefill/TTFT",
      "message": ".. get a 3090 it's legitimately rapid to start a fresh convo since I got one. Or, more broadly, an nvidia card.\n\nAlternately: increase your batch/ubatch setting. That can significantly improve your prefill/TTFT (but trial it, it's only up to a point)"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4 R9700s (+1 more being RMA'd) + 2 V620s, 2 EPYC 7532s, 8x32GB of DDR4-3200 each",
      "quantization": "",
      "speed": "speeds up CPU decode by 30% or so",
      "message": "Sorry for the delay, was in a doctor appointment.\nI have 4 R9700s (+1 more being RMA'd) + 2 V620s, plus some CPU offloading (2 EPYC 7532s, 8x32GB of DDR4-3200 each). I have a fork of llama.cpp with NUMA support, speeds up CPU decode by 30% or so.\nStill in the optimization process so I don't have any figures to give."
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4x 5060 ti",
      "quantization": "",
      "speed": "",
      "message": "In my benchmarks, pipeline parallism with 4x 5060 ti's doesn't seem to yield better t/s until at least 8 or higher concurrency. I don't know if my benchmarks are flawed though"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "390GB/s per die",
      "quantization": "",
      "speed": "390GB/s per die",
      "message": "I disassembled it last night so I can re-mount just the gpus on my gpu rack (I took them off the rack cause the motherboard was flexxing to much) but I was getting a little over 390GB/s per die in practice, under a heavy hermes agent stress test, total system bandwidth was a little over 6.4TB/s but that was including my V620"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "400Mb/s bandwidth",
      "quantization": "",
      "speed": "400Mb/s",
      "message": "I was seeming 400Mb/s for bandwidth with TP=4 once it was done loading the model"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4x 5060 ti's",
      "quantization": "",
      "speed": "performance difference",
      "message": "yeah, I wish it made sense for me to use llama-cpp. but with 4x 5060 ti's with TP=4 the performance difference is worth it to use vllm"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "5090",
      "quantization": "",
      "speed": "30s for 25k tokens",
      "message": "me when i wait 30s for 25k tokens to prefill on a 5090"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "mi50",
      "quantization": "",
      "speed": "prefill ~1300, token gen ~50",
      "message": "i tried llaminate right now for my mi50, while prefill was at around 1300 declining to 1100 for longer prompts the token gen was only around 50"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "2080S",
      "quantization": "",
      "speed": "faster tokens",
      "message": "i don't need faster tokens with my 2080S"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4x4 nvmes on an x16 pcie4 port",
      "quantization": "",
      "speed": "",
      "message": "this is so janky. now i wonder if 4x4 nvmes on an x16 pcie4 port in raid mode could raise those tok/s"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "Intel optane ... 28gb/sec read or write speed",
      "quantization": "",
      "speed": "28gb/sec",
      "message": "Maybe Intel optane would become \"useful again\" for colibri.\nGiven the fact they can be parallelized too..\n4 Intel optane s\u00e9ries 2 in parallel seems to be around 28gb/sec read or write speed"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4x5060 ti's",
      "quantization": "Q8",
      "speed": "6.5 seconds",
      "message": "With Q8 with bf16 kv cache on 4x5060 ti's the prefill is still ass at 4+ concurrency with P2P\n\nI tried TP=2 PP=2 and that made it so TTFT mean and median were around 6.5 seconda at 6 concurrency. at 8 concurrency, the TP overhead on the PCIE lanes started to slow down TTFT/prefill"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4x 5060 ti",
      "quantization": "unsloth/nvfp4",
      "speed": "TTFT/prefill climbs significantly",
      "message": "benchmark done using new faster unsloth/nvfp4 on 4x 5060 ti's with PP=4 with P2P working\n\n https://gist.github.com/joorklee/30f71926c729532a8a05bbe27a4e3807 \n\nbenchmark is done. above 8 concurrency with 4x 5060 ti's even with P2P enabled and PP=4 for less PCIE bandwidth overhead at 12 concurrency TTFT/prefill climbs significantly."
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4 lanes of gen 4",
      "quantization": "",
      "speed": "prefill hit a PCIE bandwidth bottleneck",
      "message": "somewhere between 9 and 12 concurrency the prefill hit a PCIE bandwidth bottleneck on 4 lanes of gen 4 per card"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "laptop",
      "quantization": "",
      "speed": "3gb/s",
      "message": "right now the current solution pulls 3gb/s on my shitass laptop and all the red CPU usage is just massive amounts of little nvme reads"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "dual 9070 xt",
      "quantization": "",
      "speed": "prefill gets worse after 50k ish context",
      "message": "Yo dual 9070 xt is nice for $1.3k but the hugest bottleneck I think is the L2 cache. It's not unified like Nvidia's, prefill gets worse after 50k ish context because it has to evict and repopulate kv and that causes big drop off in overall speed at long context"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "Blackwell",
      "quantization": "",
      "speed": "2x",
      "message": "unfortunately Blackwell isn't always getting 2x speedups because inference engines and quantizer scripts are having a hell of time implementing it"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "4090",
      "quantization": "",
      "speed": "0.02 tok/s",
      "message": "hey technically you can run it on like a 4090 with 0.02 tok/s!"
    },
    {
      "month": "2026-07",
      "tier": "hw_speed",
      "model": "",
      "hardware": "vram",
      "quantization": "",
      "speed": "latency tax",
      "message": "if you can't fit in vram then you pay latency tax that ruins the benefit for you"
    },
    {
      "month": "2026-07",
      "tier": "inferred",
      "model": "",
      "hardware": "macbook",
      "quantization": "",
      "speed": "10 tokens per sec \u00b7 10 tok/s",
      "message": "sadly on my macbook only 10 tokens per sec.."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-35b",
      "hardware": "AMD APU, 7840U, 780M, 32GB",
      "quantization": "Q4_K_XL",
      "speed": "Gen TPS 21.4",
      "message": "o/ - I have been experimenting with persistent ssd backed kv cache and other improvements to help improve llama.cpp performance on my AMD APU based devices ( 7840U / 780M / 32GB, etc) - thought I'd share incase it was interesting to anyone else.\n\nIt wouldn't make sense if you have a GPU, but it might if you're like me and you don't. \n\n #### Qwen3.6-35B (Q4_K_XL, 35B MoE, hybrid)\n\n| Size | Tokens | Cold TTFT | Warm TTFT | Speedup | Gen TPS |\n|--------|--------|-----------------|-----------|---------|---------|\n| Small | ~1243 | 8.8s | 0.4s | 20.1x | 21.4 |\n| Medium | ~5409 | 39.1s | 0.6s | 61.9x | 20.7 |\n| Large | ~15.7K | 125.1s (2.1min) | 1.1s | 117.8x | 19.0 | \n\n https://github.com/fewtarius/llama-ai \n https://github.com/fewtarius/llama.cpp"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "gemma4-31b",
      "hardware": "3090ti, ~24GB, >8GB gpu",
      "quantization": "4bit qat",
      "speed": "45t/s \u00b7 45 tok/s, 45 tok/s, 45 tok/s",
      "message": "if we taking actual coding out of the equation, which models is better. gemma4 31b needs like ~24GB with mtp and vision. tested it on 3090ti, 45t/s, sometimes more. gemma4 qat 12b seems to be popular now but still needs >8GB gpu, to run the 4bit qat, being a dense model."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "5090",
      "quantization": "int4 autoround",
      "speed": "80t/s \u00b7 80 tok/s, 80 tok/s, 80 tok/s",
      "message": "WSL on Windows is ok if you are forced to be on it. I get over 80t/s with Intel's Qwen 3.6 27B int4 autoround quant with vLLM on my 5090, and it's rock solid memory wise"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "gemma4-26b",
      "hardware": "3090",
      "quantization": "QAT",
      "speed": "pretty damn fast",
      "message": "this is gemma4 26b + draft model on a 3090, it's already pretty damn fast. it'd be cool if they do a QAT of the diffusion one tho."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "gemma4-31b",
      "hardware": "24Gb",
      "quantization": "q8_0, IQ4_XS",
      "speed": "78.12 t/s, 68.55 t/s \u00b7 78.12 tok/s, 68.55 tok/s, 42.89 tok/s, 16384 tok/s",
      "message": "My speed champion for single card was using the beellama.cpp fork with DFlash ( 78.12 t/s 42.89% acceptance on writing python.)\nHIP_VISIBLE_DEVICES=0 build-rocm/bin/llama-server -hf \"$TARGET_HF\" -hfd \"Anbeeld/gemma-4-31B-it-DFlash-GGUF:IQ4_XS\" --spec-type dflash --no-spec-dm-adaptive --spec-draft-n-max 16 --spec-draft-p-min 0.0 --spec-draft-ctx-size 1024 --spec-dflash-cross-ctx 1024 --spec-draft-temp auto --host 0.0.0.0 --port 8080 -fa on --reasoning on --reasoning-loop-min-tokens 16384 -ngl 999 -ngld 999 -fit off --temp 1.0 --top-p 0.95 --top-k 64 --ctx-size 32768 -np 1 --threads 8 --mmap --no-mmproj -sm none -ctk q8_0 -ctv q8_0 -ctkd q8_0 -ctvd q8_0 -b 2048 -ub 512 --metrics --log-timestamps\n\nI've deleted the repo and build files, but that was working on my 24Gb last night, maybe that'll get you going? \n\nI just tried this config to run mainline, with mtp on 24Gb of ram. (68.55 t/s 58% acceptance.)\n GGML_CUDA_ALLREDUCE=nccl HIP_VISIBLE_DEVICES=0 build-rocm-rccl/bin/llama-server -hf \"unsloth/gemma-4-31b-it-GGUF:UD-Q4_K_XL\" --spec-type draft-mtp --spec-draft-n-max 10 --host 0.0.0.0 --port 8080 -fa on --reasoning on -ngl 999 -fit off --temp 1.0 --top-p 0.95 --top-k 64 -np 1 --threads 8 --mmap --cache-ram 0 -ctk f16 -ctv f16 -b 2048 -ub 512 --metrics --log-timestamps\n\nI think the NVIDIA versions of those commands should fit in 24Gb?"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "llama 2 7B",
      "hardware": "AMD GPUs, 32GB, 512 GB/s",
      "quantization": "Q4_0",
      "speed": "1250 t/s PP, 70 t/s TG, 1000 t/s PP, 55 t/s TG \u00b7 1250 tok/s, 70 tok/s, 1000 tok/s, 55 tok/s",
      "message": "They're AMD GPUs. 32GB, 512 GB/s speed. The MI50 32GB used to be the cheapest high-capacity GPU, but those have gone up in price so V620s are the new king(?).\nThey're solid for the price. According to the llama 2 7B Q4_0 tests on the l.cpp GitHub, 25%-ish better performance than the P40 (and 8GB more VRAM).\nV620: 1250 t/s PP and 70 t/s TG\nP40: 1000 t/s PP and 55 t/s TG"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.5-27b",
      "hardware": "2x AMD Instinct MI50/MI60",
      "quantization": "Q8_0",
      "speed": "256.29 t/s, 180.34 t/s, 147.99 t/s, 28.45 t/s, 27.45 t/s, 20.72 t/s, 233.83 t/s, 168.49 t/s, 133.12 t/s, 27.43 t/s, 26.68 t/s, 19.32 t/s \u00b7 20 tok/s, 20 tok/s",
      "message": "You should be able to get +20 t/s generation easy with two V620 in tensor parallel, here's some numbers from my own setup:\n\n ========================================================================================\nTest Scenario Tensor (Full) Tensor (PCIe 1.0) Layer Split PCIe Drop %\n========================================================================================\npp2048 (Prefill) 256.29 \u00b1 0.15 180.34 \u00b1 0.03 147.99 \u00b1 0.03 -29.63%\ntg256 (Decoding) 28.45 \u00b1 0.06 27.45 \u00b1 0.05 20.72 \u00b1 0.01 -3.51%\npp2048 @ 16k Context 233.83 \u00b1 0.75 168.49 \u00b1 0.38 133.12 \u00b1 0.06 -27.94%\ntg256 @ 16k Context 27.43 \u00b1 0.25 26.68 \u00b1 0.25 19.32 \u00b1 0.02 -2.73%\n========================================================================================\n* Model: Qwen 27B Q8_0 | GPUs: 2x AMD Instinct MI50/MI60\n* \"PCIe Drop %\" shows performance loss of Tensor (PCIe 1.0) compared to Tensor (Full)."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-35b-a3b",
      "hardware": "dual 3060's",
      "quantization": "Q6_K_XL",
      "speed": "~260 pp/sec; ~170 pp/sec",
      "message": "I'm running dual 3060's in my PC, and I'm trying to isolate a performance problem. So I run Qwen3.6-35B-A3B-UD-Q6_K_XL, with -c 131072 and the MOE offloaded to the cpu. Using -dev CUDA0 and I get ~260 pp/sec I run it on -dev CUDA1, and I'm only getting 170 pp/sec. Both have similar tg/sec. The only diff between the two cards is one is running on a PCIE16x that's direct to the cpu, and the other is running PCIE8x that's direct to the CPU... Could that be the difference?"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "m1 max",
      "quantization": "a4b-qat",
      "speed": "52.76 tokens/sec, 3.37 secs to first token, 18.91 tokens/sec, 0.87 secs to first token \u00b7 52.76 tok/s, 18.91 tok/s",
      "message": "oh i tried gemma 4 today on my m1 max (macbook pro) and compared it to one of the qwen models, used a really simple prompt, gemma4 was a lot worse than qwen:\n\ngpu: m1 max base model\n\nmodel: google/gemma4-26b-a4b-qat\nprompt: write me a javascript mandelbrot function that runs in a browser\nresults: generation: 52.76 tokens/sec, 3.37 secs to first token, no data on prompt processing\n\nmodel: qwen3.6-27b-mlx\nprompt: write me a javascript mandelbrot function that runs in a browser\nresults: generation: 18.91 tokens/sec, 0.87 secs to first token, no data on prompt processing\n\ncomments: image quality and code was much better on qwen, pan and zoom in/out worked (unlike gemma4)"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "Gemma-4 MeroMero 31B",
      "hardware": "RTX 5060 Ti 16GB + RTX 3060 12GB",
      "quantization": "IQ4_XS",
      "speed": "14.6 tokens/s \u00b7 14.6 tok/s",
      "message": "hey guys, I am currently running a local Gemma-4 MeroMero 31B IQ4_XS model on KoboldCPP, setting layers so that the 5060 Ti handles most of the workload in a dual GPU setup (RTX 5060 Ti 16GB + RTX 3060 12GB). My current speed is 14.6 tokens/s. If I replace the 3060 with an RTX 5070 Ti, what speed can I expect compared to the old combo?"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "dual V620",
      "quantization": "Q4_M",
      "speed": "",
      "message": "Any of you guys that have a dual V620 that could test Qwen3.6-27B Q4_M with MTP=3 and tell me what is the tok/s ? I couldn't find any info about it on the interwebz"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "M4 Mac Mini with 16GB",
      "quantization": "4bit",
      "speed": "14 tokens/s \u00b7 14 tok/s",
      "message": "GLM 5.2 is optimizing the fuck out of my M4 Mac Mini with 16GB. It got Qwen 3.6 27B 4bit running at 14 tokens/s on a bag of potato chips"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "16GB M1 Pro Mac",
      "quantization": "~3 bits, TurboQuant",
      "speed": "10 t/s \u00b7 10 tok/s, 10 tok/s",
      "message": "Qwen 3.6 27B ~3 bits with no vision and TurboQuant around 10 t/s no MTP or DFlash on my 16GB M1 Pro Mac from 2021"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "2x 5060 ti\u2019s",
      "quantization": "Q6_K",
      "speed": "30 tokens a second \u00b7 30 tok/s",
      "message": "Hey peeps.\n\nTrying out a Q6_K quant of qwen 3.6 27b to see the tokens per second on 2x 5060 ti\u2019s\n\nRunning it with p2p enabled and without MTP.\n\nGetting 30 tokens a second."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.5-27b",
      "hardware": "AMD Instinct MI50/MI60",
      "quantization": "Q8_0",
      "speed": "pp2048 256.29",
      "message": "If I'm remembering correctly, MTP wasn't that big of an improvement on the MI50 (probably because of the compute limitations), but here's my numbers running Q8 with two cards:\n\n ========================================================================================\nTest Scenario Tensor (Full) Tensor (PCIe 1.0) Layer Split PCIe Drop %\n========================================================================================\npp2048 (Prefill) 256.29 \u00b1 0.15 180.34 \u00b1 0.03 147.99 \u00b1 0.03 -29.63%\ntg256 (Decoding) 28.45 \u00b1 0.06 27.45 \u00b1 0.05 20.72 \u00b1 0.01 -3.51%\npp2048 @ 16k Context 233.83 \u00b1 0.75 168.49 \u00b1 0.38 133.12 \u00b1 0.06 -27.94%\ntg256 @ 16k Context 27.43 \u00b1 0.25 26.68 \u00b1 0.25 19.32 \u00b1 0.02 -2.73%\n========================================================================================\n* Model: Qwen 27B Q8_0 | GPUs: 2x AMD Instinct MI50/MI60\n* \"PCIe Drop %\" shows performance loss of Tensor (PCIe 1.0) compared to Tensor (Full)."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "2 5060 ti's 16GB",
      "quantization": "FP8",
      "speed": "2500",
      "message": "waiting on the delivery of 2 5060 ti's to confirm. but if your use case is only inference, this might be the strat while GPU prices are inflated. The downside is finetuning and non inference tasks wouldn't be viable on this setup. But 4x 5060 ti's 16GB for 64GB total should be able to run Qwen/Qwen3.6-27B-FP8 with 4 concurrency and 262144 context with bfloat16 KV cache.\n\nThe tokens per second will be interesting to confirm with this setup.\n\nBut you could run Q8/FP8 quant with max context for roughly 2500 total (guestimating). Pickup an old ryzen CPU that has 16 dedicated lanes to the first PCI x16 slot, bifurcate it into x4 lanes of gen 4 pci and have a 5060 ti on each of the 4 oculink 4x lanes. CPU + DDR4 RAM would be maybe 300-500, motherboard maybe 150, PSU probably 200, case price idunno.\n\nAnd you can get 5060 ti's for 400 to 450 USD each if you watch for deals on slickdeals or etc.\n\nCompared to spending 3000 for 2x 3090's where you will be limited to 48GB or RAM or 2x 4090's for 6000, 2x 5090's for 8000+ its a solid strat for inference only use case"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "4x 5060 ti 16gb for 64 gb total",
      "quantization": "FP8",
      "speed": "70 tokens /second \u00b7 70 tok/s, 70 tok/s",
      "message": "4x 5060 ti 16gb for 64 gb total. Able to run Qwen/Qwen3.6-27b-FP8 with bf16 kv cache, 262K context, 4 concurrency, and 16k batch tokens at 70 tokens /second"
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.5-122b",
      "hardware": "64GB RAM",
      "quantization": "GGUF",
      "speed": "EXTREMELY fast",
      "message": "I tested several days with the Q1 from this model: https://huggingface.co/unsloth/Qwen3.5-122B-A10B-GGUF .\n\nI even had it write entire chunks of code. I had it analyze bugs without realizing I was using this model. LMStudio hides the model quantization you\u2019re running, despite repeated complaints about this. \n\nI was completely blown away by what it had done. It had indeed made a few minor bugs. It had added an extra quote here and there, but the entire code and the entire debugging process had gone exactly as planned.\n\nTo those who think a Q1 isn\u2019t capable of much, I say the opposite! These things are EXTREMELY fast and highly usable. Especially for everyday chat, online searches, combing through code for bugs, etc., etc... Even code design.\n\nJust try it! You wont die from it! If you have 64GB RAM, this will work. However, if you have a fast GPU, this will help. Something we all know in here..."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "26B-A4B",
      "hardware": "CPU only",
      "quantization": "Q4_K_XL",
      "speed": "64 tok/s \u00b7 64 tok/s",
      "message": "Wow I'm getting 64 tok/s on 26B-A4B Q4_K_XL on CPU only now. Also PP is usually more like 250+ but this was a short prompt so I guess it wasn't enough to get a good measure."
    },
    {
      "month": "2026-06",
      "tier": "full",
      "model": "qwen3.6-27b",
      "hardware": "two Macs with Thunderbolt",
      "quantization": "q4",
      "speed": "5 tokens/s \u00b7 5 tok/s",
      "message": "I do get 5 tokens/s on q4 27b if I link my two Macs with Thunderbolt. That\u2019s without MTP"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "minimax-m2.5",
      "hardware": "4090",
      "quantization": "",
      "speed": "7tk/s \u00b7 7 tok/s, 7 tok/s, 7 tok/s",
      "message": "hey, i'm trying to toy around with LFM2.5 8B A1B but i'm getting a rather shocking 7tk/s on a 4090"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "rtx6k",
      "quantization": "",
      "speed": "20ish",
      "message": "rtx6k can handle 20ish nonstop parallel requests for qwen 3.6 27b (on vllm). i think it depends on the use you're aiming for. using coding agents will require a beefier setup"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.5-27b",
      "hardware": "rx 9070xt",
      "quantization": "q3-k",
      "speed": "15-20t/s \u00b7 20 tok/s, 20 tok/s, 20 tok/s",
      "message": "I tried using lllamacpp vulkan and qwen 27b q3 on my rx 9070xt and i get like 15-20t/s output"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "80gb dense model",
      "hardware": "1.9tb/s",
      "quantization": "",
      "speed": "20tk/s \u00b7 20 tok/s, 20 tok/s, 20 tok/s",
      "message": "to run bigger models you need more bandwidth. Lets say you're trying to run a 80gb dense model on 1.9tb/s. That will only yield about 20tk/s at full theorotical bandwidth"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "deepseek-v4-flash",
      "hardware": "32gb ram i3 13100f",
      "quantization": "",
      "speed": "0.5tps \u00b7 0.5 tok/s",
      "message": "Any tips for making deepseek v4-flash run faster I have 32gb ram i3 13100f running it in wsl it's using about 15gb ram getting 0.5tps and not maxing out any comments getting 70 percent nvme 40 CPU and ram has a few GB left"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b-a3b",
      "hardware": "rtx 3090",
      "quantization": "",
      "speed": "150token/seconds",
      "message": "so with diffusiongemma we are trading accuracy vs speed. it's not that interesting no? after all I have around 150token/seconds on qwen3.6-35b-A3b running on a rtx 3090 , which is enough fast to be usable and far more intelligent than diffusiongemma"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "gemma4-12b",
      "hardware": "5090 desktop, 4070 laptop, 5080 desktop",
      "quantization": "",
      "speed": "19 tps, 96 tps \u00b7 19 tok/s, 96 tok/s",
      "message": "I just pulled the trigger on a 5090 desktop. I ran an experiment this morning, google/gemma-4-12b-qat runs at 19 tps on a 4070 laptop, 96 tps on my son's 5080 desktop, and i'm expecting significantly better on a 5090 (dont have that to test)"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b-a3b",
      "hardware": "Rtx 3060 12gb, Xeon 2650 v4, 32 RAM",
      "quantization": "",
      "speed": "35.20 t/s \u00b7 2.301 tok/s, 35.2 tok/s, 35.2 tok/s",
      "message": "Rtx 3060 12gb + Xeon 2650 v4 + 32 RAM\n2.301 tokens | 1min 5s | 35.20 t/s\n\nIs it good?\nllama-server.exe ^\n -m \"C:\\Users\\Rafael\\Downloads\\models\\Qwen3.6-35B-A3B-APEX-MTP-I-Compact.gguf\" ^\n -ngl all ^\n -t 16 ^\n --n-cpu-moe 15 ^\n -c 90000 ^\n -b 2048 ^\n -ub 1024 ^\n --no-mmap ^\n --ctx-checkpoints 128 ^\n --mlock ^\n --prio 2 ^\n --prio-batch 2 ^\n -fa on ^\n -ctk turbo3_tcq ^\n -ctv turbo3_tcq ^\n -np 1 ^\n --port 8080"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "RTX 5070 Ti 16 GB, 32 GB of RAM, Ryzen 9900X",
      "quantization": "",
      "speed": "2.5 tokens per second \u00b7 2.5 tok/s",
      "message": "all good - I've just downloaded Qwen 3.6 27B model and I'm not sure if there's any config I can adjust, but it's taking like 2.5 tokens per second?\n\nRTX 5070 Ti 16 GB\n32 GB of RAM\nRyzen 9900X"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.5-27b",
      "hardware": "2x MI50 32GB",
      "quantization": "fp16, q8",
      "speed": "185.88 tokens per second \u00b7 185.88 tok/s, 167 tok/s, 20.84 tok/s, 50 tok/s",
      "message": "2x MI50 32GB with Qwen 27B Q8 / FP16 gives this at agentic coding contexts:\n\n19.18.577.068 I slot print_timing: id 0 | task 0 | prompt eval time = 717955.95 ms / 133456 tokens ( 5.38 ms per token, 185.88 tokens per second )\n\n19.43.889.896 I slot print_timing: id 0 | task 70 | eval time = 8014.40 ms / 167 tokens ( 47.99 ms per token, 20.84 tokens per second )\n\nNot that big of an improvement honestly, you double the cards and only get +50 t/s on pp and +5 t/s on tg."
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "2 v100",
      "quantization": "",
      "speed": "60-80tok/s \u00b7 80 tok/s, 80 tok/s",
      "message": "Nah I'm probably doing what Black Jesus suggested B70 or AMD V620, I'm just searching some benchs or trying to rent to do my test case, I'm aiming for at least have Qwen3.6-27B at 60-80tok/s I prove that with 2 v100, but I'm really concerned about cooling and idle power and of course spending it on a 10year platofrm that could die on me at any moment"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "16GB Mac mini",
      "quantization": "",
      "speed": "14 t/s \u00b7 14 tok/s, 14 tok/s",
      "message": "Okay so we\u2019re at 14 t/s @64k context for Qwen 3.6 27B on the 16GB Mac mini"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "gemma4-e4b",
      "hardware": "i5 / 16gb ram / rtx 2070",
      "quantization": "",
      "speed": "fast \u00b7 4000 tok/s, 120 tok/s",
      "message": "hello ! i'm running gemma4 e4b locally to classify court documents. my config is relatively old (2019 i5 / 16gb ram / rtx 2070). model is running fast and without any problems on normal questions but as soon as I try to pass court documents (whom are around ~4000 tokens) the model starts to answer, get it clearly (no hallucination, it gives me information from the document) and stops after outputing a few tokens (from my test, it stops after outputing ~120 tokens). It's not telling me a clear refusal, it's rather answering exactly how I want but stopping mid sentence\n\ni tried disabling thinking (still same problem)\n\ni have a \"weird\" guess that the model may stop due to the court documents describing criminal activities; but for now, the only documents I passed to the model involves petty crime (shoplifting, DUI...)\n\nit's my first time trying local models for this task, where do you think it is coming from ? and if it's coming from the model, what would be a good alternative to gemma ? my main objective is having the fastest token output, i'd rather have a few hallucinations than a slow model as i've got thousands of documents to classify"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "Llama-3.2-3B-Instruct",
      "hardware": "geforce mx440",
      "quantization": "",
      "speed": "about a minute per pdf",
      "message": "Like 6 months ago I ran some experiments, I have code ready for you which you likely just need to ask an LLM to tweak a little bit.\nDocling for extraction to markdown of PDFs \nOllama + Llama-3.2-3B-Instruct IIRC , need to check it, (works on CPU only, I couldn't fit it well on my laptop's geforce mx440 ) for parsing markdown and extracting into structured formatted JSON \nTook about a minute IIRC per pdf, but there are better models now to do it.\n\nHaven \u00b4t touched it in a bit.. actually need to refactor it today for some court case I have coming up."
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "deepseek",
      "hardware": "k80s",
      "quantization": "",
      "speed": "4 tok/s \u00b7 4 tok/s",
      "message": "well, if i feel like putting in untold hours of work to get 4 tok/s on deepseek on my k80s at 100x the power cost of openrouter, only to be told to knock that off by IT, I will be sure to come back and update you guys"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "gemma4-26b",
      "hardware": "dual 6248R",
      "quantization": "",
      "speed": "38-40 tok/s generation \u00b7 40 tok/s",
      "message": "Hey FYI I didn't abandon this NUMA mirror thing! I had Opus 4.8 add model weight and KV mirroring on ik_llama.cpp today! I am hoping to put it on github tonight or tomorrow if you want to try it.\n\nI also upgraded my R740 to dual 6248R to get the extra AVX512 enhancements, and populated all my memory channels now have 768 GB total.\n\nGetting 38-40 tok/s generation on gemma4 26b a4b and close to 300 pp with all cores. Decent results for pure CPU!"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "llama-server, Granite",
      "hardware": "i5-12500T, 16GB RAM, GTX 1050Ti with 4GB VRAM, i7-7700HQ, 16GB RAM",
      "quantization": "",
      "speed": "10 t/s \u00b7 10 tok/s, 10 tok/s",
      "message": "Just figured I'd introduce myself (doesn't seem to be an #introductions channel). I've been playing with llama-server some locally, mostly out of curiosity out of what I can get it to do on my existing computers.\n\nI'm mostly using it on a little HP 400 G9 Mini with an i5-12500T (unfortunately 12th-gen, so no AVX512 -- bought it mostly as a small server) with 16GB of RAM, though I've ended up with a set of models that are reasonably fast on it. I've been particularly impressed with some of the MoE Granite models. Only machine I have with a GPU is a Lenovo Y520 from 2017 (i7-7700HQ, 16GB RAM, GTX 1050Ti with 4GB VRAM); that machine ends up about half the speed on the HP, but with the GPU is about 10 t/s faster.\n\n(Have also played with it on my cheap 2023 Motorola phone, just becasue I can.)\n\nMight end up setting up more infrastructure; I think I've convinced my network-geek roommate to ditch his Perplexity subscription."
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b",
      "hardware": "3 p100s",
      "quantization": "",
      "speed": "~45 tokens per second decode and ~400 tokens per second prompt processing \u00b7 45 tok/s, 400 tok/s",
      "message": "im also running qwen3.6 35b on 3 p100s with ~45 tokens per second decode and ~400 tokens per second prompt processing"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b-a3b",
      "hardware": "ddr5 6000",
      "quantization": "q4",
      "speed": "50t/s \u00b7 50 tok/s, 50 tok/s, 50 tok/s",
      "message": "if its ddr5 6000, you can expect to get around 50t/s from the 35b q4"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "gpt-oss-120b",
      "hardware": "192 GB RAM, 6000 MHz",
      "quantization": "",
      "speed": "18 tokens per second, 40-50 tok/second \u00b7 18 tok/s",
      "message": "I was running 192 GB RAM (2 times 2x48 GB) for a little while, which prevented me from using the XMP profile (they were identical kits but bought at separate times). gpt-oss 120b speeds were like 18 tokens per second. Then once I took two of the sticks out and overclocked to 6000 MHz, I was getting like 40-50 tok/second"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "Hermes",
      "hardware": "DDR3",
      "quantization": "",
      "speed": "",
      "message": "I was running Hermes on single channel DDR3 for the challenge got the t/s usable"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-35b",
      "hardware": "GPU's/RAM",
      "quantization": "",
      "speed": "30 tps \u00b7 30 tok/s",
      "message": "goddamn MTP is a god send for local inferencing , almost makes me question whether I need more GPU's/RAM . qwen 3.6 35B is running at 30 tps"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "m3 q1",
      "hardware": "128gb ram + 56gb vram",
      "quantization": "",
      "speed": "",
      "message": "how many tok/s with m3 q1 on 128gb ram + 56gb vram?"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_model",
      "model": "qwen3.6-27b",
      "hardware": "7900xtx",
      "quantization": "",
      "speed": "145tps \u00b7 145 tok/s",
      "message": "wow! 145tps on 27b dense on a 7900xtx\nthe prompt:"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "radeon rx 6900xt",
      "quantization": "",
      "speed": "around 1500t/s on empty context \u00b7 1500 tok/s, 1500 tok/s, 1500 tok/s",
      "message": "radeon rx 6900xt is the main one I use for LLMs, and its prompt processing sucks compared to nvidia. And by \"sucks\" I mean around 1500t/s on empty context."
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "L4 GPUs",
      "quantization": "bf16",
      "speed": "1,500 token/s \u00b7 500 tok/s",
      "message": "yeah it is fast I ran the full bf16 version on some cheap L4 GPUs and got 1,500 token/s with 128 parallel requests using vLLM"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "16 gigs vram",
      "quantization": "mtp and quant",
      "speed": "15 tok/s \u00b7 15 tok/s, 98 tok/s",
      "message": "on the same model mtp and quant I get 15 tok/s at 98k context 16 gigs vram"
    },
    {
      "month": "2026-06",
      "tier": "hw_speed_benchmark",
      "model": "",
      "hardware": "16GB VRAM",
      "quantization": "iq3_xxs",
      "speed": "~50-60t/s \u00b7 60 tok/s, 60 tok/s, 60 tok/s",
      "message": "try an iq3_xxs quant. I get ~50-60t/s generation on 16GB VRAM."
    }
  ]
} as const;

const HW_MSG_DATA = {
  "rows": [
    {
      "slug": "rtx-5090",
      "month": "2025-08",
      "extracted": "4090, 5090, connectx-3",
      "message": "Has anyone set up infiniband at home? I have a 4090 in one box, a 5090 in another, and I'd like to set up infiniband between them just to learn about how to configure it and play with some distributed training/inference. I bought some connectx-3 cards for like $25 on ebay but app\u2026"
    },
    {
      "slug": "rtx-5090",
      "month": "2025-08",
      "extracted": "5090, 3080, epyc server",
      "message": "I wouldnt personally.(i mean you can also slot in the 3080 why not?) keep the 5090 for prefill and build an epyc server around it to offload what you cant fit"
    },
    {
      "slug": "rtx-5090",
      "month": "2025-08",
      "extracted": "5090, 3080",
      "message": "hey folks. wanted to ask if someone can point me in the right direction.\n\nMy dumbass bought a 5090 before actually researching because I managed to snag a founder edition. The plans were quite ambitious but now im realizing I cant even run qwen 30b with context. I have a 3080 lay\u2026"
    },
    {
      "slug": "rtx-5090",
      "month": "2025-09",
      "extracted": "16GB",
      "message": "so any thoughts on if nvidea will actually release any cards higher than 16GB for the ti / super series? 5090 just for vram is quite a price jump"
    },
    {
      "slug": "rtx-5090",
      "month": "2025-09",
      "extracted": "6000 pro",
      "message": "if i had 5090 money i'd prolly just get the 6000 pro"
    },
    {
      "slug": "rtx-5090",
      "month": "2025-09",
      "extracted": "6000",
      "message": "Local pricing puts a 6000 above 3 5090's"
    },
    {
      "slug": "rtx-3090",
      "month": "2025-08",
      "extracted": "P40, 4060 ti, 5060 ti, 3090 ti",
      "message": "Im building a homelab for this, and plan on hosting a suite of specialized llms for different tasks, with one in particular managing things / acting as the assistant. Im curious what you all think about the p40? I know there's some 3d printing / cooling challenges. But is it wort\u2026"
    },
    {
      "slug": "rtx-3090",
      "month": "2025-08",
      "extracted": "3090",
      "message": "no idea, have a 3090 =/"
    },
    {
      "slug": "rtx-3090",
      "month": "2025-08",
      "extracted": "3090",
      "message": "used 3090 still king imo"
    },
    {
      "slug": "rtx-3090",
      "month": "2025-08",
      "extracted": "3\u202f\u00d7\u202f3090s, ASUS TUF, 3090fe, Gainward 3090ti, PCIe slot spacing",
      "message": "The gpus I own are 3 3090s. 1 asus tuf (2slot), 3090fe (3slot) and gainward 3090ti (3 slot i believe)\n\ni could not fit the 3rd card because the bottom 2 pcie slots are closer to eachother than the top 2."
    },
    {
      "slug": "rtx-3090",
      "month": "2025-08",
      "extracted": "Intel Core 7 20threads, 3090 FE 24GB, 64GB DDR5",
      "message": "Success! My first homelab is up and running!\nProxmox 9\nIntel Core 7 20threads\n3090 FE 24GB\n64GB DDR5\n\ngoing through the motions to set everything up. passing the GPU drivers through is a real pain.\n\nSetting up both llama.cpp and ollama, and open web ui to start"
    },
    {
      "slug": "rtx-3090",
      "month": "2025-08",
      "extracted": "2x 3090s with 48GB of VRAM, one 4090",
      "message": "What would be smarter... 2x 3090s with 48GB of VRAM or just one 4090"
    },
    {
      "slug": "rtx-5060-ti",
      "month": "2025-08",
      "extracted": "P40, 4060 ti, 5060 ti, 3090 ti",
      "message": "Im building a homelab for this, and plan on hosting a suite of specialized llms for different tasks, with one in particular managing things / acting as the assistant. Im curious what you all think about the p40? I know there's some 3d printing / cooling challenges. But is it wort\u2026"
    },
    {
      "slug": "rtx-5060-ti",
      "month": "2025-09",
      "extracted": "16gb RTX 5060 Ti",
      "message": "model recommendations for a 16gb RTX 5060 Ti? (llamacpp)"
    },
    {
      "slug": "rtx-5060-ti",
      "month": "2025-09",
      "extracted": "5060ti 16g with 64gb ddr5 and 5090 with 128gb",
      "message": "Hey guys, whats the top dog coding models? Got a 5060ti 16g with 64gb ddr5 and another system with 5090 and 128gb"
    },
    {
      "slug": "rtx-5060-ti",
      "month": "2025-10",
      "extracted": "5060ti",
      "message": "I watched the specs of 5060ti in Nvidia site - there nothing about fp8 or fp4 - only about gaming features"
    },
    {
      "slug": "rtx-5060-ti",
      "month": "2025-10",
      "extracted": "2x 5060ti 16gb",
      "message": "2x 5060ti 16gb in my area was cheaper than anyone would sell a single 3090 used"
    },
    {
      "slug": "rtx-5060-ti",
      "month": "2025-10",
      "extracted": "5060ti",
      "message": "Sorry for stupid question, does 5060(ti) have hardware support of fp8_e4m3fn ? I doesnt found that info in the specs of 5060ti"
    },
    {
      "slug": "rtx-4090",
      "month": "2025-08",
      "extracted": "4090",
      "message": "Hey guys, working on a personal project right now. I'm trying to normalize a dataset with 2M+ records using an LLM into a JSON format. Currently I'm getting decent results with nous-hermes-2-mistral-7b-dpo. However, even though it's fast on my 4090. It would still take like 3 wee\u2026"
    },
    {
      "slug": "rtx-4090",
      "month": "2025-08",
      "extracted": "4090",
      "message": "I'd probably begin with caching the model state to just after your prompt so the only thing that's changing is the row data. We have someone in here getting thousands of tokens per second on a 4090 using insrancing"
    },
    {
      "slug": "rtx-4090",
      "month": "2025-08",
      "extracted": "4090, 4080, 24gb",
      "message": "Parakeet by Nvidia, no question. Runs 600x realtime on a 4090. It'll burn rubber on a 4080. It's light as hell, so you can pretty easily run it alongside the rest of your stack without taking up too much vram. I frequently run it alongside kokoro (100x realtime voice output) and \u2026"
    },
    {
      "slug": "rtx-4090",
      "month": "2025-08",
      "extracted": "4090",
      "message": "https://www.reddit.com/r/LocalLLaMA/comments/1mt2iev/gptoss20b_at_10000_tokenssecond_on_a_4090_sure/"
    },
    {
      "slug": "rtx-4090",
      "month": "2025-08",
      "extracted": "4090",
      "message": "Well, that was a fun one. 10k tokens/second with 100% effective tool calling is hilarious off a single 4090 ;p"
    },
    {
      "slug": "rtx-4090",
      "month": "2025-08",
      "extracted": "4090",
      "message": "I'd upvote you if I could. Nice work on this. I really didn't realize the 4090 was capable of this level of throughput. I greatly underestimated this thingy"
    },
    {
      "slug": "rtx-5060",
      "month": "2025-08",
      "extracted": "P40, 4060 ti, 5060 ti, 3090 ti",
      "message": "Im building a homelab for this, and plan on hosting a suite of specialized llms for different tasks, with one in particular managing things / acting as the assistant. Im curious what you all think about the p40? I know there's some 3d printing / cooling challenges. But is it wort\u2026"
    },
    {
      "slug": "rtx-5060",
      "month": "2025-09",
      "extracted": "16gb RTX 5060 Ti",
      "message": "model recommendations for a 16gb RTX 5060 Ti? (llamacpp)"
    },
    {
      "slug": "rtx-5060",
      "month": "2025-10",
      "extracted": "2x 5060",
      "message": "Lmstudio handled my 2x 5060 well"
    },
    {
      "slug": "rtx-5060",
      "month": "2025-10",
      "extracted": "5060",
      "message": "I'm almost certain 5060 has native fp8 support"
    },
    {
      "slug": "rtx-5060",
      "month": "2025-10",
      "extracted": "5060ti",
      "message": "Sorry for stupid question, does 5060(ti) have hardware support of fp8_e4m3fn ? I doesnt found that info in the specs of 5060ti"
    },
    {
      "slug": "rtx-5060",
      "month": "2025-11",
      "extracted": "5060 ti 16gb",
      "message": "What would be the best worth for money GPU? I was looking at 5060 ti 16gb but I am not too sure"
    },
    {
      "slug": "rtx-6000-ada",
      "month": "2025-08",
      "extracted": "rtx 6000 pros",
      "message": "with a couple rtx 6000 pros you can get close =)"
    },
    {
      "slug": "rtx-6000-ada",
      "month": "2025-08",
      "extracted": "rtx 6000",
      "message": "i know what the problem is, he's got one rtx 6000 too many, if he donated one to me everything would be perfect"
    },
    {
      "slug": "rtx-6000-ada",
      "month": "2025-09",
      "extracted": "Rtx 6000",
      "message": "Blackwell Rtx 6000 workstation"
    },
    {
      "slug": "rtx-6000-ada",
      "month": "2025-09",
      "extracted": "H200; RTX 6000 96GB",
      "message": "Good for companies but for local users you wouldn\u2019t get your value out of that card. The real power of the H200 is not individual model speed or the vram- it\u2019s parallel throughout. Many many users at once.\n\nIndividual user would get far more bang for the buck at that price buying\u2026"
    },
    {
      "slug": "rtx-6000-ada",
      "month": "2025-09",
      "extracted": "3090; 5090; rtx 6000",
      "message": "It's like the same argument people have for 3090s, or 5090s vs the rtx 6000, but funnier"
    },
    {
      "slug": "rtx-6000-ada",
      "month": "2025-10",
      "extracted": "2 h200, 4x rtx 6000 pros, 5tb/s, 600gb/s bandwidth system ram",
      "message": "Btw, wouldnt you have been better off with 2 h200's instead?\n\nhalf the power consumption of 4x rtx 6000 pros\nyou only need to fit 2 gpus\n2.5x as much bandwidth (5tb/s) as blackwell rtx pro 6000 (1.9tb/s)\nsame amount of vram\n\nPretty much enables you to utilize an sp5 board like th\u2026"
    },
    {
      "slug": "rtx-pro-6000-blackwell",
      "month": "2025-08",
      "extracted": "4090, RTX Pro 6000",
      "message": "Hm, you're doing 150-190 tok/s on a 4090 with llama.cpp? Wonder if I'm missing some compilation flags, I get around 180-190 on a RTX Pro 6000 currently"
    },
    {
      "slug": "rtx-pro-6000-blackwell",
      "month": "2025-09",
      "extracted": "4 x RTX PRO 6000s",
      "message": "btw, some of you guys might appreciate this. here's some vllm-bench/sharegpt benchmarks of what throughput looks like for llama3-8b w/ 4 x RTX PRO 6000s - at that rate you can generate about 1.3B tokens/day"
    },
    {
      "slug": "rtx-pro-6000-blackwell",
      "month": "2025-09",
      "extracted": "4 x RTX PRO 6000s",
      "message": "4 x RTX PRO 6000s\n\nwe just need to wait 10 years till they become obsolette and get cheap"
    },
    {
      "slug": "rtx-pro-6000-blackwell",
      "month": "2025-09",
      "extracted": "RTX Pro 6000",
      "message": "Peer to peer communication which the RTX Pro 6000 can do"
    },
    {
      "slug": "rtx-pro-6000-blackwell",
      "month": "2025-10",
      "extracted": "2 h200, 4x rtx 6000 pros, 5tb/s, 600gb/s bandwidth system ram",
      "message": "Btw, wouldnt you have been better off with 2 h200's instead?\n\nhalf the power consumption of 4x rtx 6000 pros\nyou only need to fit 2 gpus\n2.5x as much bandwidth (5tb/s) as blackwell rtx pro 6000 (1.9tb/s)\nsame amount of vram\n\nPretty much enables you to utilize an sp5 board like th\u2026"
    },
    {
      "slug": "rtx-pro-6000-blackwell",
      "month": "2025-10",
      "extracted": "RTX 6000 Ada; RTX Pro 6000 Blackwell",
      "message": "It's interesting that if you have a very compute bound workflow where you can fit everything in the 96MB or 128MB L2-cache:\n\n https://www.techpowerup.com/gpu-specs/rtx-6000-ada-generation.c3933 \n\n https://www.techpowerup.com/gpu-specs/rtx-pro-6000-blackwell.c4272 \n\nthen the perfo\u2026"
    },
    {
      "slug": "m5",
      "month": "2025-09",
      "extracted": "m5 mac",
      "message": "upcoming m5 mac with the matmul accelerators? What is everybody thinking"
    },
    {
      "slug": "m5",
      "month": "2025-09",
      "extracted": "vram",
      "message": "Once the m5 with possible native matmul arrives, it\u2019ll be interesting to see how that shifts the landscape. Macs have always had stupid amounts of vram but lack speed. Add some speed to the mix and things get fun."
    },
    {
      "slug": "m5",
      "month": "2025-09",
      "extracted": "Mac minis, Mac studios, M5",
      "message": "after looking at mac minis/mac studios, just heard about the M5 matmul rumors around the corner... ugh okay I'll wait for october/november"
    },
    {
      "slug": "m5",
      "month": "2025-09",
      "extracted": "M5 Macs",
      "message": "from what I've heard, M5 Macs will not be coming until early next year and big performance jump won't happen until M6 when they shrink to 2nm process"
    },
    {
      "slug": "m5",
      "month": "2025-10",
      "extracted": "celastiel igpus, m5",
      "message": "intel is coming up with celastiel igpus soon and apple is also releasing m5 this year"
    },
    {
      "slug": "m5",
      "month": "2025-10",
      "extracted": "M5",
      "message": "you can also wait for M5"
    }
  ]
} as const;

function slugLabel(slug: string): string {
  return slug.replace(/-/g, " ").replace(/\b(rtx|rx|dgx|gb10)\b/gi, (m) => m.toUpperCase());
}

export default function HwSpeedSetups() {
  return (
    <Stack gap={16}>
      <Stack gap={4}>
        <H1>Hardware, speed &amp; setup benchmarks</H1>
        <Text tone="secondary">
          Source: LocalLLM Discord hardware/speed/quantization categories · Jul 2025 – Jul 2026 ·
          Match: scan full message + LLM extracted field against registry aliases (longest alias
          wins per slug)
        </Text>
      </Stack>

      <Row gap={12} wrap>
        <Stat label="Hardware mentions" value={String(HW_DATA.meta.messages)} />
        <Stat label="Registry-matched" value={String(HW_DATA.meta.mapped)} tone="info" />
        <Stat label="Speed mentions" value={String(SPEED_DATA.meta.messages)} />
        <Stat label="Numeric speed reports" value={String(SPEED_DATA.meta.with_metrics)} tone="success" />
        <Stat label="Full setups (4-way)" value={String(SETUP_DATA.count)} tone="warning" />
      </Row>

      <Card>
        <CardHeader>Top hardware by month (registry slugs)</CardHeader>
        <CardBody>
          <BarChart
            categories={[...HW_DATA.monthLabels]}
            series={HW_DATA.slugs.map((slug) => ({
              name: slugLabel(slug),
              data: [...HW_DATA.matrix[HW_DATA.slugs.indexOf(slug)]],
            }))}
            stacked
            height={320}
          />
          <Text tone="tertiary" size="small" style={{ marginTop: 8 }}>
            Y-axis: mention count · X-axis: month · Top {HW_DATA.slugs.length} specific GPUs/platforms
            (excludes generic vram/ram/cpu)
          </Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={12}>
        {HW_DATA.slugs.slice(0, 8).map((slug, rowIdx) => (
          <Card>
            <CardHeader
              trailing={
                <Text tone="secondary" size="small">
                  {HW_DATA.slugTotals[rowIdx]} total
                </Text>
              }
            >
              {slugLabel(slug)}
            </CardHeader>
            <CardBody>
              <BarChart
                categories={[...HW_DATA.monthLabels]}
                series={[{ name: "Mentions", data: [...HW_DATA.matrix[rowIdx]] }]}
                height={160}
              />
            </CardBody>
          </Card>
        ))}
      </Grid>

      <Card>
        <CardHeader>Sample hardware messages (with full text)</CardHeader>
        <CardBody>
          <Table
            headers={["Slug", "Month", "Extracted", "Message"]}
            rows={HW_MSG_DATA.rows.map((row) => [
              slugLabel(row.slug),
              row.month.slice(0, 7),
              row.extracted,
              row.message,
            ])}
            striped
            stickyHeader
          />
          <Text tone="tertiary" size="small" style={{ marginTop: 8 }}>
            Full messages in hardware-parsed.json · Samples from top hardware slugs
          </Text>
        </CardBody>
      </Card>

      <Divider />

      <Stack gap={4}>
        <H2>Speed metrics over time</H2>
        <Text tone="secondary">
          Parsed tok/s and TTFT from speed-category messages · Median per month ·{" "}
          {SPEED_DATA.meta.tps_values.toLocaleString()} tok/s data points ·{" "}
          {SPEED_DATA.meta.ttft_values} TTFT data points
        </Text>
      </Stack>

      <Card>
        <CardHeader>Median tokens/sec by month</CardHeader>
        <CardBody>
          <LineChart
            categories={[...SPEED_DATA.monthLabels]}
            series={[
              { name: "Median tok/s", data: [...SPEED_DATA.tpsMedian], tone: "info" },
              { name: "Report count", data: [...SPEED_DATA.tpsCount], tone: "neutral" },
            ]}
            height={260}
          />
          <Text tone="tertiary" size="small" style={{ marginTop: 8 }}>
            Y-axis: tok/s (left series) or count (right series) · Overall median:{" "}
            {SPEED_DATA.meta.overall_tps_median} tok/s · Outlier-heavy months skew the mean; median
            is shown
          </Text>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>Median TTFT by month (ms)</CardHeader>
        <CardBody>
          <LineChart
            categories={[...SPEED_DATA.monthLabels]}
            series={[
              {
                name: "Median TTFT (ms)",
                data: [...SPEED_DATA.ttftMedianMs],
                tone: "warning",
              },
              { name: "TTFT reports", data: [...SPEED_DATA.ttftCount], tone: "neutral" },
            ]}
            beginAtZero={false}
            height={220}
          />
          <Text tone="tertiary" size="small" style={{ marginTop: 8 }}>
            Y-axis: milliseconds to first token · Sparse data — only months with explicit TTFT/latency
            numbers are non-zero
          </Text>
        </CardBody>
      </Card>

      <Divider />

      <Stack gap={4}>
        <H2>Setup lists (case-by-case)</H2>
        <Text tone="secondary">
          Expanded detection: category tags + full-message scan for tok/s, t/s, TTFT, and registry
          hardware · {SETUP_DATA.count} setups · Showing {SETUP_DATA.setups.length} newest rows
        </Text>
      </Stack>

      <Card>
        <CardHeader>Full benchmark setups</CardHeader>
        <CardBody>
          <Table
            headers={["Month", "Tier", "Model", "Hardware", "Quant", "Speed", "Message"]}
            rows={SETUP_DATA.setups.map((row) => [
              row.month.slice(0, 7),
              row.tier,
              row.model,
              row.hardware,
              row.quantization,
              row.speed,
              row.message,
            ])}
            striped
            stickyHeader
          />
          <Text tone="tertiary" size="small" style={{ marginTop: 8 }}>
            Message column: full Discord text · Complete export in setup-lists.json
          </Text>
        </CardBody>
      </Card>
    </Stack>
  );
}
