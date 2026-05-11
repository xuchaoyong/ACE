# HEDEx CLI Manual Extractor — Run Report

This report records a local execution of `bin/nassim_cli_manual_extractor.py`
against the live Huawei HEDEx command manual at:

```
https://support.huawei.com/hedex/hdx.do?docid=EDOC1100218869&tocURL=resources/hedex-homepage.html
```

The script implements the NAssim-style assimilation idea: walk the HEDEx
navigation tree, fetch each command's HTML topic, and emit structured JSON
fields (`PageTitle`, `FuncDef`, `CLIs`, `ParentView`, `ParaDef`, `Examples`,
`ExtraInfo`).

## 1. Environment

| Item       | Value                                                |
| ---------- | ---------------------------------------------------- |
| OS         | Linux 6.12.58+ x86_64 GNU/Linux                      |
| Python     | 3.12.3 (system, no extra dependencies)               |
| Run dir    | `/tmp/nassim-local`                                  |
| Output dir | `/tmp/nassim-local/outputs`                          |
| Doc target | `EDOC1100218869` (NE40E V800R021C00SPC100, lib `AEK1025J` v03) |

Only Python 3 standard library is used (`urllib`, `html.parser`, `json`,
`argparse`); no third-party packages need to be installed.

## 2. Local setup ("download" step)

The script lives in the repo as `bin/nassim_cli_manual_extractor.py`. For a
clean local run, it is copied into a dedicated working directory:

```bash
mkdir -p /tmp/nassim-local/outputs
cp bin/nassim_cli_manual_extractor.py /tmp/nassim-local/
chmod +x /tmp/nassim-local/nassim_cli_manual_extractor.py
python3 -m py_compile /tmp/nassim-local/nassim_cli_manual_extractor.py
```

Compilation: `COMPILE_OK` (no syntax errors).

`--help` reports the supported options:

- `--url` — HEDEx entry URL containing `docid=...`
- `--command` — command title to locate in the navigation tree (e.g. `8021p-inbound`)
- `--topic-url` — direct HEDEx topic URL
- `--all` — extract every command leaf below the selected root
- `--root-position` — navigation position to start from (e.g. `8.1.6.14.3`)
- `--limit`, `--max-search-nodes`, `--sleep`
- `--output`, `--no-source`, `--compact`

## 3. Runs

Each run was timed with `date +%s.%N` before and after the Python process.
All runs used `--no-source` so the output contains only the NAssim-style
fields.

### Run 1 — single command by name

```bash
python3 nassim_cli_manual_extractor.py \
  --url "$URL" \
  --command 8021p-inbound \
  --root-position 8.1.6.14.3 \
  --no-source \
  -o outputs/8021p-inbound.json
```

| Metric        | Value                                  |
| ------------- | -------------------------------------- |
| Exit code     | 0                                      |
| Duration      | 1.733 s                                |
| Output bytes  | 2 637                                  |
| Output sha256 | `bdc3af233d6b547b…`                    |
| Shape         | single object                          |
| Title         | `8021p-inbound`                        |
| CLIs / Params / Views / Examples | 2 / 3 / 1 / 1       |
| ExtraInfo chars | 1 238                                |

### Run 2 — single command by topic URL

```bash
python3 nassim_cli_manual_extractor.py \
  --url "$URL" \
  --topic-url resources/command/8090/8021P-OUTBOUND.html \
  --no-source \
  -o outputs/8021p-outbound.json
```

| Metric        | Value               |
| ------------- | ------------------- |
| Exit code     | 0                   |
| Duration      | 1.146 s             |
| Output bytes  | 2 417               |
| Output sha256 | `49b076721cf59d8a…` |
| Title         | `8021p-outbound`    |
| CLIs / Params / Views / Examples | 2 / 3 / 1 / 1 |

### Run 3 — another single command by topic URL

```bash
python3 nassim_cli_manual_extractor.py \
  --url "$URL" \
  --topic-url resources/command/8090/DIFFSERV_DOMAIN.html \
  --no-source \
  -o outputs/diffserv-domain.json
```

| Metric        | Value               |
| ------------- | ------------------- |
| Exit code     | 0                   |
| Duration      | 1.131 s             |
| Output bytes  | 2 595               |
| Output sha256 | `bdb4e5164cb8e5cd…` |
| Title         | `diffserv domain`   |
| CLIs / Params / Views / Examples | 3 / 4 / 1 / 1 |

### Run 4 — batch extract under a navigation root

```bash
python3 nassim_cli_manual_extractor.py \
  --url "$URL" \
  --all \
  --root-position 8.1.6.14.5 \
  --sleep 0.2 \
  --no-source \
  -o outputs/last-mile-qos.json
```

