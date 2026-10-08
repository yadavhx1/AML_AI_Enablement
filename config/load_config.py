"""Load the AML base-layer notebook parameters.

Usage in a notebook (replaces the hardcoded GLOBAL VARIABLES cell):

    from load_config import load_config
    cfg = load_config("eligibility.yaml")        # common.yaml + the notebook file, notebook wins
    tx_tbl_final_name = cfg["tables"]["tx_tbl_final_name"]
    aml_dx_full = cfg["codes"]["aml_dx_full"]
    spark.sql(f"... WHERE SOURCE_DIAGNOSIS_CODE_1 IN ({sql_list(aml_dx_full)}) ...")

`{cws}` and `{suffix}` in table names and `codes.*` / `products.*` / `tables.*` / `schemas.*` reference
strings are resolved on load.
"""
from copy import deepcopy
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent


def _merge(base, override):
    out = deepcopy(base)
    for k, v in (override or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _resolve(node, cfg, fmt):
    if isinstance(node, dict):
        return {k: _resolve(v, cfg, fmt) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, cfg, fmt) for v in node]
    if isinstance(node, str):
        head = node.split(".", 1)[0]
        if head in ("codes", "products", "tables", "schemas") and "." in node and " " not in node:
            ref = cfg
            for part in node.split("."):
                if not isinstance(ref, dict) or part not in ref:
                    return node
                ref = ref[part]
            return _resolve(ref, cfg, fmt)
        if "{cws}" in node or "{suffix}" in node:
            return node.replace("{cws}", fmt["cws"]).replace("{suffix}", fmt["suffix"])
    return node


def load_config(notebook_file=None, overrides=None):
    """Return common.yaml merged with `notebook_file` and then `overrides` (dict), fully resolved."""
    cfg = yaml.safe_load((CONFIG_DIR / "common.yaml").read_text(encoding="utf-8"))
    if notebook_file:
        cfg = _merge(cfg, yaml.safe_load((CONFIG_DIR / notebook_file).read_text(encoding="utf-8")))
    cfg = _merge(cfg, overrides)
    fmt = {"cws": cfg["schemas"]["cws"], "suffix": cfg["run"]["build_suffix"]}
    return _resolve(cfg, cfg, fmt)


def sql_list(values):
    """Render a Python list as a SQL IN-list body: 'A', 'B', 'C'."""
    return ", ".join("'" + str(v).replace("'", "''") + "'" for v in values)


def case_map(column, mapping, else_value="NULL"):
    """Render {product: value} as CASE WHEN column IN (...) THEN value ... END, grouping equal values."""
    by_value = {}
    for k, v in mapping.items():
        by_value.setdefault(v, []).append(k)
    whens = "\n".join(f"    WHEN {column} IN ({sql_list(ks)}) THEN {v}" for v, ks in by_value.items())
    return f"CASE\n{whens}\n    ELSE {else_value}\nEND"


def backbone_case(hierarchy, operator="LIKE", column="REGIMEN"):
    """Render an ordered [[patterns], value] hierarchy as the backbone CASE (first match wins)."""
    whens = []
    for patterns, value in hierarchy:
        if operator.upper() == "RLIKE":
            cond = " OR ".join(f"{column} RLIKE '{p}'" for p in patterns)
        else:
            cond = " OR ".join(f"{column} LIKE '%{p}%'" for p in patterns)
        whens.append(f"    WHEN {cond} THEN '{value}'")
    return "CASE\n" + "\n".join(whens) + "\n    ELSE NULL\nEND"
