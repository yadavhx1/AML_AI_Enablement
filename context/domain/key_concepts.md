## Key concepts - AML base layer

Concepts needing a paragraph. One-line terms are in `context/data/taxonomy.yaml`.

**Episode → regimen → line of therapy.** The three-stage construction, in order:

> "Episodes are created to consolidate consecutive fills/administrations of the same drug into
> continuous episodes. A new episode starts when the gap between fills exceeds the allowed days
> supply + gap tolerance."
> "To monitor and track a patient's use of multiple products at the same point of the patient
> journey, product episodes must be combined into regimens used to identify the patient's total
> treatment picture."
> "The final step is to apply line of therapy. This considers the primary (backbone) regimen the
> patient is on at a given time as well as the count of regimens this patient has had successively."
*(AML SHA Business Rules Guide V5.pptx · slide 11)*

The order is not a convention—getting it wrong produces a wrong answer that looks right. Use the KBT for the notebook stage that produces the field you need (KBT 1-5). NPS dashboard figures use KBT 4 with the `nps_dashboard_legacy` metric.

**Backbone product.** "A backbone product is the foundational drug of a regimen. It can be combined
with other drugs within an episode, but when regimen is assigned to a patient it is classified based
upon the backbone product being taken." Where a regimen has several products, "The backbone product
is chosen based on a hierarchy, meaning the highest-ranked product in the regimen becomes the
backbone." For CLL, "Orals are given priority over CITs".
*(AML SHA Business Rules Guide V5.pptx · slides 14 and 8; CLL_LoT_Business_rules_v1_ZS.pptx · slide 7)*

**Patient eligibility exists because the data has holes.** The rationale, verbatim:

> "In real-world data, two patients may follow the same treatment journey, yet appear different due
> to missing information ... For one patient, missing claims create artificial gaps—after the first
> prescription of Product A and before the second prescription of Product B. Although both patients
> have identical real-world behavior, incomplete data alters the perceived journey and can lead to
> incorrect [conclusions]. This presents a structural challenge. While such patients should be
> excluded where possible, there is no reliable way to confirm whether a claim truly did not occur or
> was simply not captured by the data vendor. To mitigate this risk, we apply patient eligibility
> criteria at the patient level."
*(AML SHA Business Rules Guide V5.pptx · slide 15)*

**Cytarabine intensity (AML).** Cytarabine appears as three distinct products depending on dose,
which is why the AML basket lists L-DAC, S-DAC and HI-DAC separately:

> "Based on effective dosage: L-DAC = ≤ 20 mg/m²; S-DAC = >20 mg/m² and < 2,000 mg/m²;
> Hi-DAC = ≥ 2,000 mg/m²."
> Strength for Rx claims is "(Quantity × Strength) / Days of Supply (DOS)"; for Px claims it is
> "Units × Strength" from a static procedure-code table. "Effective Dosage = Strength / Gender
> factor. Gender factor = Male: 1.9, Female: 1.6, Else: 1.7."
> Data hygiene: "Replace NULL/0 values with mode value at product level. In case of tie in mode
> value, hierarchy based on min DOS and max Qty is considered." And: "Mean + 3 SD is calculated at
> the product code level for DOS, quantity, and units. If for any patient, their DOS, quantity, or
> units value exceeds their respective Mean + 3 SD, that corresponding value is replaced by the
> respective Mean + 3 SD value."
*(AML SHA Business Rules Guide V5.pptx · slide 9)*

In the current AML base layer the split is **inherited**: the build reads the mastered product name
(already L-DAC / S-DAC / HI-DAC) and the notebook's own dose-split block is commented out.
*(Patient Eligibility.ipynb · cells 38-39)*

---

## AML base layer (2026 production build)

Sources: `AML_Base_Business_Rule.html` (explainer),
`AML_LOT_VAL.ipynb` (May'26 validation build, `_v2` tables) and `Patient Eligibility.ipynb` (Aug'26
build of LoT + eligibility flags + HCP affiliations). Where the explainer and the code disagree, **the
code wins**; the disagreements are listed below. All tables are in `Z_ABV_CWS_MABI_ONC_ANALYTICS` and
carry the suffix `_BUSINESS_RULE_CHANGE_VAL` (Aug'26 build) or `_BUSINESS_RULE_CHANGE_VAL_v2` (May'26
validation build). Spark SQL plus pandas; episode/regimen steps use `pldlib.stencil`.

