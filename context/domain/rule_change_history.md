## Rule change history - AML

What changed, when, and what stops being comparable.

### AML line-of-therapy exception — Mar'26

> "Exception: Don't change the LoT if the gap b/w regimens is <= 90 days, and backbone switch in
> consideration is VEN <-> HMA. Within the same line, consolidate all regimens"

The slide annotates this "New rule (Mar'26)".
*(AML SHA Business Rules Guide V5.pptx · slide 14)*

**Comparability.** An AML line distribution crossing Mar'26 mixes two methods. Before the change a
VEN-to-HMA switch within 90 days advanced the line; after it, it does not.

### AML base layer — 2026 business-rule change

The current AML base-layer notebooks (`scripts/Notebooks/`; validation build May'26,
tables `..._BUSINESS_RULE_CHANGE_VAL_v2`; Aug'26 build, tables `..._BUSINESS_RULE_CHANGE_VAL`) change the
following relative to the V5 rules guide. Each is marked in code as "Changes Made".

1. **Patient pool.** The patient indication filter (diagnosis frequency, recency and hierarchy) was
   removed. The `_v2` build uses 2+ AML diagnosis claims instead; the Aug'26 build uses
   `market_code='VENC_AML'`.
2. **Backbone hierarchies.** RYDAPT and MYLOTARG were removed from the IC-Ineligible hierarchy (13 → 11
   products). INQOVI and ONUREG resolve to the generic `HMA` backbone in both hierarchies. In IC
   Eligible, S-DAC and HI-DAC are grouped as `S-DAC/HI-DAC`.
3. **Intensity (legacy rule).** INQOVI and ONUREG became IC-Ineligible products. RYDAPT and MYLOTARG are
   IC-Eligible only; the Rydapt/Mylotarg + VEN/HMA exception was dropped.
4. **VEN ↔ HMA exception scope.** Because Inqovi and Onureg are now `HMA`, the Mar'26 exception also
   covers Venclexta ↔ Inqovi and Venclexta ↔ Onureg.
5. **Regimen consolidation removed.** Short regimens (< 28 days, subset of a neighbour, no gap) are no
   longer folded into major regimens, and the minimum-length filter (≥ 28 days; Rydapt ≥ 14) is gone.
   More line changes surface.
6. **Grace.** INQOVI grace is 28 days (V5 workbook: 60).
7. **New outputs.** These are the new definition age-and-product intensity, VEN-anchored
   eligibility flags, SCT and timing flags, the LoT regimen grouping table, and the AML HCP
   affiliations table.

**Comparability.** AML line, backbone, intensity and NPS-by-line figures built before this change are
not comparable with figures from the new tables. The cohort itself differs by build (57,697 vs 84,199
patients). State `AML_LOT_RULE_VERSION` and the table suffix, and flag any trend that crosses the
change (flag it; never present it as a clean trend). If new definition is adopted later, each side of the cutover must say which rule produced it.

### FDA approval floors on line-of-therapy cuts

Not a rule change, but a hard boundary on the data: `aml_lot_group` is "Null before Jan 2019 (FDA approval
floor)". A line-based trend cannot extend before those dates.
