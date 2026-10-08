## Reference data - AML base layer

Reproduced exactly as written, including duplicates; cleaning a code list silently changes every result.

### AML diagnosis codes

The full 37-code list, from the workbook embedded in the AML rules guide:

```
205, 205.0, 205.00, 205.01, 205.02, C92, C92.0, C92.00, C92.01, C92.02, C92.5, C92.50,
C92.51, C92.52, C92.6, C92.60, C92.61, C92.62, C92.9, C92.90, C92.A, C92.A0, C92.A1,
C92.A2, C92.Z0, C93, C93.0, C93.00, C93.01, C93.02, C94.0, C94.00, C94.01, C94.2,
C94.20, C94.21, C94.22
```
*(AML SHA Business Rules Guide V5.pptx · embedded workbook 'Codes' · AML Dx Codes)*

**Used by the AML base layer** (`AML_LOT_VAL.ipynb` cell 7; `Patient Eligibility.ipynb` cell 129): the
same 37 codes, read from `abv_val_ptd_onc_synd.dx_fact_curated_vw.SOURCE_DIAGNOSIS_CODE_1`, for the
2+-claim patient pool (`COUNT(DISTINCT mx_claim_id) > 1`, `source_flag='SHA_PTD'`) and for `FIRST_DX`
(MIN claim date, no source filter).

**AML relapse/remission ("RR") codes - 13** (`aml_dx` global, "RR AML DX ONLY"): `C92.01, C92.02,
C92.51, C92.52, C92.61, C92.62, C92.A1, C92.A2, C93.01, C93.02, C94.01, C94.21, C94.22`. These are the
"without remission / in remission" ICD-10 subtypes. They drive the 1L -> 2L+ promotion in
`MABI_AML_PATS_LOT_RR_12M_UPD_*` (see `key_concepts.md`). The business-rules page shows these 13 as
its "AML diagnosis codes" chips. The pool and FIRST_DX do not use them; they use the 37-code set.

**ICD-9 legacy codes shown on the business-rules page (7)** (current revision, Section 03, with its
mapping to ICD-10):

| ICD-9 | Page description | ICD-10 it covers |
|---|---|---|
| 205.00 | Myeloid leukemia, acute, without remission | C92.01 / C92.61 / C92.A1 |
| 205.01 | Myeloid leukemia, acute, in remission | "in remission" side of the same C92 codes |
| 206.00 | Monocytic leukemia, acute, without remission | C92.51, C93.01 |
| 206.01 | Monocytic leukemia, acute, in remission | C92.52, C93.02 |
| 207.00 | Acute erythremia and erythroleukemia | C94.01 |
| 207.20 | Megakaryocytic leukemia, without remission | C94.21 |
| 207.21 | Megakaryocytic leukemia, in remission | C94.22 |

**The code does not use 206.x or 207.x.** The 37-code pool/FIRST_DX set carries ICD-9 205, 205.0,
205.00, 205.01 and 205.02 only. A pre-ICD-10 (before Oct 2015) patient coded only as 206.0x or 207.x is
therefore not in the pool and has no FIRST_DX. Treat the page's ICD-9 list as a crosswalk, not the
code's set (open item OI-14).

The guide's own slide shows a subset with descriptions: 205 Myeloid Leukemia · 205.0 Myeloid Leukemia
(Acute) · 205.00 Acute myeloid leukemia, without mention of having achieved remission · 205.01 Acute
myeloid leukemia, in remission · 205.02 Acute myeloid leukemia, in relapse · C92 Myeloid leukemia and
various subtypes · C92.9 Unspecified myeloid leukemia · C93 Monocytic leukemia · C94 Acute erythroid
leukemia · C94.2 Acute megakaryoblastic leukemia. *(same deck · slide 7)*

The GPO competitor query uses a slightly different AML set (it omits C92.A1, C92.A2 and adds C94.0x
variants differently); reproduced as written:

```
'205','205.00','205.0','205.01','205.02','C92','C92.0','C92.00','C92.01','C92.02','C92.5',
'C92.50','C92.51','C92.52','C92.6','C92.60','C92.61','C92.62','C92.9','C92.90','C92.A',
'C92.A0','C92.A1','C92.A2','C92.Z0','C93','C93.0','C93.00','C93.01','C93.02','C94.0',
'C94.00','C94.01','C94.2','C94.20','C94.21','C94.22'
```
*(NON PLD VERIFIED QUERIES 1.sql · QUERY 13)*

### AML backbone hierarchy

**Current production rule (AML base layer, 2026).** Source: `scripts/Notebooks/`
(`Patient Eligibility.ipynb` cells 101 and 114; `AML_LOT_VAL.ipynb` cells 65 and 81). The notebook is
the code that runs and wins where it disagrees with the business-rules page or the V5 guide.

The backbone is the highest-ranked product present in the regimen string. The SQL CASE is evaluated
top to bottom with `LIKE`/`RLIKE` on the comma-joined regimen, so **branch order is the hierarchy**.

**IC Ineligible hierarchy - 11 products** (`MABI_AML_IC_INELIG_LOT_FINAL_*`):

| Rank | Product(s) in regimen | BACKBONE value |
|---:|---|---|
| 1 | VENCLEXTA | VENCLEXTA |
| 2 | TIBSOVO | TIBSOVO |
| 3 | REZLIDHIA | REZLIDHIA |
| 4 | IDHIFA | IDHIFA |
| 5 | XOSPATA | XOSPATA |
| 6 | DAURISMO | DAURISMO |
| 7 | L-DAC | L-DAC |
| 8 | AZACITIDINE, DECITABINE, INQOVI, ONUREG | HMA |