**AML is built here, not inherited.** Unlike CLL, the AML episode/regimen/LoT frame used by the AML
KPIs is produced by this pipeline in the CWS schema. Read `MABI_AML_PATS_COMB_LOT_TBL_*` (or the RR
version) and `MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*` instead of rebuilding it, unless the user asks for a
rule simulation.

**Pipeline, in order** (each stage only adds columns; source claims are never edited):

1. **Claims intake** from `abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw`
   (`source_flag='SHA_PTD'`, `source_market='ONC'`), restricted to the 28 AML basket products via
   `mastered_product_name`. Patient key = `patient_sk` kept whole (with the `SHA_PTDONC` suffix) as
   `PATIENT_GID`.
2. **Patient pool** - two variants exist, see "Patient pool" below.
3. **DOS + grace** per product (`reference_codes_and_mappings.md`, AML market basket). Filgrastim is
   dropped first.
4. **`stencil.sob`** - `sob(grace='GRACE_VALUE', lookback='360', dedup_type_vl='yesremove')`: the
   pldlib `sob` function, which prepares the episode input. Same patient, product and day keeps the
   claim with the larger DOS (`DOS_FINAL DESC, CLAIM_ID`). It also labels each episode start with a
   source of business (NTB/RS, switch/add-on), and the 360-day lookback is used only for those labels.
   Episodes break on grace alone (`context/domain/pldlib.md`). The explainer page calls
   this step "Start-of-Bucket" (and no longer defines SOB in its glossary), but the library names it
   source of business (SME Q-65), which is what its `sob_lvl7` labels are.
5. **Episode** - `stencil.episode`: groups the SOB rows to one row per patient × product × episode
   with `EPISODE_START_DATE_DRVD`, `EPISODE_END_DATE1/2/3_DRVD`, `episode_length` and
   `episode_first_sob`.
6. **Regimen** - `stencil.regimen(collect_type='COLLECT_SET', clean_up_type_vl='no',
   regimen_threshold_vl='5000')`: overlapping episodes of different products combine into one regimen
   string naming every active product (comma-joined, e.g. `AZACITIDINE, VENCLEXTA`).
7. **Patient intensity** (legacy rule) splits patients into IC_ELIG / IC_INELIG, each with its own backbone
   hierarchy.
8. **No regimen consolidation.** The previous "major regimen" / subset-merge passes (regimens shorter
   than 28 days that were a subset of a neighbour with no gap) and the minimum-length filter
   (`REGIMEN_LENGTH >= 28`, Rydapt >= 14) are **commented out**. Every regimen row is kept. This
   surfaces more line changes than earlier builds.
9. **Line of therapy**, per patient in regimen-start order:
   - REG_NUM = 1 -> LINE_CHANGE = 1 (line 1).
   - PREV_GAP = DATEDIFF(regimen start, previous regimen end) > 90 -> new line.
   - PREV_GAP <= 90: same backbone -> same line; VENCLEXTA <-> HMA in either direction -> same line
     (named exception, covers azacitidine, decitabine, Inqovi and Onureg because all four resolve to
     `HMA`); any other backbone change -> new line.
   - LOT = running SUM(LINE_CHANGE).
   The exception compares backbones with `LIKE '%VENCLEXTA%'` / `LIKE '%HMA%'`.
10. **Combined LoT table** `MABI_AML_PATS_COMB_LOT_TBL_*` = UNION of the IC_ELIG and IC_INELIG LoT
    tables, with `TYPE` = intensity.
11. **LoT regimen grouping** `MABI_AML_PATS_LOT_GROUPING_TBL_*` - one row per patient x LOT:
    LOT_START_DATE = MIN(regimen start), LOT_END_DATE = MAX(regimen end), LOT_REGIMEN_GROUP = sorted,
    de-duplicated union of every product in the line.
12. **new-definition intensity** (age + product, on LOT = 1) -> `PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT`.
13. **First Dx/Tx** `MABI_AML_LOT_PAT_FST_DX_TX_TBL_*`: FIRST_DX (37-code set, `dx_fact_curated_vw`),
    FIRST_TX / LAST_TX (MIN regimen start / MAX regimen end), VEN_START / VEN_END (MIN Venclexta episode
    start / MAX Venclexta episode end).
14. **Eligibility flags** `MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*` - see
    `context/domain/aml_eligibility_flags.md`.
