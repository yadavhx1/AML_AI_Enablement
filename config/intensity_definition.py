"""IC Eligible / IC Ineligible definition switch for the AML base layer.

Two definitions classify each patient as IC_ELIG or IC_INELIG:

  legacy  Product-only (production). IC_ELIG if any regimen in the patient's journey contains an
          IC-Eligible-only product, otherwise IC_INELIG. Decided once for the whole journey.
          Table: MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_* (PATIENT_INTENSITY_GROUP).

  new     Age + product. Classified on the patient's LEGACY line-1 product group:
          any IC-Eligible product -> IC_ELIG; every product in the forced-ineligible set (HMAs, Tibsovo,
          Idhifa) -> IC_INELIG; otherwise age at first diagnosis <= 65 -> IC_ELIG, > 65 -> IC_INELIG;
          no age -> IC_INELIG. Table: PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT_* (PATIENT_INTENSITY_UPDATED).

`run.intensity_definition` in config/common.yaml selects the definition (default `legacy`).

How a `new` run works (AML_LOT_PATIENT_INTENSITY_LOT):
  pass 1  build lines with the legacy definition into scratch tables, exactly as before;
  classify each patient with the new definition from that legacy line-1 group (the code's original
          classification step);
  pass 2  rebuild the IC_ELIG / IC_INELIG lines, the combined LoT table and the LoT grouping using
          the new classes. Outputs carry run.new_definition_tag, so legacy tables are never overwritten.

Downstream notebooks call resolve() with the same config, so eligibility (PATIENT_COHORT) and the NPS
dashboard read the tables and intensity column of the chosen definition.
"""

DEFINITIONS = ("legacy", "new")

# Tables whose content depends on the intensity definition. A new-definition run writes these with the tag.
DEFINITION_DEPENDENT_TABLES = (
    "patient_group",            # cohort: legacy class (pass 1 copy in a new run)
    "ic_inelig_final",
    "ic_elig_final",
    "pat_comb_lot",
    "lot_regimen_group",
    "patient_intensity_based_on_age_n_product",
)

# Eligibility outputs that depend on the definition: PATIENT_COHORT and everything built from the
# combined LoT (first/last treatment, continuity flags, arsenic, flags table).
ELIGIBILITY_DEPENDENT_TABLES = (
    "pat_fst_dx_tx", "dx_lookback_elig", "tx_txl_mx_elig", "tx_txl_rx_elig",
    "tx_lookback_elig_ven", "tx_lookback_elig_rx_ven", "tx_txl_mx_elig_ven", "tx_txl_rx_elig_ven",
    "elig_flags_final",
)


def definition(cfg):
    """Return 'legacy' or 'new' from a loaded config; anything else raises ValueError."""
    value = (cfg.get("run") or {}).get("intensity_definition", "legacy")
    if value not in DEFINITIONS:
        raise ValueError(f"Unsupported run.intensity_definition {value!r}; use one of {DEFINITIONS}")
    return value


def tag(cfg):
    """'' for legacy; run.new_definition_tag (default '_NEWDEF') for new."""
    return "" if definition(cfg) == "legacy" else (cfg.get("run") or {}).get("new_definition_tag", "_NEWDEF")


def table(cfg, key, base=None):
    """Definition-aware table name: the configured name (or `base`), tagged in a new-definition run."""
    name = base if base is not None else cfg["tables"][key]
    return name + tag(cfg)


def tables(cfg, keys=DEFINITION_DEPENDENT_TABLES):
    return {k: table(cfg, k) for k in keys if k in cfg.get("tables", {})}


def scratch(name):
    """Pass-1 (legacy) scratch name used inside a new-definition LoT run."""
    return name + "_P1LEGACY"


def intensity_column(cfg):
    """Column holding the patient class for the chosen definition, and the table it lives in."""
    if definition(cfg) == "legacy":
        return "PATIENT_INTENSITY_GROUP", table(cfg, "patient_group")
    return "PATIENT_INTENSITY_UPDATED", table(cfg, "patient_intensity_based_on_age_n_product")


def label(cfg):
    return ("legacy rule (product-only)" if definition(cfg) == "legacy"
            else "new definition (age + product)")
