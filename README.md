# hardwarelist

Crowdsourced local-LLM hardware setups (GPU + model + quant + speed) extracted from the LocalLLM Discord.

## Layout

```
hardwarelist/
  hardware_registry.txt      # GPU slug/alias registry
  model_registry.txt
  quantization_registry.txt
  data/                      # Project outputs + classified hardware messages
  output/                    # HTML lists (locallist.html, localllmsetuplist.html)
  canvases/                  # Review canvases + liked picks
  scripts/                   # Build / rollup / HTML generators
```

Upstream Discord monthly exports and classifier category folders are still read from the sibling repo:

`../discorddata/jsonstrimmed/localllmbymonth/`

Override with `DISCORDDATA_ROOT=/path/to/discorddata` if needed.

## Common commands

```bash
# Rebuild setups from Discord classifications
python3 scripts/build_setup_lists.py

# Roll up hardware mentions by GPU slug
python3 scripts/build_hardware_rollup.py

# Build HTML lists from liked canvas picks
python3 scripts/build_locallist_html.py
python3 scripts/build_localllm_setup_list_html.py

# eBay recently-sold prices (Chrome profile under .ebay-profile/)
# Sold comps usually require an eBay login first:
python3 scripts/scrape_ebay_sold.py --login
python3 scripts/scrape_ebay_sold.py
python3 scripts/build_locallist_html.py   # refresh price fields from data/ebay-prices.json
```
