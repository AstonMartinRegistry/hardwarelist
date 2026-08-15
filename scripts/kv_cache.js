/**
 * Exact KV cache size from Hugging Face text_config (same formula as the
 * old build_locallist_html.py):
 *
 *   KV (bytes) = 2 × L × N_kv × d_head × N_ctx × B_element
 *
 * For hybrid Qwen3.5/3.6/3.8, L = count of `full_attention` layers only
 * (linear_attention / DeltaNet does not use this dense KV form).
 *
 * B_element: f16/bf16=2, q8_0=1, q4≈0.5, etc.
 */
const fs = require('fs');
const path = require('path');

function loadHfTextConfig(relOrAbs) {
  const p = path.isAbsolute(relOrAbs)
    ? relOrAbs
    : path.join(__dirname, '..', relOrAbs);
  const cfg = JSON.parse(fs.readFileSync(p, 'utf8'));
  return cfg.text_config || cfg;
}

function kvCacheFromHf(textCfg, ctx, elementBytes) {
  const layers = textCfg.layer_types || [];
  const nLayers = layers.length
    ? layers.filter((t) => t === 'full_attention').length
    : Number(textCfg.num_hidden_layers || 0);
  const nKv = Number(textCfg.num_key_value_heads || 0);
  let headDim = textCfg.head_dim;
  if (headDim == null) {
    const hidden = Number(textCfg.hidden_size || 0);
    const nHeads = Number(textCfg.num_attention_heads || 1);
    headDim = hidden / nHeads;
  }
  headDim = Number(headDim);
  const raw =
    2 * nLayers * nKv * headDim * Number(ctx) * Number(elementBytes);
  return {
    bytes: raw,
    gib: raw / 1024 ** 3,
    gb: raw / 1e9,
    n_layers: nLayers,
    n_kv: nKv,
    head_dim: headDim,
    ctx: Number(ctx),
    element_bytes: Number(elementBytes),
    title:
      `KV = 2×${nLayers}L×${nKv}kv×${headDim}d×${ctx}ctx×${elementBytes}B` +
      ` = ${(raw / 1024 ** 3).toPrecision(4)} GiB` +
      ' (full_attention layers from HF config)',
  };
}

/** Round for display on cards (match historical HTML: often 1–2 decimals). */
function roundKvGib(gib) {
  if (!Number.isFinite(gib)) return null;
  if (gib >= 10) return Math.round(gib * 10) / 10;
  return Math.round(gib * 100) / 100;
}

function kvElementBytesFromCacheType(cacheType) {
  const t = String(cacheType || 'f16').toLowerCase();
  if (t === 'f16' || t === 'fp16' || t === 'bf16' || t === 'bfloat16') return 2;
  if (t === 'q8' || t === 'q8_0' || t === 'q8_1') return 1;
  if (t === 'q4' || t === 'q4_0' || t === 'q4_1') return 0.5;
  if (t === 'f32' || t === 'fp32') return 4;
  const n = Number(cacheType);
  return Number.isFinite(n) ? n : 2;
}

module.exports = {
  loadHfTextConfig,
  kvCacheFromHf,
  roundKvGib,
  kvElementBytesFromCacheType,
};
