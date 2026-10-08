from __future__ import annotations

from pathlib import Path
import csv
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_KBTS = 6
errors: list[str] = []


def fail(m: str) -> None:
    errors.append(m)


def tsv(rel: str) -> list[dict[str, str]]:
    p = ROOT / rel
    if not p.exists():
        fail(f"Missing TSV: {rel}")
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


for rel in ["AML_Base_Business_Rule.html", "scripts/pldlib/pldlib.egg", "context/domain/pldlib.md", "CLAUDE.md", "README.md", "kbts/index.md", "context/data/table_index.tsv", "context/metrics/index.tsv",
            "verified_queries/index.tsv", "evals/kbt_selection_cases.yaml", "context/assumptions/defaults.yaml"]:
    if not (ROOT / rel).exists():
        fail(f"Missing core file: {rel}")

claude_lines = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
if len(claude_lines) > 130:
    fail(f"CLAUDE.md too long: {len(claude_lines)} lines")

skills = sorted((ROOT / ".claude/skills").glob("*/SKILL.md"))
nums = set()
for p in skills:
    t = p.read_text(encoding="utf-8")
    parts = t.split("---", 2)
    fm = yaml.safe_load(parts[1]) if t.startswith("---") and len(parts) == 3 else {}
    if fm.get("name") != p.parent.name:
        fail(f"Skill name mismatch: {p.parent.name}")
    if len(str(fm.get("description", ""))) < 60:
        fail(f"Description too short: {p.parent.name}")
    if fm.get("user-invocable") is not True:
        fail(f"Skill not user-invocable: {p.parent.name}")
    m = re.match(r"kbt-(\d{2})-", p.parent.name)
    if not m:
        continue  # non-KBT skill: frontmatter checks only
    nums.add(int(m.group(1)))
    for h in ["## Analytical intent", "## Method", "## Working defaults", "## Minimum QC", "## Verified-query candidates"]:
        if h not in t:
            fail(f"Missing {h} in {p.parent.name}")
    nb = re.search(r"Notebook: `([^`]+)`", t)
    if not nb or not (ROOT / nb.group(1)).exists():
        fail(f"Skill {p.parent.name} does not reference an existing notebook")
    for q in re.findall(r"`(AML_[A-Z_]+)`", t.split("## Verified-query candidates")[1].split("##")[0]):
        if q not in {r["query_name"] for r in tsv("verified_queries/index.tsv")}:
            fail(f"Skill {p.parent.name} names unknown query {q}")
if nums != set(range(1, EXPECTED_KBTS + 1)):
    fail(f"KBT numbering mismatch: {sorted(nums)}")

tables = tsv("context/data/table_index.tsv")
if len({r["table_name"] for r in tables}) != len(tables):
    fail("Duplicate table names")
ccols = fcols = 0
for r in tables:
    for k in ["profile_file", "analysis_columns_file", "full_columns_file"]:
        if not (ROOT / r[k]).exists():
            fail(f"Missing {k} for {r['table_name']}")
    try:
        comp = tsv(r["analysis_columns_file"])
        full = tsv(r["full_columns_file"])
    except Exception:
        continue
    if not {c["column_name"] for c in comp} <= {c["column_name"] for c in full}:
        fail(f"Compact columns not a subset for {r['table_name']}")
    if r["analysis_column_count"] != str(len(comp)) or r["full_column_count"] != str(len(full)):
        fail(f"Column counts wrong for {r['table_name']}")
    ccols += len(comp)
    fcols += len(full)

metrics = tsv("context/metrics/index.tsv")
for r in metrics:
    if not (ROOT / r["file"]).exists():
        fail(f"Missing metric file {r['file']}")

queries = tsv("verified_queries/index.tsv")
names = [q["query_name"] for q in queries]
if len(set(names)) != len(names):
    fail("Duplicate query names")
indexed = set()
for q in queries:
    p = ROOT / q["file"]
    indexed.add(p.resolve())
    if not p.exists():
        fail(f"Missing query file {q['file']}")
        continue
    t = p.read_text(encoding="utf-8")
    if f"-- QUERY: {q['query_name']}" not in t:
        fail(f"Header mismatch in {q['file']}")
    if not q["primary_kbt"].isdigit() or not 1 <= int(q["primary_kbt"]) <= EXPECTED_KBTS:
        fail(f"Bad KBT for {q['query_name']}")
    body = "\n".join(l for l in t.splitlines() if l.strip() and not l.lstrip().startswith("--"))
    if not re.search(r"\b(SELECT|WITH)\b", body, re.I):
        fail(f"No SQL in {q['file']}")
    if re.search(r"\bCREATE\s+TABLE\b", body, re.I):
        fail(f"Reference must not create tables: {q['file']}")
    leftover = set(re.findall(r"\{([a-z_]+)\}", body)) - {"exc_dt"}
    if leftover:
        fail(f"Unresolved placeholders {sorted(leftover)} in {q['file']}")
if {p.resolve() for p in (ROOT / "verified_queries").rglob("*.sql")} != indexed:
    fail("verified_queries/*.sql and index.tsv disagree")
covered = {int(q["primary_kbt"]) for q in queries}
if covered != set(range(1, EXPECTED_KBTS + 1)):
    fail(f"Queries do not cover every KBT: {sorted(covered)}")

cases = (yaml.safe_load((ROOT / "evals/kbt_selection_cases.yaml").read_text(encoding="utf-8")) or {}).get("cases", [])
if {int(c["expected_kbt"]) for c in cases} != set(range(1, EXPECTED_KBTS + 1)):
    fail("Eval cases do not cover every KBT")

for p in ROOT.rglob("*"):
    if "outputs" in p.relative_to(ROOT).parts:
        continue  # analysis outputs, not pack content
    if p.is_file() and p.suffix.lower() in {".md", ".tsv", ".sql", ".yaml", ".yml", ".txt"}:
        try:
            t = p.read_text(encoding="utf-8")
        except Exception as e:
            fail(f"Not UTF-8: {p.relative_to(ROOT)}: {e}")
            continue
        if p.suffix.lower() in {".yaml", ".yml"}:
            try:
                yaml.safe_load(t)
            except Exception as e:
                fail(f"Invalid YAML {p.relative_to(ROOT)}: {e}")
        if p.suffix.lower() == ".md":
            for ref in re.findall(r"`((?:context|verified_queries|scripts|config|workflows|kbts|evals|tools)/[^`*<>]+?)`", t):
                if not (ROOT / ref).exists() and "*" not in ref:
                    fail(f"Broken path `{ref}` in {p.relative_to(ROOT)}")

print("AML base-layer KBT pack validation")
print(f"  OK: {len(skills)} KBT skills covering KBT 1-{EXPECTED_KBTS}")
print(f"  OK: {len(tables)} table profiles ({ccols} analysis columns vs {fcols} complete columns)")
print(f"  OK: {len(metrics)} metric files")
print(f"  OK: {len(queries)} indexed verified-query references")
print(f"  OK: {len(cases)} KBT-selection eval prompts")
print(f"  OK: CLAUDE.md: {len(claude_lines)} lines")
if errors:
    print("\nFAILURES:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("\nPASS: structural and content-integrity validation completed with no errors.")
