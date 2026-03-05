"""
validate_schema.py
==================
Validates the schema_registry.yml for naming-convention violations.

Offline mode (default — used in CI):
    python validate_schema.py                         # validate all tables
    python validate_schema.py --table mkcgp_sop10100  # validate one table

Online mode (developer use — requires Fabric/Delta credentials):
    python validate_schema.py --live --env prod        # compare registry vs actual Delta schemas
    python validate_schema.py --live --env dev --workspace MKC-Silver-Dev

Exit code 0 = clean; exit code 1 = violations found (CI will fail).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed. Run: pip install pyyaml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REGISTRY_PATH = Path(__file__).parent / "schema_registry.yml"

# Recognised Silver column suffixes (from naming-conventions.md)
ALLOWED_SUFFIXES: list[str] = [
    "_id",
    "_key",
    "_date",
    "_at",
    "_amount",
    "_qty",
    "_quantity",
    "_name",
    "_type",
    "_flag",
    "_pct",
    "_number",
    "_code",
    "_class",
    "_description",
    "_index",
    "_limit",
    "_terms",
    "_entry",
    "_change",
]

# Regex: all lowercase letters, digits, underscores; must not start/end with underscore
_SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$|^[a-z]$")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _is_snake_case(name: str) -> bool:
    """Return True if name is valid snake_case (lowercase, letters/digits/underscores)."""
    return bool(_SNAKE_RE.match(name))


def _has_allowed_suffix(name: str) -> bool:
    """Return True if name ends with one of the registered suffixes."""
    return any(name.endswith(suffix) for suffix in ALLOWED_SUFFIXES)


def validate_offline(registry: dict[str, Any], target_table: str | None = None) -> list[str]:
    """
    Validate registry format and naming rules without a live connection.

    Returns a list of violation messages. Empty list means clean.
    """
    violations: list[str] = []
    tables: dict[str, Any] = registry.get("tables", {})

    if not tables:
        violations.append("REGISTRY: 'tables' key is missing or empty.")
        return violations

    for table_key, table_def in tables.items():
        if target_table and table_key != target_table:
            continue

        prefix = f"[{table_key}]"

        # Required top-level fields
        for field in ("source_db", "source_table", "silver_entity", "columns"):
            if field not in table_def:
                violations.append(f"{prefix} Missing required field: '{field}'")

        columns: dict[str, Any] = table_def.get("columns", {})
        if not columns:
            violations.append(f"{prefix} 'columns' is empty — at least one column mapping is required.")
            continue

        seen_silver: dict[str, str] = {}  # silver_name → source_name (duplicate detection)

        for source_col, col_def in columns.items():
            silver_name: str = col_def.get("silver", "")

            if not silver_name:
                violations.append(f"{prefix}.{source_col}: 'silver' name is missing.")
                continue

            # Rule 1: must be all-lowercase snake_case
            if not _is_snake_case(silver_name):
                violations.append(
                    f"{prefix}.{source_col}: silver name '{silver_name}' is not valid "
                    f"snake_case (lowercase letters, digits, underscores only; no leading/trailing underscores)."
                )

            # Rule 2: must end with a recognised suffix
            if not _has_allowed_suffix(silver_name):
                violations.append(
                    f"{prefix}.{source_col}: silver name '{silver_name}' does not end with "
                    f"a recognised suffix. Allowed suffixes: {', '.join(ALLOWED_SUFFIXES)}"
                )

            # Rule 3: no duplicate Silver names within the same table
            if silver_name in seen_silver:
                violations.append(
                    f"{prefix}.{source_col}: silver name '{silver_name}' is already used by "
                    f"source column '{seen_silver[silver_name]}' in the same table."
                )
            else:
                seen_silver[silver_name] = source_col

            # Rule 4: 'type' must be present
            if not col_def.get("type"):
                violations.append(f"{prefix}.{source_col}: 'type' field is missing.")

    if target_table and target_table not in tables:
        violations.append(f"Table '{target_table}' not found in registry.")

    return violations


# ---------------------------------------------------------------------------
# Online mode (optional — not used in CI)
# ---------------------------------------------------------------------------

def validate_online(registry: dict[str, Any], env: str, workspace: str | None = None) -> list[str]:
    """
    Compare registry column definitions against actual Delta table schemas in OneLake.

    Requires `deltalake` or `pyarrow` with OneLake ABFS credentials available in the
    environment (e.g., via AZURE_CLIENT_ID / AZURE_CLIENT_SECRET / AZURE_TENANT_ID).
    """
    try:
        from deltalake import DeltaTable  # type: ignore
    except ImportError:
        return ["Online mode requires 'deltalake'. Run: pip install deltalake"]

    env_cap = env.capitalize()
    ws_name = workspace or f"MKC-Silver-{env_cap}"
    base_path = f"abfss://{ws_name}@onelake.dfs.fabric.microsoft.com/Silver.Lakehouse/Tables"

    violations: list[str] = []

    for table_key, table_def in registry.get("tables", {}).items():
        silver_entity: str = table_def.get("silver_entity", "")
        table_path = f"{base_path}/{silver_entity}"
        registered_silvers: set[str] = {
            col_def["silver"]
            for col_def in table_def.get("columns", {}).values()
            if col_def.get("silver")
        }

        try:
            dt = DeltaTable(table_path)
            actual_cols: set[str] = {field.name for field in dt.schema().fields}
        except Exception as exc:
            violations.append(f"[{table_key}] Could not read Delta table at '{table_path}': {exc}")
            continue

        # Columns in registry but absent from actual table
        missing = registered_silvers - actual_cols
        for col in sorted(missing):
            violations.append(f"[{table_key}] MISSING in actual table: '{col}' (registered in schema_registry.yml)")

        # Columns in actual table but absent from registry (undocumented)
        # Ignore Bronze audit columns (_ingested_at etc.) and surrogate keys
        undocumented = actual_cols - registered_silvers - {
            "_ingested_at", "_source_system", "_source_table", "_pipeline_run_id",
            "_loaded_at", "_source_company",
        }
        for col in sorted(undocumented):
            violations.append(f"[{table_key}] UNDOCUMENTED column in actual table: '{col}' (not in schema_registry.yml)")

    return violations


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate schema_registry.yml for naming-convention violations."
    )
    parser.add_argument(
        "--table",
        metavar="TABLE_KEY",
        help="Validate a single table (e.g. mkcgp_sop10100). Default: all tables.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Online mode: compare registry against actual Delta schemas in OneLake.",
    )
    parser.add_argument(
        "--env",
        default="dev",
        choices=["dev", "prod"],
        help="Target environment for online mode (default: dev).",
    )
    parser.add_argument(
        "--workspace",
        metavar="WORKSPACE_NAME",
        help="Override workspace name for online mode.",
    )
    parser.add_argument(
        "--registry",
        default=str(REGISTRY_PATH),
        metavar="PATH",
        help=f"Path to schema_registry.yml (default: {REGISTRY_PATH}).",
    )
    args = parser.parse_args()

    registry_path = Path(args.registry)
    if not registry_path.exists():
        print(f"ERROR: Registry file not found: {registry_path}")
        sys.exit(1)

    with open(registry_path, encoding="utf-8") as fh:
        registry = yaml.safe_load(fh)

    # Always run offline validation first
    violations = validate_offline(registry, target_table=args.table)

    if args.live:
        if violations:
            print("Offline validation failed — fix naming violations before running online mode.\n")
        else:
            online_violations = validate_online(registry, env=args.env, workspace=args.workspace)
            violations.extend(online_violations)

    # Report results
    table_count = len(registry.get("tables", {}))
    if args.table:
        scope = f"table '{args.table}'"
    else:
        scope = f"all {table_count} table(s)"

    mode = "offline + online" if args.live else "offline"

    if violations:
        print(f"\nSchema validation FAILED [{mode}] — {scope}\n")
        for v in violations:
            print(f"  VIOLATION: {v}")
        print(f"\n{len(violations)} violation(s) found.")
        sys.exit(1)
    else:
        print(f"Schema validation PASSED [{mode}] — {scope} — no violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