15. **RR line refinement** `MABI_AML_PATS_LOT_RR_12M_UPD_*` - see below.
16. **HCP affiliations** `MABI_AML_HCP_AFFILIATIONS` - see below.

**Patient pool.** The two notebooks define it differently, and the counts are not interchangeable:

| Build | Pool rule | Patients |
|---|---|---:|
| `AML_LOT_VAL` (`_v2` tables) | >= 2 distinct AML-coded diagnosis claims (37-code set) ever, SHA_PTD; `market_code` filter commented out | 57,697 |
| `Patient Eligibility` (`_BUSINESS_RULE_CHANGE_VAL` tables) | `market_code = 'VENC_AML'` on the claims view, no diagnosis-count filter | 84,199 |

The business-rules page describes the 2+ diagnosis rule ("no recency window, no hierarchy against
other cancers"). It is not stated which build is the published one (open item). Name the table
suffix you read. Neither build checks for a competing non-AML primary diagnosis. Legacy rule split: `_v2` 43,194 IC_INELIG / 14,503 IC_ELIG; Aug'26 60,839 / 23,360.

**RR line refinement (1L -> 2L+).** For each regimen, take the latest AML relapse/remission diagnosis
(13 RR codes) in the 12 months up to and including the regimen start (`MAX_RR_DIAG_DT`, from
`SHA_PTD_MABI_ONC_SYND.MABI_DX_TBL`). MIN_RR_DT = earliest of those dates across the patient's
regimens. A LOT 1 regimen starting on or after MIN_RR_DT is promoted to LOT 2; `LOT_REF` = '1L' when
the refined line is 1, else '2L+'. This is the source of the `aml_lot_group` 1L / 2L+ buckets. The
step sits after `spark.stop()` in the notebook, so confirm the RR table is current before using it.

**AML HCP affiliations** (`Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_HCP_AFFILIATIONS`). For every NPI on
the AML treatment claims: NPI -> ABBOTT_CUSTOMER_ID (`ABV_DDS_SYND.CUSTOMER_TBL`, `DDS_ACTIVE_FLAG='Y'`);
child account from `ABV_ADS_SYND.DIM_ACCOUNT_AFFILIATIONS_TBL` (`UNIVERSE_NAME='1VIEW_ONCOLOGY'`,
`SALES_FORCE_CODE='ONH2'`, `DDS_ACTIVE_FLAG='Y'`), falling back to Reltio
`ABV_MHCD_SYND.MHCD_RLTN_ALL_ORG_CUSTOMR_WKLY_TBL` (`ADS_ACTIVE_FLAG='Y'`, `VALUATION_INCLUDE_FLAG='Y'`)
only for customers absent from the first. Site of care (`FINAL_ACCOUNT_TYPE_GROUP_2`) comes from the
COE-uploaded `heme_account` account type, keeping the highest-priority type per HCP (Elite Oncology
Center > Academic Teaching Hospital > IDN - Academic Affiliated > IDN - Community Affiliated >
Corporate > Other Community > VA > DOD > NULL), grouped as Academic / Academic Satellite / Community /
Federal / Not Available. Community splits into Larger Community (max child-account decile >= 8 from
`MABI_AML_CHILD_ACCOUNT_DECILE`) and Smaller Community. The SOC step uses the 1View `HCI-HCP`
affiliation type. None of these upstream tables is cataloged in this pack.

**Business-rules page (current revision, 2026-10-07).** The page in
`AML_Base_Business_Rule.html` was revised. The previous revision
(2026-10-01) was removed from the pack; a copy is in `aml_context_pack_kbt.zip`. The revision removed the earlier
problem passages instead of correcting them. It no longer contains:

- the "recent methodology change" notes on the pool, backbones and consolidation;
- the cytarabine grace asymmetry note;
- the SCT and timing section (SCT_PX/DX flags, TX_POST_DX_FLG, DX_TX_DIFF_FLG, ARSENIC_FLG default);
- the calendar-semester rule;
- the "What comes out" KPI section;
- the rule index;
- the open-items table;
- the glossary entries for NPS, SCT, Semester and SOB.

Those rules still run in the notebooks, so the pack documents them from code (flags metric, NPS metric,
`open_items.md`). The revision also changed or added the following:

- **Diagnosis codes.** The 13 ICD-10 codes it shows are now labelled "AML diagnosis codes" and no longer
  "the 13 codes that define the pool". It adds 7 legacy ICD-9 codes (205.00, 205.01, 206.00, 206.01,
  207.00, 207.20, 207.21) as the ICD-9 counterparts.
- **Rx sources.** Rx claims are "retail and mail order"; specialty pharmacy is no longer listed.
- **legacy rule wording.** It now says "even one IC-ELIG-only product at any point in their journey", which
  matches the code (MIN over regimens).
- **Eligibility flags.** It now lists five flags: DX_LB, TX_TXL_MX, TX_TXL_RX and the two VEN lookback
  flags. The two VEN continuity flags (TX_TXL_MX/RX_ELIG_VEN_FLG) are no longer described, though the
  code still builds them.

**Where the page and the code still disagree** (code followed):

- **Diagnosis codes.** The page's code chips (13 ICD-10 + 7 ICD-9) are not the code's sets. The pool
  and FIRST_DX use the 37-code set. That set carries ICD-9 205.x only; 206.x and 207.x appear in no
  notebook. The 13 ICD-10 codes are the RR set.
- **new definition.** The page says new definition looks at every product ever taken; the code evaluates only the
  line-1 regimen group.
- **Flag windows.** The page says the flags test "every semester of a defined lookback window". The two
  VEN lookback flags use calendar semesters; DX_LB and the TXL flags use exact-date rolling 6-month
  windows (see the flags metric).
- **Flag count.** The page lists five flags and still says "8+ eligibility flags" and "8 continuity
  flags" in its header and pipeline. The code builds seven activity flags plus the timing, SCT and
  arsenic flags.
- **Cytarabine.** The page says the cytarabine split happens before DOS/grace. That is true of the
  mastered product name; the notebooks' own dose-split code is commented out.

**Validation-build data cut.** The Aug'26 build reads data through 2026-06-30 (Rx max claim date); its
eligibility exclusion semester (`exc_dt`) is 2025-07-01, the last semester with complete data. The
treatment table spans 2010-01-01 to 2026-07-03.

---


## Notebooks and KBTs

The pack's five notebooks are in `scripts/Notebooks/`. The four AML_LOT notebooks are the production
`AML_LOT_VAL.ipynb` split by stage; AML_PATIENT_ELIGIBILITY is the eligibility part of `Patient Eligibility.ipynb`.
The original team notebooks are not kept in the pack. Fully commented-out cells
were removed. Each notebook is independent (own Spark session and globals) but reads the persisted
output of the one before.

| Notebook | KBT | Builds |
|---|---:|---|
| AML_LOT_TX_TABLE | 1 | patient pool (temp view), TX table, TX final table with DOS and grace |
| AML_LOT_SOB_EPISODE | 2 | SOB table, episode table |
| AML_LOT_REGIMEN | 3 | regimen table |
| AML_LOT_PATIENT_INTENSITY_LOT | 4 | patient cohort (legacy rule), IC_INELIG / IC_ELIG LoT, combined LoT, LoT grouping, new-definition intensity |
| AML_PATIENT_ELIGIBILITY | 5 | exact-date activity tables, first Dx/Tx, eligibility flag tables, final flags table |
| AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated | 6 | NPS dashboard: legacy line backbone, initiating HCP, account and segments, Power BI dataset, NPS by LoT and month, Ipsos index, account rollup |

`AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` is a sixth notebook, added as supplied (outputs cleared). It runs after
the whole base layer, once AML_PATIENT_ELIGIBILITY has finished, and reads the LoT grouping, the cohort
and the final eligibility flags. It is not part of the base-layer refresh (`workflows/aml_nps_dashboard_legacy.md`). Its "legacy" IC definition picks one backbone per line
from the product rank lists in pandas, instead of the per-regimen SQL backbone of KBT 4.

Changes made when splitting (see `PACK_CHANGELOG.md`): AML_LOT_REGIMEN reads the persisted episode table
instead of the `episode_df` temp view; AML_LOT_PATIENT_INTENSITY_LOT re-creates `patient_pool`, formats the
`lot_regimen_group` and new-definition table names (three cells previously sent `{...}` to Spark literally),
and renames the new definition DataFrame so it no longer overwrites the table-name global; AML_PATIENT_ELIGIBILITY reads
the combined LoT table through the `pat_comb_lot` global and the new-definition table from its persisted name.

Steps of the original team notebooks that are **not** in the five notebooks: the relapse/remission line
refinement (`MABI_AML_PATS_LOT_RR_12M_UPD`) and the AML HCP affiliations. Their profiles are kept for
reference; there is no KBT for them.