RYDAPT and MYLOTARG were **removed** from this hierarchy ("REMOVING RYDAPT AND MYLOTARG FROM IC INELIG
BACKBONE HIERARCHY"). Both are now IC-Eligible-only products, so an IC-Ineligible patient never carries
them. INQOVI and ONUREG were **added** and resolve to `HMA`.

**IC Eligible hierarchy - 28 products, 24 distinct backbone values** (`MABI_AML_IC_ELIG_LOT_FINAL_*`):

| Rank | Product(s) in regimen | BACKBONE value |
|---:|---|---|
| 1 | S-DAC or HI-DAC | S-DAC/HI-DAC |
| 2 | VANFLYTA | VANFLYTA |
| 3 | VYXEOS | VYXEOS |
| 4 | CYCLOPHOSPHAMIDE | CYCLOPHOSPHAMIDE |
| 5 | VINCRISTINE | VINCRISTINE |
| 6 | FLUDARABINE | FLUDARABINE |
| 7 | IDARUBICIN | IDARUBICIN |
| 8 | DAUNORUBICIN | DAUNORUBICIN |
| 9 | MITOXANTRONE | MITOXANTRONE |
| 10 | RYDAPT | RYDAPT |
| 11 | VENCLEXTA | VENCLEXTA |
| 12 | XOSPATA | XOSPATA |
| 13 | TIBSOVO | TIBSOVO |
| 14 | REZLIDHIA | REZLIDHIA |
| 15 | IDHIFA | IDHIFA |
| 16 | MYLOTARG | MYLOTARG |
| 17 | DAURISMO | DAURISMO |
| 18 | ONUREG | HMA |
| 19 | INQOVI | HMA |
| 20 | NEXAVAR | NEXAVAR |
| 21 | ETOPOSIDE | ETOPOSIDE |
| 22 | CLADRIBINE | CLADRIBINE |
| 23 | CLOFARABINE | CLOFARABINE |
| 24 | AZACITIDINE or DECITABINE | HMA |
| 25 | L-DAC | L-DAC |
| 26 | ARSENIC_TRIOXIDE | ARSENIC_TRIOXIDE ("PATIENTS EXCLUDED LATER", via ARSENIC_FLG) |

`HMA` is reached from two non-adjacent positions (18/19 and 24). The output string is identical, so
LoT results are unaffected, but never derive a numeric rank from the backbone name.

**Rank-list variant (new-definition intensity build).** The Python hierarchy used for the age-and-product
backbone (`PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT`) lists S-DAC and HI-DAC as separate ranks 1 and 2,
keeps ONUREG/INQOVI/AZACITIDINE/DECITABINE as named products (not `HMA`), and returns `UNKNOWN` when no
regimen product is on the applicable list. Its BACKBONE values use a different vocabulary from the SQL
LoT tables, so do not union the two BACKBONE columns.

**Superseded - AML SHA Business Rules Guide V5 (slide 8).** The guide listed 26 IC Eligible products and
13 IC Ineligible products (1 VENCLEXTA, 2 TIBSOVO, 3 REZLIDHIA, 4 IDHIFA, 5 XOSPATA, 6 DAURISMO,
7 RYDAPT, 8 MYLOTARG, 9 LDAC, 10 AZACITIDINE, 11 DECITABINE, 12 INQOVI, 13 ONUREG), with HMAs as
named products. Figures built before the 2026 base-layer change used that hierarchy; see
`rule_change_history.md`.

### AML patient-intensity classification (IC Eligible / IC Ineligible)

**legacy rule - product-only (production; `TYPE` on the LoT table, `PATIENT_COHORT` on the flags table).**
Classified once per patient over every regimen in the journey: if any regimen contains an
IC-Eligible-only product the patient is `IC_ELIG`, otherwise `IC_INELIG` (`MIN(LOW_INTENSITY)` over
the patient's regimens). The class is not re-evaluated per line.

IC-Eligible-only products (`LOW_INTENSITY = 0`): ARSENIC_TRIOXIDE, CLADRIBINE, CLOFARABINE,
CYCLOPHOSPHAMIDE, S-DAC, HI-DAC, DAUNORUBICIN, ETOPOSIDE, FILGRASTIM (dead branch, because Filgrastim
is dropped earlier), FLUDARABINE, IDARUBICIN, MITOXANTRONE, MYLOTARG, NEXAVAR, RYDAPT, VANFLYTA,
VINCRISTINE, VYXEOS.

The observed IC_INELIG product set is exactly: AZACITIDINE, DAURISMO, DECITABINE, IDHIFA, INQOVI,
L-DAC, ONUREG, REZLIDHIA, TIBSOVO, VENCLEXTA, XOSPATA. INQOVI and ONUREG were **moved** to the
IC-Ineligible side ("NOW INQOVI CONSIDERED AS IC INELIG"). The earlier Rydapt/Mylotarg + VEN/HMA
exception (`RYD_MYL_FLG`) is computed in one notebook but no longer changes the result.

**New definition - age and product (`PATIENT_INTENSITY_UPDATED`, surfaced as `PATIENT_COHORT_UPDATED`).** Evaluated on the patient's **line-1 regimen group** only (`LOT = 1` of
`MABI_AML_PATS_LOT_GROUPING_TBL_*`), in this order:

1. Any line-1 product in {MYLOTARG, RYDAPT, ARSENIC_TRIOXIDE, CLADRIBINE, CLOFARABINE, CYCLOPHOSPHAMIDE,
   DAUNORUBICIN, ETOPOSIDE, FILGRASTIM, FLUDARABINE, HI-DAC, IDARUBICIN, MITOXANTRONE, NEXAVAR, S-DAC,
   VINCRISTINE, VANFLYTA, VYXEOS} -> `IC_ELIG`.
2. Every line-1 product in {AZACITIDINE, DECITABINE, ONUREG, INQOVI, TIBSOVO, IDHIFA} -> `IC_INELIG`.
3. Otherwise, if age is known: age = YEAR(FIRST_DX) - SOURCE_PATIENT_HIPAA_BIRTH_YEAR; <= 65 ->
   `IC_ELIG`, > 65 -> `IC_INELIG`.
4. Otherwise -> `IC_INELIG`.

New definition is stored alongside legacy rule, not instead of it, and does not drive the LoT build (the LoT tables
still split on legacy rule). The two can disagree for the same patient. The line-1-only test is narrower than
the business-rules page's wording ("every product the patient has ever taken").

### AML market basket - days of supply and grace period per product

**Current production values** (`Patient Eligibility.ipynb` cell 49; `AML_LOT_VAL.ipynb` cell 17).
28 products. Filgrastim (supportive care) is excluded before DOS/Grace assignment
(`FINAL_PRODUCT_NAME <> 'FILGRASTIM'`), so it can never create or extend an episode.

DOS rule: Rx claims (`source_type LIKE '%RX%'`) use `PRODUCT_DAYS_SUPPLY`, falling back to a flat 28
days when it is NULL or <= 0. Every other claim (PX/SX) uses the fixed value below. A product with no
reviewed grace value gets NULL, never a default (the production QC found zero NULL DOS and zero NULL
grace rows).

| Product | Grace (d) | DOS on PX (d) | Note |
|---|---:|---:|---|
| ARSENIC_TRIOXIDE | 60 | 28 | 28-day cycle |
| AZACITIDINE | 60 | 28 | 28-day cycle |
| CLADRIBINE | 7 | 1 | |
| CLOFARABINE | 5 | 1 | |
| CYCLOPHOSPHAMIDE | 5 | 1 | |
| DAUNORUBICIN | 5 | 1 | |
| DAURISMO | 60 | Rx | oral |
| DECITABINE | 60 | 28 | 28-day cycle |
| ETOPOSIDE | 5 | 1 | |
| FLUDARABINE | 5 | 1 | |
| HI-DAC | 7 | 1 | high-dose cytarabine |
| IDARUBICIN | 5 | 1 | |
| IDHIFA | 60 | Rx | oral |
| INQOVI | **28** | Rx | oral, HMA backbone (V5 guide said 60) |
| L-DAC | 60 | 1 | low-dose cytarabine |
| MITOXANTRONE | 3 | 1 | |
| MYLOTARG | 7 | 1 | |
| NEXAVAR | 18 | Rx | oral |
| ONUREG | 28 | Rx | oral, HMA backbone |
| REZLIDHIA | 60 | Rx | oral |
| RYDAPT | 60 | Rx | oral |
| S-DAC | 7 | 1 | standard-dose cytarabine |
| TIBSOVO | 60 | Rx | oral |
| VANFLYTA | 28 | Rx | oral |
| VENCLEXTA | 60 | Rx | oral |
| VINCRISTINE | 28 | 1 | |
| VYXEOS | 5 | 1 | |
| XOSPATA | 60 | Rx | oral |

"Rx" = taken from the claim. The PX CASE has no branch for these products, so a PX claim for one of
them would get NULL DOS (none were observed).

The three cytarabine products do **not** share one grace value: L-DAC is 60 days, S-DAC and HI-DAC are
7 days. The business-rules page's grace table and cytarabine table now agree with the code (its
earlier note saying all three carry 7 days was removed in the current revision). Whether the 7-day S-DAC/HI-DAC value was clinically
reviewed is unconfirmed (open item OI-10, `context/assumptions/open_items.md`).