| Metric        | Value               |
| ------------- | ------------------- |
| Exit code     | 0                   |
| Duration      | 4.607 s             |
| Output bytes  | 15 052              |
| Output sha256 | `f14178ffaa070fbb…` |
| Shape         | JSON list of 7 commands |

Extracted commands (Last Mile QoS Configuration Commands):

| Title | CLIs | Params | ParentView |
| --- | --- | --- | --- |
| `display qos link-adjustment configuration` | 1 | 3 | All views |
| `qos link-adjustment link-layer-exclude l2tp-layer-exclude` | 4 | 3 | System view |
| `qos link-adjustment remote` | 2 | 1 | Interface view |
| `qos link-adjustment remote enable` | 2 | 0 | AAA domain view |
| `qos link-adjustment remote(aaa domain view)` | 2 | 1 | AAA domain view |
| `qos link-adjustment shaping-mode` | 2 | 2 | AAA domain view, Eth-Trunk interface view, GE electrical interface view |
| `qos link-adjustment vendor` | 2 | 3 | System view |

## 4. Sample structured output

Excerpt of `outputs/8021p-inbound.json`:

```json
{
  "PageTitle": "8021p-inbound",
  "FuncDef": "The 8021p-inbound command maps 802.1p values of upstream VLAN packets in a DiffServ (DS) domain to internal classes of service (CoSs) and colors the packets.\n\nThe undo 8021p-inbound command restores the default mapping relationships from 802.1p values to internal CoSs.\n\nBy default, the mappings between 802.1p values and CoSs are displayed as Table 1.",
  "CLIs": [
    "8021p-inbound <8021p-value> phb <service-class> [ <color> ]",
    "undo 8021p-inbound [ <8021p-value> ]"
  ],
  "ParentView": [
    "DiffServ domain view"
  ],
  "ParaDef": [
    { "Parameters": "8021p-value", "Info": "Specifies the 802.1p value of VLAN packets.\nThe value is an integer ranging from 0 to 7." },
    { "Parameters": "phb service-class", "Info": "Specifies the CoS value.\nThe value is an enumerated type and can be case-insensitive EF, AF1, AF2, AF3, AF4, BE, CS6, or CS7." },
    { "Parameters": "color", "Info": "Specifies the color used to mark the packets.\nThe value can be green, yellow, or red. By default, the packets are colored green." }
  ],
  "Examples": [
    [
      "<HUAWEI> system-view",
      "[~HUAWEI] diffserv domain test",
      "[*HUAWEI-dsdomain-test] 8021p-inbound 2 phb af1 green"
    ]
  ],
  "ExtraInfo": "Usage Scenario\n\nTo implement QoS scheduling on the upstream VLAN packets, ..."
}
```

## 5. Comparison with the requested schema

The original schema in the task definition is matched field-by-field:

| Field        | Requested | Run 1 result |
| ------------ | --------- | ------------ |
| `PageTitle`  | `8021p-inbound` | identical |
| `FuncDef`    | 3-paragraph definition | identical wording (paragraphs joined with `\n\n`) |
| `CLIs`       | 2 command syntax lines, `<>` for variables, `[ ]` for optional | identical |
| `ParentView` | `["DiffServ domain view"]` | identical |
| `ParaDef`    | 3 entries (`8021p-value`, `phb service-class`, `color`) | identical |
| `Examples`   | 3 CLI lines | identical, preserved as separate list elements |
| `ExtraInfo`  | Usage Scenario + default mapping table + Configuration Impact + Precautions | identical content; section headings preserved |

## 6. Summary

- The HEDEx CLI manual extractor runs end-to-end with only the Python 3
  standard library against the live Huawei support site.
- Per-command latency is ~1.1 s for direct topic URLs and ~1.7 s when the
  command must first be resolved by name through the navigation tree.
- Batch extraction over 7 commands completes in ~4.6 s with a 200 ms
  inter-request delay.
- All four sample outputs match the requested NAssim-style schema.

To reproduce on any machine with Python 3.8+ and outbound HTTPS to
`support.huawei.com`:

```bash
git checkout cursor/nassim-cli-manual-extractor-b13b
python3 bin/nassim_cli_manual_extractor.py \
  --url 'https://support.huawei.com/hedex/hdx.do?docid=EDOC1100218869&tocURL=resources/hedex-homepage.html' \
  --command 8021p-inbound \
  --root-position 8.1.6.14.3 \
  --no-source \
  -o 8021p-inbound.json
```
