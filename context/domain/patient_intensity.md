# Patient intensity (IC Eligible / IC Ineligible)

**Definition id:** `patient_intensity`
**Aliases:** IC Elig, IC Inelig, IC_ELIG, IC_INELIG, intensity, TYPE, PATIENT_INTENSITY_GROUP, PATIENT_COHORT, legacy rule, new definition, age + product, PATIENT_INTENSITY_UPDATED, PATIENT_COHORT_UPDATED
**Working behavior:** Use the legacy rule everywhere unless the user explicitly asks for the new definition.

## Definition
Whether a patient is treated as intensive-chemotherapy eligible. It decides which backbone hierarchy
applies, and it is made once per patient.

## Calculation
```text
Legacy rule (production, default):
    IC_ELIG if any regimen in the journey contains an IC-Eligible-only product
    (ARSENIC_TRIOXIDE, CLADRIBINE, CLOFARABINE, CYCLOPHOSPHAMIDE, S-DAC, HI-DAC, DAUNORUBICIN, ETOPOSIDE,
     FLUDARABINE, IDARUBICIN, MITOXANTRONE, MYLOTARG, NEXAVAR, RYDAPT, VANFLYTA, VINCRISTINE, VYXEOS);
    else IC_INELIG.

New definition (age + product), on the legacy line-1 product group:
    any IC-Eligible product -> IC_ELIG;
    all products in {AZACITIDINE, DECITABINE, ONUREG, INQOVI, TIBSOVO, IDHIFA} -> IC_INELIG;
    else age (YEAR(FIRST_DX) - birth year) <= 65 -> IC_ELIG, > 65 -> IC_INELIG;
    no age -> IC_INELIG.
```

## Grain and dimensions
One row per patient

## Source tables
- Legacy rule: `MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_*` (`PATIENT_INTENSITY_GROUP`); `TYPE` on the
  combined LoT; `PATIENT_COHORT` on the flags table.
- New definition: `PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT_*` (`PATIENT_INTENSITY_UPDATED`);
  `PATIENT_COHORT_UPDATED` on the flags table.
- Lines built with the new definition: the `_NEWDEF` tables of a run with
  `run.intensity_definition: new` (`config/common.yaml`).
  - The cohort table there keeps the legacy class in `PATIENT_INTENSITY_GROUP_LEGACY`.
  - `PATIENT_INTENSITY_GROUP` holds the new class; patients with no line-1 group keep their legacy
    class.

## Caveats
- May'26 legacy split: 43,194 IC_INELIG / 14,503 IC_ELIG (57,697).
- Never mix the two definitions in one trend.
- The new definition is line-1-only, which is narrower than the business-rules page wording. The
  page's wording for the legacy rule ("even one IC-ELIG-only product at any point in their journey")
  matches the code.
- **Classes vs lines.** In a legacy build, `PATIENT_INTENSITY_UPDATED` is a new-definition class
  attached to legacy-rule lines. Only a new-definition run rebuilds the lines (backbone hierarchy and
  line changes) with the new classes.

## Source lineage
- scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb
- config/intensity_definition.py (definition switch)