Product attributes from the V5 workbook. The high intensity flag (`0` = IC Ineligible product, `1` = IC
Eligible product) is superseded by the legacy rule list above: ONUREG and INQOVI were 1 and are now
IC-Ineligible; MYLOTARG and RYDAPT were "0 or 1" and are now IC-Eligible only.

| Generic name | Final product name | Administration | V5 high intensity flag |
|---|---|---|---|
| azacitidine | AZACITIDINE | SC/IV | 0 |
| glasdegib | DAURISMO | Oral | 0 |
| decitabine | DECITABINE | IV | 0 |
| enasidenib | IDHIFA | Oral | 0 |
| cytarabine | L-DAC | SC/IV | 0 |
| ivosidenib | TIBSOVO | Oral | 0 |
| venetoclax | VENCLEXTA | Oral | 0 |
| gilteritinib | XOSPATA | Oral | 0 |
| olutasidenib | REZLIDHIA | Oral | 0 |
| gemtuzumab ozogamicin | MYLOTARG | IV | 0 or 1 |
| midostaurin | RYDAPT | Oral | 0 or 1 |
| arsenic trioxide | ARSENIC TRIOXIDE | IV | 1 |
| cladribine | CLADRIBINE | IV | 1 |
| clofarabine | CLOFARABINE | IV | 1 |
| cyclophosphamide | CYCLOPHOSPHAMIDE | Oral/IV | 1 |
| daunorubicin | DAUNORUBICIN | IV | 1 |
| etoposide | ETOPOSIDE | IV | 1 |
| fludarabine | FLUDARABINE | IV | 1 |
| cytarabine | HI-DAC | SC/IV | 1 |
| idarubicin | IDARUBICIN | IV | 1 |
| mitoxantrone | MITOXANTRONE | IV | 1 |
| sorafenib | NEXAVAR | Oral | 1 |
| azacitidine | ONUREG | Oral | 1 |
| cedazuridine/decitabine | INQOVI | Oral | 1 |
| cytarabine | S-DAC | SC/IV | 1 |
| vincristine | VINCRISTINE | IV | 1 |
| quizartinib | VANFLYTA | Oral | 1 |
| daunorubicin and cytarabine (liposomal) | VYXEOS | IV | 1 |

*(AML SHA Business Rules Guide V5.pptx, embedded workbook 'AML Market'; basket source: "NCCN
guidelines". The V5 workbook's DOS/grace columns are replaced by the production table above.)*

**Note the grace period is per product for AML** - 3, 5, 7, 18, 28 or 60 days. Venclexta itself is
60. A multi-product AML cohort therefore does not share one stop rule.

**Product resolution.** The production build reads `mastered_product_name` from the claims view, which
already carries L-DAC/S-DAC/HI-DAC and ONUREG/INQOVI/REZLIDHIA/VANFLYTA. The notebook's own cytarabine
dose split and NDC/procedure-code lookups for those four products are commented out; the split is
inherited from the mastered column, using the rule in `key_concepts.md` (Cytarabine intensity).

### AML procedure and product code sets

From the workbook embedded in the AML rules guide, sheet 'Codes':

- **BMB codes (20)**: `079T00Z, 079T0ZX, 079T0ZZ, 079T30Z, 079T3ZX, 079T3ZZ, 079T40Z, 079T4ZX,
  079T4ZZ, 07DT0ZX, 07DT0ZZ, 07DT3ZX, 07DT3ZZ, 38220, 38221, 38222, 4131, 88305, G0364, S2150`
- **SCT codes to be checked in Dx (2)**: `Z94.84, V42.82`
- **SCT codes to be checked in Tx (110)**: `38240, 38241, 30240G2, 30240G3, 4105, 4103, 30233C0,
  30233H0, 30233S0, 30233V0, 30233Y3, 30233Y2, 30260Y1, 30263G1, 30243C0, 30230K0, 30230X0, 30230G0,
  30230Y4, 30233G1, 30250G1, 30243Y4, 30233R0, 30233Q0, 30243H0, 30243L0, 38242, 38243, 30240Y1,
  30240G4, 4101, 4108, 38232, 38206, 30240M0, 30240N0, 30230G3, 30230G4, 30243G1, 30240Y4, 4109,
  30230C0, 30240X0, 30240G0, 30250Y0, 30253G0, 30233Y1, 30233G4, 30260G1, 30253Y1, 30263N0, 30263Y0,
  30243Q0, 30243R0, 30230Y3, 30230Y2, 30243Y2, 30243Y3, 30233P0, 30233N0, 30260Y0, 30253Y0, 30243Y0,
  30243X0, 30230G2, 30230G1, 30240Y3, 30240Y2, 4104, 4107, 30233Y0, 30233X0, 30250N0, 30243S0,
  30233Y4, 30240G1, 30230U2, 30230U3, 30230Y1, 30230U4, 30243G3, 30243G2, 30243Y1, 30243G4, 30233J0,
  30233K0, 4102, 30263Y1, 30253N0, 30253M0, 30230N0, 30230R0, 30233L0, 30233M0, 30233G0, 30230Y0,
  30253R0, 30253Q0, 30240C0, 30253H0, 30240Y0, 30243G0, 30233G3, 30233G2, 30253G1, 30250Y1, 30263G0,
  30263K0, 30243P0, 30243N0`
- **SCT codes used by the production eligibility build (51)**: a subset of the 110 Tx list, searched in
  both `abv_val_ptd_onc_synd.sx_fact_curated_vw.SURGICAL_CODE` and
  `abv_val_ptd_onc_synd.px_fact_curated_vw.PROCEDURE_CODE` (`Patient Eligibility.ipynb` cell 308):
  `38240, 38241, 38243, 38242, 30230G1, 30230G2, 30230G3, 30230G4, 30230U2, 30230U3, 30230U4, 30230Y1,
  30230Y2, 30230Y3, 30230Y4, 30233G1, 30233G2, 30233G3, 30233G4, 30233Y1, 30233Y2, 30233Y3, 30233Y4,
  30240G1, 30240G2, 30240G3, 30240G4, 30240Y1, 30240Y2, 30240Y3, 30240Y4, 30243G1, 30243G2, 30243G3,
  30243G4, 30243Y1, 30243Y2, 30243Y3, 30243Y4, 30250G1, 30250Y1, 30253G1, 30253Y1, 30260G1, 30260Y1,
  30263G1, 30263Y1, 4102, 4103, 4105, 4108`. The other 59 guide codes (e.g. 38206, 38232, 4101, 4104,
  4107, 4109 and the `...C0/H0/X0` ICD-10-PCS variants) are not checked by the production
  `SCT_PX_FLG`. Reproduce the production flag with the 51-code list; use the 110-code list only as a
  stated sensitivity.
- **AML market basket procedure codes (57)**: PROCEDURE_CODE → PROCEDURE_DESC pairs, e.g. J9074 →
  CYCLOPHOSPHAMIDE, J9300 → MYLOTARG, C9024 → VYXEOS, J9017 → ARSENIC_TRIOXIDE. Full list in the
  embedded workbook.
- **AML market basket product ids (715)**: PRODUCT_NAME → PRODUCT_ID (`PRD`-prefixed) pairs. Full
  list in the embedded workbook.
- **Cytarabine Px strength codes (69)**: PROCEDURE_CODE → STRENGTH1 pairs, e.g. J9110 → 500 mg,
  J9094 → 200 mg, C9024 → "2.27 mg, 1mg". Several carry `-` for strength. Full list on slide 10.

*(AML SHA Business Rules Guide V5.pptx · slide 10 and embedded workbook 'Codes')*

### Other code lists

- **market_code (SME Q-09/Q-10)**: on the claims view the valid values are `VENC_CLL`, `VENC_AML`,
  `VENC_CLL_AML_OTHER` (singular; `VENC_CLL_AML_OTHERS` is a typo). On the Rx/Mx activity tables the
  value is `ONC`, and the `market_code = 'ONC'` filter is required. The supplied persistency query omits
  it, so its denominator is too wide; add the filter in any working query.
- **source_type (SME Q-35)**: stored values carry the `' FACT'` suffix (`'RX FACT'`, `'PX FACT'`, …).
  The dictionary's short forms are loose descriptions. The full value set was not supplied; confirm
  it with `SELECT DISTINCT`.
- **AML 1L regimens ranked by patient count** (139 rows, rank only — no counts given): VENCLEXTA 1,
  AZACITIDINE 2, "AZACITIDINE, VENCLEXTA" 3, DECITABINE 4, "DECITABINE, VENCLEXTA" 5, XOSPATA 6,
  RYDAPT 7, ONUREG 8, INQOVI 9, VANFLYTA 10, IDHIFA 11, S-DAC 12 … Ties share a rank.
  *(AML SHA Business Rules Guide V5.pptx · embedded workbook '1L Regimens in SHA')*
  Because it gives rank without counts, this cannot serve as a reference figure for a line
  distribution — see Q-28.

---
