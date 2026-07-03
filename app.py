import base64
import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from xml.sax.saxutils import escape as xml_escape

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    def load_dotenv() -> None:
        return None

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
REPORT_FOLDER = BASE_DIR / "reports"
UPLOAD_FOLDER.mkdir(exist_ok=True)
REPORT_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

STATE: Dict[str, Any] = {
    "schema": None,
    "skills": "",
    "last_upload": None,
    "latest_checks": [],
    "latest_report": None,
    "latest_report_path": None,
}

TEXT_TYPES = {
    "char",
    "nchar",
    "varchar",
    "nvarchar",
    "text",
    "ntext",
    "sysname",
}
DATE_TYPES = {"date", "datetime", "datetime2", "datetimeoffset", "smalldatetime", "time"}
ROW_PREVIEW_LIMIT = 200
BLOCKED_SQL_WORDS = {
    "alter",
    "backup",
    "bulk",
    "create",
    "delete",
    "drop",
    "exec",
    "execute",
    "insert",
    "merge",
    "restore",
    "truncate",
    "update",
}


def load_skills() -> str:
    skills_path = BASE_DIR / "DEskills.md"
    if skills_path.exists():
        return skills_path.read_text(encoding="utf-8")
    return ""


def normalize_sql_text(raw_text: str) -> str:
    text = raw_text.lstrip("\ufeff").strip()
    if not text:
        return ""

    if text.startswith("{"):
        try:
            notebook = json.loads(text)
            cells = notebook.get("cells", [])
            fragments: List[str] = []
            for cell in cells:
                if cell.get("cell_type") != "code":
                    continue
                source = cell.get("source", "")
                if isinstance(source, list):
                    fragments.append("".join(source))
                else:
                    fragments.append(str(source))
            if fragments:
                return "\n".join(fragments)
        except Exception:
            pass

    return raw_text


def split_top_level_csv(text: str) -> List[str]:
    parts: List[str] = []
    start = 0
    depth = 0
    in_quote = False
    quote_char = ""

    for idx, char in enumerate(text):
        if in_quote:
            if char == quote_char:
                in_quote = False
            continue
        if char in {"'", '"'}:
            in_quote = True
            quote_char = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            parts.append(text[start:idx].strip())
            start = idx + 1

    final = text[start:].strip()
    if final:
        parts.append(final)
    return parts


def bracket_identifier(schema: str, table: Optional[str] = None, column: Optional[str] = None) -> str:
    def clean(value: str) -> str:
        return str(value).replace("]", "]]")

    if table is None:
        return f"[{clean(schema)}]"
    if column is None:
        return f"[{clean(schema)}].[{clean(table)}]"
    return f"[{clean(schema)}].[{clean(table)}].[{clean(column)}]"


def column_identifier(column: str, alias: Optional[str] = None) -> str:
    name = f"[{str(column).replace(']', ']]')}]"
    if alias:
        return f"{alias}.{name}"
    return name


def extract_bracket_columns(text: str) -> List[str]:
    return [match.group(1) for match in re.finditer(r"\[([^\]]+)\]\s*(?:ASC|DESC)?", text, re.IGNORECASE)]


def constraint_columns(chunk: str) -> List[str]:
    match = re.search(r"\((?P<cols>.*?)\)", chunk, re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    return extract_bracket_columns(match.group("cols"))


def find_matching_paren(text: str, open_index: int) -> int:
    depth = 0
    in_quote = False
    quote_char = ""
    for idx in range(open_index, len(text)):
        char = text[idx]
        if in_quote:
            if char == quote_char:
                in_quote = False
            continue
        if char in {"'", '"'}:
            in_quote = True
            quote_char = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return idx
    return -1


def parse_column_definition(chunk: str) -> Optional[Dict[str, Any]]:
    column_match = re.match(
        r"^\[(?P<name>[^\]]+)\]\s+\[(?P<type>[^\]]+)\](?:\s*\((?P<params>[^)]+)\))?(?P<rest>.*)$",
        chunk.strip(),
        re.IGNORECASE | re.DOTALL,
    )
    if not column_match:
        return None

    rest = column_match.group("rest") or ""
    params = column_match.group("params")
    max_length: Optional[int] = None
    precision: Optional[str] = None
    if params:
        first_param = params.split(",")[0].strip()
        if first_param.isdigit():
            max_length = int(first_param)
        precision = params.strip()

    return {
        "name": column_match.group("name"),
        "data_type": column_match.group("type").lower(),
        "nullable": "NOT NULL" not in rest.upper(),
        "max_length": max_length,
        "precision": precision,
    }


def parse_sql_schema(sql_text: str) -> Dict[str, Any]:
    sql = normalize_sql_text(sql_text)
    database_match = re.search(r"\bUSE\s+\[([^\]]+)\]", sql, re.IGNORECASE)
    database = database_match.group(1) if database_match else None

    tables: List[Dict[str, Any]] = []
    table_lookup: Dict[str, Dict[str, Any]] = {}
    create_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:\[(?P<schema>[^\]]+)\]\.)?\[(?P<table>[^\]]+)\]\s*\(",
        re.IGNORECASE,
    )

    for match in create_pattern.finditer(sql):
        open_index = match.end() - 1
        close_index = find_matching_paren(sql, open_index)
        if close_index < 0:
            continue

        schema_name = match.group("schema") or "dbo"
        table_name = match.group("table")
        body = sql[open_index + 1 : close_index]
        table = {
            "schema": schema_name,
            "table": table_name,
            "columns": [],
            "primary_key": [],
            "unique_constraints": [],
            "foreign_keys": [],
        }

        for chunk in split_top_level_csv(body):
            clean_chunk = " ".join(chunk.split())
            if not clean_chunk:
                continue
            upper_chunk = clean_chunk.upper()
            column = parse_column_definition(chunk)
            if column:
                table["columns"].append(column)
                continue
            if "PRIMARY KEY" in upper_chunk:
                table["primary_key"] = constraint_columns(chunk)
            elif " UNIQUE " in f" {upper_chunk} ":
                columns = constraint_columns(chunk)
                if columns:
                    table["unique_constraints"].append({"name": constraint_name(chunk), "columns": columns})
            elif "FOREIGN KEY" in upper_chunk:
                fk = parse_foreign_key_chunk(chunk, schema_name, table_name)
                if fk:
                    table["foreign_keys"].append(fk)

        tables.append(table)
        table_lookup[f"{schema_name}.{table_name}".lower()] = table

    for fk in parse_alter_table_foreign_keys(sql):
        table = table_lookup.get(f"{fk['schema']}.{fk['table']}".lower())
        if table is not None:
            table["foreign_keys"].append(fk)

    for uq in parse_create_unique_indexes(sql):
        table = table_lookup.get(f"{uq['schema']}.{uq['table']}".lower())
        if table is not None and uq["columns"]:
            table["unique_constraints"].append({"name": uq["name"], "columns": uq["columns"]})

    return {"tables": tables, "source": "uploaded_sql", "database": database, "relationships": schema_relationships(tables)}


def constraint_name(chunk: str) -> str:
    match = re.search(r"CONSTRAINT\s+\[([^\]]+)\]", chunk, re.IGNORECASE)
    if match:
        return match.group(1)
    return "unnamed_constraint"


def parse_foreign_key_chunk(chunk: str, schema_name: str, table_name: str) -> Optional[Dict[str, Any]]:
    fk_match = re.search(
        r"FOREIGN\s+KEY\s*\((?P<cols>.*?)\)\s+REFERENCES\s+(?:\[(?P<ref_schema>[^\]]+)\]\.)?\[(?P<ref_table>[^\]]+)\]\s*\((?P<ref_cols>.*?)\)",
        chunk,
        re.IGNORECASE | re.DOTALL,
    )
    if not fk_match:
        return None
    return {
        "name": constraint_name(chunk),
        "schema": schema_name,
        "table": table_name,
        "columns": extract_bracket_columns(fk_match.group("cols")),
        "referenced_schema": fk_match.group("ref_schema") or "dbo",
        "referenced_table": fk_match.group("ref_table"),
        "referenced_columns": extract_bracket_columns(fk_match.group("ref_cols")),
    }


def parse_alter_table_foreign_keys(sql: str) -> List[Dict[str, Any]]:
    pattern = re.compile(
        r"ALTER\s+TABLE\s+(?:\[(?P<schema>[^\]]+)\]\.)?\[(?P<table>[^\]]+)\].*?"
        r"CONSTRAINT\s+\[(?P<name>[^\]]+)\]\s+FOREIGN\s+KEY\s*\((?P<cols>.*?)\)\s*"
        r"REFERENCES\s+(?:\[(?P<ref_schema>[^\]]+)\]\.)?\[(?P<ref_table>[^\]]+)\]\s*\((?P<ref_cols>.*?)\)",
        re.IGNORECASE | re.DOTALL,
    )
    relationships = []
    for match in pattern.finditer(sql):
        relationships.append(
            {
                "name": match.group("name"),
                "schema": match.group("schema") or "dbo",
                "table": match.group("table"),
                "columns": extract_bracket_columns(match.group("cols")),
                "referenced_schema": match.group("ref_schema") or "dbo",
                "referenced_table": match.group("ref_table"),
                "referenced_columns": extract_bracket_columns(match.group("ref_cols")),
            }
        )
    return relationships


def parse_create_unique_indexes(sql: str) -> List[Dict[str, Any]]:
    pattern = re.compile(
        r"CREATE\s+UNIQUE\s+(?:NONCLUSTERED|CLUSTERED)?\s*INDEX\s+\[(?P<name>[^\]]+)\]\s+ON\s+"
        r"(?:\[(?P<schema>[^\]]+)\]\.)?\[(?P<table>[^\]]+)\]\s*\((?P<cols>.*?)\)",
        re.IGNORECASE | re.DOTALL,
    )
    indexes = []
    for match in pattern.finditer(sql):
        indexes.append(
            {
                "name": match.group("name"),
                "schema": match.group("schema") or "dbo",
                "table": match.group("table"),
                "columns": extract_bracket_columns(match.group("cols")),
            }
        )
    return indexes


def schema_relationships(tables: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    relationships = []
    for table in tables:
        for fk in table.get("foreign_keys", []):
            relationships.append(
                {
                    "name": fk.get("name"),
                    "from_table": f"{fk.get('schema', table.get('schema'))}.{fk.get('table', table.get('table'))}",
                    "from_columns": fk.get("columns", []),
                    "to_table": f"{fk.get('referenced_schema')}.{fk.get('referenced_table')}",
                    "to_columns": fk.get("referenced_columns", []),
                }
            )
    return relationships


def summarize_schema(schema: Dict[str, Any], max_tables: int = 80) -> str:
    if not schema or not schema.get("tables"):
        return "No schema available."

    lines = []
    for table in schema.get("tables", [])[:max_tables]:
        cols = []
        for column in table.get("columns", [])[:40]:
            required = "NOT NULL" if not column.get("nullable", True) else "NULL"
            size = f"({column['precision']})" if column.get("precision") else ""
            cols.append(f"{column['name']} {column['data_type']}{size} {required}")
        pk = f" PK({', '.join(table.get('primary_key', []))})" if table.get("primary_key") else ""
        uniques = [",".join(item.get("columns", [])) for item in table.get("unique_constraints", [])]
        uq = f" UQ({'; '.join(uniques[:5])})" if uniques else ""
        lines.append(f"{table['schema']}.{table['table']}: {', '.join(cols)}{pk}{uq}")

    rels = schema.get("relationships") or schema_relationships(schema.get("tables", []))
    if rels:
        lines.append("Relationships:")
        for rel in rels[:120]:
            lines.append(
                f"{rel['from_table']}({', '.join(rel.get('from_columns', []))}) -> "
                f"{rel['to_table']}({', '.join(rel.get('to_columns', []))})"
            )
    return "\n".join(lines)


def get_connection(database_name: Optional[str] = None):
    server = os.getenv("SQL_SERVER", "localhost")
    database = database_name or os.getenv("SQL_DATABASE", "master")
    username = os.getenv("SQL_USERNAME", "")
    password = os.getenv("SQL_PASSWORD", "")

    import pyodbc

    if username and password:
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};"
            f"UID={username};PWD={password};Encrypt=no;TrustServerCertificate=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};"
            "Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
        )
    return pyodbc.connect(conn_str, timeout=15)


def list_databases() -> Dict[str, Any]:
    try:
        conn = get_connection("master")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sys.databases
            WHERE state_desc = 'ONLINE'
            ORDER BY name
            """
        )
        databases = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"databases": databases}
    except Exception as exc:
        return {"databases": [], "error": str(exc)}


def discover_schema_from_database(database_name: Optional[str] = None) -> Dict[str, Any]:
    database = database_name or os.getenv("SQL_DATABASE", "master")
    try:
        conn = get_connection(database)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
        )
        tables = []
        table_lookup: Dict[str, Dict[str, Any]] = {}
        for schema_name, table_name in cursor.fetchall():
            col_cursor = conn.cursor()
            col_cursor.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH,
                       NUMERIC_PRECISION, NUMERIC_SCALE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """,
                schema_name,
                table_name,
            )
            columns = []
            for column_name, data_type, is_nullable, char_len, precision, scale in col_cursor.fetchall():
                columns.append(
                    {
                        "name": column_name,
                        "data_type": (data_type or "").lower(),
                        "nullable": str(is_nullable).upper() != "NO",
                        "max_length": char_len if isinstance(char_len, int) and char_len > 0 else None,
                        "precision": f"{precision},{scale}" if precision is not None and scale is not None else None,
                    }
                )
            table = {
                "schema": schema_name,
                "table": table_name,
                "columns": columns,
                "primary_key": [],
                "unique_constraints": [],
                "foreign_keys": [],
            }
            tables.append(table)
            table_lookup[f"{schema_name}.{table_name}".lower()] = table

        for pk in fetch_primary_keys(conn):
            table = table_lookup.get(f"{pk['schema']}.{pk['table']}".lower())
            if table is not None:
                table["primary_key"] = pk["columns"]

        for uq in fetch_unique_constraints(conn):
            table = table_lookup.get(f"{uq['schema']}.{uq['table']}".lower())
            if table is not None and uq["columns"] != table.get("primary_key"):
                table["unique_constraints"].append({"name": uq["name"], "columns": uq["columns"]})

        for fk in fetch_foreign_keys(conn):
            table = table_lookup.get(f"{fk['schema']}.{fk['table']}".lower())
            if table is not None:
                table["foreign_keys"].append(fk)

        conn.close()
        return {"tables": tables, "source": "live_database", "database": database, "relationships": schema_relationships(tables)}
    except Exception as exc:
        return {"tables": [], "source": "live_database", "error": str(exc), "database": database}


def fetch_primary_keys(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.name AS schema_name, t.name AS table_name, kc.name AS constraint_name,
               c.name AS column_name, ic.key_ordinal
        FROM sys.key_constraints kc
        JOIN sys.tables t ON kc.parent_object_id = t.object_id
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        JOIN sys.index_columns ic ON kc.parent_object_id = ic.object_id AND kc.unique_index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE kc.type = 'PK'
        ORDER BY s.name, t.name, kc.name, ic.key_ordinal
        """
    )
    grouped: Dict[tuple, List[str]] = {}
    for schema_name, table_name, constraint_name, column_name, _ in cursor.fetchall():
        grouped.setdefault((schema_name, table_name, constraint_name), []).append(column_name)
    return [{"schema": key[0], "table": key[1], "name": key[2], "columns": cols} for key, cols in grouped.items()]


def fetch_unique_constraints(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.name AS schema_name, t.name AS table_name, i.name AS index_name,
               c.name AS column_name, ic.key_ordinal
        FROM sys.indexes i
        JOIN sys.tables t ON i.object_id = t.object_id
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.is_unique = 1 AND i.is_hypothetical = 0 AND ic.is_included_column = 0
        ORDER BY s.name, t.name, i.name, ic.key_ordinal
        """
    )
    grouped: Dict[tuple, List[str]] = {}
    for schema_name, table_name, index_name, column_name, _ in cursor.fetchall():
        grouped.setdefault((schema_name, table_name, index_name), []).append(column_name)
    return [{"schema": key[0], "table": key[1], "name": key[2], "columns": cols} for key, cols in grouped.items()]


def fetch_foreign_keys(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT fk.name AS fk_name,
               sch_child.name AS child_schema, child.name AS child_table, child_col.name AS child_column,
               sch_parent.name AS parent_schema, parent.name AS parent_table, parent_col.name AS parent_column,
               fkc.constraint_column_id
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        JOIN sys.tables child ON fk.parent_object_id = child.object_id
        JOIN sys.schemas sch_child ON child.schema_id = sch_child.schema_id
        JOIN sys.columns child_col ON fkc.parent_object_id = child_col.object_id AND fkc.parent_column_id = child_col.column_id
        JOIN sys.tables parent ON fk.referenced_object_id = parent.object_id
        JOIN sys.schemas sch_parent ON parent.schema_id = sch_parent.schema_id
        JOIN sys.columns parent_col ON fkc.referenced_object_id = parent_col.object_id AND fkc.referenced_column_id = parent_col.column_id
        ORDER BY sch_child.name, child.name, fk.name, fkc.constraint_column_id
        """
    )
    grouped: Dict[tuple, Dict[str, Any]] = {}
    for fk_name, child_schema, child_table, child_column, parent_schema, parent_table, parent_column, _ in cursor.fetchall():
        key = (fk_name, child_schema, child_table, parent_schema, parent_table)
        item = grouped.setdefault(
            key,
            {
                "name": fk_name,
                "schema": child_schema,
                "table": child_table,
                "columns": [],
                "referenced_schema": parent_schema,
                "referenced_table": parent_table,
                "referenced_columns": [],
            },
        )
        item["columns"].append(child_column)
        item["referenced_columns"].append(parent_column)
    return list(grouped.values())


def gemini_api_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def call_gemini(parts: List[Dict[str, Any]], system_instruction: str = "") -> str:
    api_key = gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured.")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").removeprefix("models/")
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent"
        f"?key={urllib.parse.quote(api_key, safe='')}"
    )
    body: Dict[str, Any] = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.1,
        },
    }
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Gemini HTTP error {exc.code}: {exc.reason}. Response body: {body_text}"
        ) from exc

    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    content = candidates[0].get("content", {})
    text_parts = [part.get("text", "") for part in content.get("parts", []) if part.get("text")]
    if not text_parts:
        raise RuntimeError("Gemini returned no text content.")
    return "\n".join(text_parts)


def extract_json_payload(text: str) -> Any:
    clean = text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"```$", "", clean).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        start_candidates = [idx for idx in [clean.find("{"), clean.find("[")] if idx >= 0]
        if not start_candidates:
            raise
        start = min(start_candidates)
        end = max(clean.rfind("}"), clean.rfind("]"))
        return json.loads(clean[start : end + 1])


def schema_from_image(path: Path) -> Dict[str, Any]:
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    prompt = (
        "Extract the database schema from this diagram. Return only JSON with keys: "
        "database, tables, relationships. tables must contain schema, table, columns, "
        "primary_key, unique_constraints, foreign_keys. Each column must contain name, "
        "data_type, nullable. Relationships must include from_table, from_columns, "
        "to_table, to_columns. Use dbo when the schema name is not visible. "
        "Do not invent columns or relationships that are not visible."
    )
    content = call_gemini(
        [
            {"text": prompt},
            {"inline_data": {"mime_type": mime_type, "data": encoded}},
        ],
        "You are careful at reading SQL Server schema diagrams.",
    )
    parsed = extract_json_payload(content)
    if not isinstance(parsed, dict):
        raise RuntimeError("Gemini did not return a schema object.")
    return normalize_schema_object(parsed, "uploaded_image")


def normalize_schema_object(payload: Dict[str, Any], source: str) -> Dict[str, Any]:
    tables = []
    for raw_table in payload.get("tables", []):
        full_name = raw_table.get("name") or raw_table.get("table") or raw_table.get("table_name") or ""
        schema_name = raw_table.get("schema") or "dbo"
        table_name = raw_table.get("table") or raw_table.get("table_name") or full_name
        if "." in table_name:
            schema_name, table_name = table_name.split(".", 1)
        columns = []
        for raw_col in raw_table.get("columns", []):
            if isinstance(raw_col, str):
                columns.append({"name": raw_col, "data_type": "unknown", "nullable": True})
            else:
                columns.append(
                    {
                        "name": raw_col.get("name") or raw_col.get("column"),
                        "data_type": (raw_col.get("data_type") or raw_col.get("type") or "unknown").lower(),
                        "nullable": bool(raw_col.get("nullable", True)),
                        "max_length": raw_col.get("max_length"),
                        "precision": raw_col.get("precision"),
                    }
                )
        tables.append(
            {
                "schema": schema_name,
                "table": table_name,
                "columns": [col for col in columns if col.get("name")],
                "primary_key": raw_table.get("primary_key") or raw_table.get("primaryKey") or [],
                "unique_constraints": raw_table.get("unique_constraints") or raw_table.get("uniqueConstraints") or [],
                "foreign_keys": raw_table.get("foreign_keys") or raw_table.get("foreignKeys") or [],
            }
        )

    schema = {
        "database": payload.get("database"),
        "source": source,
        "tables": tables,
        "relationships": payload.get("relationships") or schema_relationships(tables),
    }
    return schema


def build_builtin_checks(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    seen = set()

    def add(check: Dict[str, Any]) -> None:
        key = (check.get("table"), check.get("category"), check.get("question"), check.get("sql"))
        if key not in seen:
            seen.add(key)
            checks.append(check)

    for table in schema.get("tables", []):
        schema_name = table["schema"]
        table_name = table["table"]
        full_table = f"{schema_name}.{table_name}"
        from_name = bracket_identifier(schema_name, table_name)

        for column in table.get("columns", []):
            if column.get("nullable", True):
                continue
            condition = null_or_blank_condition(column, "t")
            add(
                {
                    "id": stable_id("completeness", full_table, column["name"]),
                    "table": full_table,
                    "category": "Completeness",
                    "severity": "Critical",
                    "confidence": "High",
                    "question": f"Are there records in {full_table} with missing values in mandatory column {column['name']}?",
                    "sql": f"SELECT COUNT_BIG(*) AS issue_count FROM {from_name} AS t WHERE {condition};",
                    "result_sql": f"SELECT t.* FROM {from_name} AS t WHERE {condition};",
                    "recommendation": f"Populate {column['name']} or relax the NOT NULL requirement only if the business rule changed.",
                    "evidence": f"{column['name']} is marked NOT NULL in the schema.",
                }
            )

        if table.get("primary_key"):
            add_duplicate_check(add, full_table, from_name, table["primary_key"], "Uniqueness", "Critical", "Primary key")

        for unique in table.get("unique_constraints", []):
            columns = unique.get("columns") if isinstance(unique, dict) else unique
            if columns:
                add_duplicate_check(add, full_table, from_name, columns, "Uniqueness", "Medium", "Unique constraint")

        for fk in table.get("foreign_keys", []):
            add_fk_check(add, fk)

        for start_col, end_col in temporal_column_pairs(table.get("columns", [])):
            add(
                {
                    "id": stable_id("temporal", full_table, start_col, end_col),
                    "table": full_table,
                    "category": "Temporal Consistency",
                    "severity": "High",
                    "confidence": "High",
                    "question": f"Are there records in {full_table} where {start_col} is later than {end_col}?",
                    "sql": (
                        f"SELECT COUNT_BIG(*) AS issue_count FROM {from_name} AS t "
                        f"WHERE {column_identifier(start_col, 't')} IS NOT NULL "
                        f"AND {column_identifier(end_col, 't')} IS NOT NULL "
                        f"AND {column_identifier(start_col, 't')} > {column_identifier(end_col, 't')};"
                    ),
                    "result_sql": (
                        f"SELECT t.* FROM {from_name} AS t "
                        f"WHERE {column_identifier(start_col, 't')} IS NOT NULL "
                        f"AND {column_identifier(end_col, 't')} IS NOT NULL "
                        f"AND {column_identifier(start_col, 't')} > {column_identifier(end_col, 't')};"
                    ),
                    "recommendation": f"Correct records where {start_col} is after {end_col}.",
                    "evidence": "The column names form a start/end or from/to date pair.",
                }
            )

    return checks


def null_or_blank_condition(column: Dict[str, Any], alias: str) -> str:
    col = column_identifier(column["name"], alias)
    data_type = (column.get("data_type") or "").lower()
    if data_type in TEXT_TYPES or data_type.endswith("char") or data_type in {"unknown"}:
        return f"({col} IS NULL OR NULLIF(LTRIM(RTRIM(CAST({col} AS NVARCHAR(MAX)))), '') IS NULL)"
    return f"{col} IS NULL"


def add_duplicate_check(add_func, full_table: str, from_name: str, columns: List[str], category: str, severity: str, evidence_kind: str) -> None:
    col_list = ", ".join(column_identifier(col) for col in columns)
    non_null = " AND ".join(f"{column_identifier(col)} IS NOT NULL" for col in columns)
    where = f" WHERE {non_null}" if non_null else ""
    join_condition = " AND ".join(
        f"{column_identifier(col, 't')} = duplicate_keys.{column_identifier(col)}"
        for col in columns
    )
    label = ", ".join(columns)
    add_func(
        {
            "id": stable_id("duplicate", full_table, label),
            "table": full_table,
            "category": category,
            "severity": severity,
            "confidence": "High",
            "question": f"Are there duplicate {label} values present in {full_table}?",
            "sql": (
                "SELECT COUNT_BIG(*) AS issue_count FROM ("
                f"SELECT {col_list} FROM {from_name}{where} GROUP BY {col_list} HAVING COUNT_BIG(*) > 1"
                ") AS duplicate_keys;"
            ),
            "result_sql": (
                f"SELECT t.* FROM {from_name} AS t "
                "JOIN ("
                f"SELECT {col_list} FROM {from_name}{where} GROUP BY {col_list} HAVING COUNT_BIG(*) > 1"
                f") AS duplicate_keys ON {join_condition};"
            ),
            "recommendation": f"Remove duplicate {label} values or enforce the expected uniqueness constraint.",
            "evidence": f"{evidence_kind} requires {label} to be unique.",
        }
    )


def add_fk_check(add_func, fk: Dict[str, Any]) -> None:
    columns = fk.get("columns", [])
    ref_columns = fk.get("referenced_columns", [])
    if not columns or not ref_columns or len(columns) != len(ref_columns):
        return
    child_table = f"{fk['schema']}.{fk['table']}"
    parent_table = f"{fk['referenced_schema']}.{fk['referenced_table']}"
    child_name = bracket_identifier(fk["schema"], fk["table"])
    parent_name = bracket_identifier(fk["referenced_schema"], fk["referenced_table"])
    join_condition = " AND ".join(
        f"c.{column_identifier(child_col)} = p.{column_identifier(parent_col)}"
        for child_col, parent_col in zip(columns, ref_columns)
    )
    parent_missing = " AND ".join(f"p.{column_identifier(parent_col)} IS NULL" for parent_col in ref_columns)
    child_present = " AND ".join(f"c.{column_identifier(child_col)} IS NOT NULL" for child_col in columns)
    label = ", ".join(columns)
    add_func(
        {
            "id": stable_id("fk", child_table, parent_table, label),
            "table": child_table,
            "category": "Referential Integrity",
            "severity": "Critical",
            "confidence": "High",
            "question": f"Are there records in {child_table} that reference missing parent records in {parent_table}?",
            "sql": (
                f"SELECT COUNT_BIG(*) AS issue_count FROM {child_name} AS c "
                f"LEFT JOIN {parent_name} AS p ON {join_condition} "
                f"WHERE {child_present} AND {parent_missing};"
            ),
            "result_sql": (
                f"SELECT c.* FROM {child_name} AS c "
                f"LEFT JOIN {parent_name} AS p ON {join_condition} "
                f"WHERE {child_present} AND {parent_missing};"
            ),
            "recommendation": f"Add the missing {parent_table} records or correct the {label} values in {child_table}.",
            "evidence": f"Foreign key {fk.get('name', '')} links {child_table} to {parent_table}.",
        }
    )


def temporal_column_pairs(columns: List[Dict[str, Any]]) -> List[tuple]:
    names = {col["name"].lower(): col["name"] for col in columns if (col.get("data_type") or "").lower() in DATE_TYPES}
    pairs = []
    candidates = [
        ("validfrom", "validto"),
        ("startdate", "enddate"),
        ("effectivestartdate", "effectiveenddate"),
        ("createddate", "modifieddate"),
        ("createdwhen", "lasteditedwhen"),
        ("orderdate", "deliverydate"),
        ("orderdate", "shipmentdate"),
        ("shipmentdate", "deliverydate"),
    ]
    for start, end in candidates:
        if start in names and end in names:
            pairs.append((names[start], names[end]))
    return pairs


def stable_id(*parts: str) -> str:
    raw = "|".join(str(part).lower() for part in parts)
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:90]


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def reframe_question(question: Any) -> str:
    text = str(question or "").strip()
    if not text:
        return ""
    text = text.rstrip("?").strip()

    patterns = [
        (r"^Why do records in (.+?) have (.+)$", lambda m: f"Are there records in {m.group(1)} with {m.group(2)}?"),
        (r"^Why do records in (.+?) reference (.+)$", lambda m: f"Are there records in {m.group(1)} that reference {m.group(2)}?"),
        (r"^Why are (.+)$", lambda m: f"Are there {lower_first(m.group(1))}?"),
        (r"^Why do (.+)$", lambda m: f"Do {lower_first(m.group(1))}?"),
        (r"^Why does (.+)$", lambda m: f"Does {lower_first(m.group(1))}?"),
        (r"^Why is (.+)$", lambda m: f"Is there {lower_first(m.group(1))}?"),
    ]
    for pattern, formatter in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            return formatter(match)
    return f"{text}?"


def build_gemini_checks(user_request: str, schema: Dict[str, Any], skills: str, builtin_checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt = {
        "task": "Generate additional evidence-backed SQL Server data quality checks as yes/no investigation questions.",
        "user_request": user_request,
        "schema_summary": summarize_schema(schema),
        "already_generated_checks": [
            {
                "table": check.get("table"),
                "category": check.get("category"),
                "question": check.get("question"),
            }
            for check in builtin_checks[:200]
        ],
        "required_json_shape": {
            "reply": "short data engineer summary",
            "checks": [
                {
                    "table": "schema.table",
                    "category": "Completeness|Validity|Uniqueness|Consistency|Referential Integrity|Schema Conformance|Temporal Consistency|Cross-Table Reconciliation|Business Rule Conformance",
                    "severity": "Critical|High|Medium|Low",
                    "confidence": "High|Medium",
                    "question": "yes/no investigation question beginning with Are there, Do any, Does, Is, or Can",
                    "sql": "read-only T-SQL SELECT returning issue_count",
                    "result_sql": "read-only T-SQL SELECT TOP (200) returning the rows that failed the check",
                    "recommendation": "specific remediation",
                    "evidence": "schema, relationship, business rule, or data evidence",
                }
            ],
        },
        "rules": "Return only checks that are supported by the schema or visible relationships. Phrase every question as a yes/no SQL investigation, not as a Why question. Example: use 'Are there players participating in a match not registered for one of the match teams in PlayerSeason for that season?' instead of 'Why are players participating...'. Do not generate exploratory distributions, top-N, min/max summaries, histograms, or generic questions. Do not duplicate already_generated_checks. Every sql must be read-only and return an issue_count column. Every result_sql must be read-only and return the failing rows behind that check, capped with TOP (200).",
    }
    system = (
        "You are a senior data quality engineer. Follow these local instructions exactly:\n"
        f"{skills}\n\nReturn strict JSON only."
    )
    content = call_gemini([{"text": json.dumps(prompt, ensure_ascii=False)}], system)
    parsed = extract_json_payload(content)
    if not isinstance(parsed, dict):
        return {"reply": "", "checks": []}
    checks = []
    for check in parsed.get("checks") or parsed.get("questions") or []:
        normalized = normalize_check(check)
        if normalized:
            checks.append(normalized)
    return {"reply": parsed.get("reply", ""), "checks": checks}


def normalize_check(check: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(check, dict):
        return None
    question = check.get("question") or check.get("finding")
    sql = check.get("sql") or check.get("query")
    if not question or not sql:
        return None
    category = check.get("category") or "Validity"
    severity = check.get("severity") or "Medium"
    confidence = check.get("confidence") or "Medium"
    result_sql = check.get("result_sql") or check.get("detail_sql") or check.get("row_sql") or ""
    result_sql = result_sql.strip() if isinstance(result_sql, str) else ""
    if str(confidence).lower() == "low":
        return None
    question_text = reframe_question(question)
    return {
        "id": stable_id("gemini", check.get("table", ""), question_text),
        "table": check.get("table") or "",
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "question": question_text,
        "sql": sql.strip(),
        "result_sql": result_sql if result_sql and is_read_only_sql(result_sql) else "",
        "recommendation": check.get("recommendation") or "Review the affected records and correct the source data or constraint.",
        "evidence": check.get("evidence") or "Generated from schema review.",
        "source": "gemini",
    }


def is_read_only_sql(sql: str) -> bool:
    stripped = strip_sql_comments(sql).strip().rstrip(";").strip()
    if not stripped:
        return False
    if re.search(r"\bGO\b", stripped, re.IGNORECASE):
        return False
    tokens = {token.lower() for token in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", stripped)}
    if tokens & BLOCKED_SQL_WORDS:
        return False
    return bool(re.match(r"^(SELECT|WITH)\b", stripped, re.IGNORECASE))


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    return sql


def execute_sql(sql: str, database_name: Optional[str] = None) -> Dict[str, Any]:
    if not sql:
        return {"ok": False, "error": "No SQL was generated.", "execution_time_ms": 0}
    if not is_read_only_sql(sql):
        return {"ok": False, "error": "Only read-only SELECT statements are allowed.", "execution_time_ms": 0}

    started = time.perf_counter()
    try:
        conn = get_connection(database_name)
        cursor = conn.cursor()
        if hasattr(cursor, "timeout"):
            cursor.timeout = 120
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(200) if cursor.description else []
        conn.close()
        elapsed = int((time.perf_counter() - started) * 1000)
        serial_rows = [[to_json_value(value) for value in row] for row in rows]
        return {
            "ok": True,
            "columns": columns,
            "rows": serial_rows,
            "row_count": len(serial_rows),
            "affected_count": affected_count(columns, serial_rows),
            "execution_time_ms": elapsed,
        }
    except Exception as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        return {"ok": False, "error": str(exc), "execution_time_ms": elapsed}


def to_json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    return value


def affected_count(columns: List[str], rows: List[List[Any]]) -> int:
    if not rows:
        return 0
    lowered = [col.lower() for col in columns]
    for candidate in ("issue_count", "affected_records", "rows_returned", "duplicate_count", "orphan_count"):
        if candidate in lowered:
            idx = lowered.index(candidate)
            try:
                return int(rows[0][idx] or 0)
            except Exception:
                return 0
    if len(rows) == 1 and rows[0] and isinstance(rows[0][0], (int, float)):
        return int(rows[0][0] or 0)
    return len(rows)


def result_sql_for_check(check: Dict[str, Any]) -> str:
    configured = (check.get("result_sql") or "").strip()
    if configured and is_read_only_sql(configured):
        return configured
    return count_query_to_result_sql(check.get("sql", ""))


def count_query_to_result_sql(sql: str) -> str:
    clean = strip_sql_comments(sql).strip().rstrip(";").strip()
    if not clean:
        return ""

    match = re.match(
        r"^SELECT\s+COUNT(?:_BIG)?\s*\([^)]*\)\s+(?:AS\s+)?(?:\[[^\]]+\]|[a-zA-Z_][a-zA-Z0-9_]*)?\s+FROM\s+(?P<from_clause>.+)$",
        clean,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return sql.strip()

    return f"SELECT * FROM {match.group('from_clause').strip()};"


def execute_checks(checks: List[Dict[str, Any]], database_name: Optional[str]) -> List[Dict[str, Any]]:
    results = []
    for check in checks:
        execution = execute_sql(check.get("sql", ""), database_name)
        status = "warning"
        if execution.get("ok"):
            status = "failed" if int(execution.get("affected_count") or 0) > 0 else "passed"
        results.append({**check, "execution": execution, "status": status})
    return results


def merge_checks(*groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged = []
    seen = set()
    for group in groups:
        for check in group:
            key = (check.get("table", "").lower(), check.get("question", "").lower())
            if key in seen:
                continue
            seen.add(key)
            merged.append(check)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    merged.sort(key=lambda item: (severity_order.get(str(item.get("severity", "")).lower(), 4), item.get("table", "")))
    return merged


def build_report(database: str, results: List[Dict[str, Any]], ai_message: str = "") -> Dict[str, Any]:
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    total = len(results)
    passed = sum(1 for item in results if item["status"] == "passed")
    failed = sum(1 for item in results if item["status"] == "failed")
    warnings = sum(1 for item in results if item["status"] == "warning")
    overall_score = int((passed / total) * 100) if total else 0

    issues = []
    for item in results:
        execution = item.get("execution", {})
        if item["status"] == "passed":
            continue
        issues.append(
            {
                "table": item.get("table", ""),
                "question": reframe_question(item.get("question", "")),
                "category": item.get("category", ""),
                "severity": item.get("severity", "Medium"),
                "confidence": item.get("confidence", "Medium"),
                "execution_time_ms": execution.get("execution_time_ms", 0),
                "rows_returned": execution.get("affected_count") if execution.get("ok") else 0,
                "columns": execution.get("columns", []),
                "rows": execution.get("rows", []),
                "sql": item.get("sql", ""),
                "result_sql": result_sql_for_check(item),
                "status": item["status"],
                "recommendation": item.get("recommendation", ""),
                "evidence": item.get("evidence", ""),
                "error": execution.get("error"),
            }
        )

    return {
        "database": database,
        "generated_at": generated_at,
        "overall_score": overall_score,
        "summary": {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
        },
        "metrics": category_metrics(results),
        "issues": issues,
        "checks": [
            {
                "table": item.get("table", ""),
                "category": item.get("category", ""),
                "severity": item.get("severity", ""),
                "confidence": item.get("confidence", ""),
                "question": reframe_question(item.get("question", "")),
                "sql": item.get("sql", ""),
                "result_sql": result_sql_for_check(item),
                "status": item.get("status", ""),
                "rows_returned": item.get("execution", {}).get("affected_count", 0),
                "columns": item.get("execution", {}).get("columns", []),
                "rows": item.get("execution", {}).get("rows", []),
                "execution_time_ms": item.get("execution", {}).get("execution_time_ms", 0),
                "recommendation": item.get("recommendation", ""),
            }
            for item in results
        ],
        "ai_message": ai_message,
    }


def category_metrics(results: List[Dict[str, Any]]) -> Dict[str, int]:
    mapping = {
        "completeness": {"Completeness"},
        "consistency": {"Consistency", "Temporal Consistency", "Cross-Table Reconciliation"},
        "uniqueness": {"Uniqueness"},
        "validity": {"Validity", "Schema Conformance", "Business Rule Conformance"},
        "accuracy": {"Business Rule Conformance", "Validity"},
        "integrity": {"Referential Integrity", "Cross-Table Reconciliation"},
    }
    metrics = {}
    overall = int((sum(1 for item in results if item["status"] == "passed") / len(results)) * 100) if results else 0
    for metric, categories in mapping.items():
        scoped = [item for item in results if item.get("category") in categories]
        if not scoped:
            metrics[metric] = overall
        else:
            metrics[metric] = int((sum(1 for item in scoped if item["status"] == "passed") / len(scoped)) * 100)
    return metrics


def create_xlsx_report(report: Dict[str, Any]) -> Path:
    filename = f"profile_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = REPORT_FOLDER / filename
    sheets = [
        ("Summary", [["Database", report["database"]], ["Generated At", report["generated_at"]], ["Overall Score", report["overall_score"]]] + list(report["summary"].items())),
        ("Metrics", [["Metric", "Score"]] + [[key, value] for key, value in report.get("metrics", {}).items()]),
        (
            "Issues",
            [["Table", "Question", "Category", "Severity", "Confidence", "Rows Returned", "Execution MS", "Recommendation", "Status", "Error"]]
            + [
                [
                    item.get("table"),
                    item.get("question"),
                    item.get("category"),
                    item.get("severity"),
                    item.get("confidence"),
                    item.get("rows_returned"),
                    item.get("execution_time_ms"),
                    item.get("recommendation"),
                    item.get("status"),
                    item.get("error") or "",
                ]
                for item in report.get("issues", [])
            ],
        ),
        (
            "Checks",
            [["Table", "Category", "Question", "SQL", "Status", "Rows Returned", "Execution MS", "Recommendation"]]
            + [
                [
                    item.get("table"),
                    item.get("category"),
                    item.get("question"),
                    item.get("sql"),
                    item.get("status"),
                    item.get("rows_returned"),
                    item.get("execution_time_ms"),
                    item.get("recommendation"),
                ]
                for item in report.get("checks", [])
            ],
        ),
    ]
    write_xlsx(path, sheets)
    return path


def write_xlsx(path: Path, sheets: List[tuple]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", content_types_xml(len(sheets)))
        workbook.writestr("_rels/.rels", package_rels_xml())
        workbook.writestr("xl/workbook.xml", workbook_xml(sheets))
        workbook.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(len(sheets)))
        workbook.writestr("xl/styles.xml", styles_xml())
        for idx, (_, rows) in enumerate(sheets, start=1):
            workbook.writestr(f"xl/worksheets/sheet{idx}.xml", worksheet_xml(rows))


def content_types_xml(sheet_count: int) -> str:
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for idx in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{overrides}</Types>"
    )


def package_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def workbook_xml(sheets: List[tuple]) -> str:
    sheet_nodes = "".join(
        f'<sheet name="{xml_escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>'
        for idx, (name, _) in enumerate(sheets, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheet_nodes}</sheets></workbook>"
    )


def workbook_rels_xml(sheet_count: int) -> str:
    relationships = "".join(
        f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        for idx in range(1, sheet_count + 1)
    )
    relationships += f'<Relationship Id="rId{sheet_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{relationships}</Relationships>'
    )


def styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        "</styleSheet>"
    )


def worksheet_xml(rows: List[List[Any]]) -> str:
    row_nodes = []
    for row_idx, row in enumerate(rows, start=1):
        cell_nodes = []
        for col_idx, value in enumerate(row, start=1):
            ref = f"{excel_column(col_idx)}{row_idx}"
            text = "" if value is None else str(value)
            cell_nodes.append(f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(text)}</t></is></c>')
        row_nodes.append(f'<row r="{row_idx}">{"".join(cell_nodes)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_nodes)}</sheetData></worksheet>'
    )


def excel_column(index: int) -> str:
    letters = ""
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def active_database(payload: Optional[Dict[str, Any]] = None) -> str:
    payload = payload or {}
    schema = STATE.get("schema") or {}
    return payload.get("database") or schema.get("database") or os.getenv("SQL_DATABASE", "master")


def export_checks_to_sql_file(checks: List[Dict[str, Any]]) -> str:
    """Export checks to a .sql file with commented questions and the queries."""
    sql_lines = []
    sql_lines.append("-- Data Quality Check Queries")
    sql_lines.append("-- Generated at: " + datetime.now().isoformat())
    sql_lines.append("")
    
    for check in checks:
        question = check.get("question", "").replace("--", "- ")
        category = check.get("category", "Unknown")
        severity = check.get("severity", "Medium")
        sql_query = check.get("sql", "").strip()
        
        if sql_query:
            sql_lines.append(f"-- Category: {category} | Severity: {severity}")
            sql_lines.append(f"-- Question: {question}")
            sql_lines.append(sql_query)
            sql_lines.append("")
    
    sql_content = "\n".join(sql_lines)
    sql_file_path = REPORT_FOLDER / f"checks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    sql_file_path.write_text(sql_content, encoding="utf-8")
    return str(sql_file_path)


def ensure_test_database() -> bool:
    """Create 'test' database if it doesn't exist and create required tables."""
    try:
        server = os.getenv("SQL_SERVER", "(local)")
        username = os.getenv("SQL_USERNAME", "")
        password = os.getenv("SQL_PASSWORD", "")
        
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};"
        if username:
            conn_str += f"UID={username};PWD={password};"
        else:
            conn_str += "Trusted_Connection=yes;"
        
        import pyodbc
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Check if test database exists
        cursor.execute("SELECT name FROM sys.databases WHERE name = 'test'")
        if not cursor.fetchone():
            cursor.execute("CREATE DATABASE [test]")
            conn.commit()
        
        cursor.close()
        conn.close()
        
        # Connect to test database and create tables
        conn_str_test = conn_str.replace("Driver=", "Database=test;Driver=").replace("Driver=test;Driver=", "Driver=")
        conn_str_test = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database=test;"
        if username:
            conn_str_test += f"UID={username};PWD={password};"
        else:
            conn_str_test += "Trusted_Connection=yes;"
        
        conn = pyodbc.connect(conn_str_test)
        cursor = conn.cursor()
        
        # Create questions table if it doesn't exist
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'questions')
            CREATE TABLE [questions] (
                [question_id] INT IDENTITY(1,1) PRIMARY KEY,
                [question] NVARCHAR(MAX) NOT NULL,
                [category] VARCHAR(100),
                [severity] VARCHAR(50),
                [table_name] VARCHAR(255),
                [created_at] DATETIME DEFAULT GETDATE()
            )
        """)
        
        # Create query table if it doesn't exist
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'query')
            CREATE TABLE [query] (
                [query_id] INT IDENTITY(1,1) PRIMARY KEY,
                [query] NVARCHAR(MAX) NOT NULL,
                [question_id] INT,
                [category] VARCHAR(100),
                [severity] VARCHAR(50),
                [table_name] VARCHAR(255),
                [created_at] DATETIME DEFAULT GETDATE(),
                FOREIGN KEY ([question_id]) REFERENCES [questions]([question_id])
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error ensuring test database: {e}")
        return False


def push_checks_to_database(checks: List[Dict[str, Any]]) -> bool:
    """Push checks (questions and queries) to the test database."""
    try:
        ensure_test_database()
        
        server = os.getenv("SQL_SERVER", "(local)")
        username = os.getenv("SQL_USERNAME", "")
        password = os.getenv("SQL_PASSWORD", "")
        
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database=test;"
        if username:
            conn_str += f"UID={username};PWD={password};"
        else:
            conn_str += "Trusted_Connection=yes;"
        
        import pyodbc
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        for check in checks:
            question = check.get("question", "")
            category = check.get("category", "")
            severity = check.get("severity", "")
            table_name = check.get("table", "")
            sql_query = check.get("sql", "").strip()
            
            # Insert question
            cursor.execute(
                "INSERT INTO [questions] ([question], [category], [severity], [table_name]) VALUES (?, ?, ?, ?)",
                (question, category, severity, table_name)
            )
            question_id = cursor.lastrowid
            
            # Insert query
            if sql_query:
                cursor.execute(
                    "INSERT INTO [query] ([query], [question_id], [category], [severity], [table_name]) VALUES (?, ?, ?, ?, ?)",
                    (sql_query, question_id, category, severity, table_name)
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error pushing checks to database: {e}")
        return False


def run_profile_flow(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not STATE.get("skills"):
        STATE["skills"] = load_skills()

    schema = STATE.get("schema")
    database = active_database(payload)
    if not schema:
        discovered = discover_schema_from_database(database)
        if discovered.get("error"):
            return {"ok": False, "error": discovered["error"]}
        schema = discovered
        STATE["schema"] = schema

    user_request = (payload.get("message") or payload.get("objective") or "Run a full data quality profile.").strip()
    builtin_checks = build_builtin_checks(schema)
    ai_message = ""
    gemini_error = None
    gemini_checks: List[Dict[str, Any]] = []
    try:
        gemini_result = build_gemini_checks(user_request, schema, STATE["skills"], builtin_checks)
        ai_message = gemini_result.get("reply", "")
        gemini_checks = gemini_result.get("checks", [])
    except Exception as exc:
        gemini_error = str(exc)

    checks = merge_checks(builtin_checks, gemini_checks)
    results = execute_checks(checks, database)
    report = build_report(database, results, ai_message)
    report_path = create_xlsx_report(report)

    STATE["latest_checks"] = checks
    STATE["latest_report"] = report
    STATE["latest_report_path"] = str(report_path)

    # Export checks to SQL file and push to test database
    sql_file_path = export_checks_to_sql_file(checks)
    push_checks_to_database(checks)

    return {
        "ok": True,
        "reply": ai_message or "Profiling checks generated and executed.",
        "gemini_error": gemini_error,
        "database": database,
        "tables": len(schema.get("tables", [])),
        "relationships": len(schema.get("relationships", [])),
        "checks": checks,
        "execution": results,
        "report": report,
        "export_url": "/api/export",
        "sql_file": sql_file_path,
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/upload")
def upload_schema():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"ok": False, "error": "No file selected."}), 400

    filename = secure_filename(file.filename)
    path = UPLOAD_FOLDER / filename
    file.save(path)
    suffix = path.suffix.lower()

    try:
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            schema = schema_from_image(path)
            source_label = "schema diagram"
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            schema = parse_sql_schema(text)
            source_label = "SQL schema"
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    STATE["schema"] = schema
    STATE["last_upload"] = filename
    STATE["skills"] = load_skills()

    return jsonify(
        {
            "ok": True,
            "message": f"Loaded {source_label} from {filename}.",
            "database": schema.get("database"),
            "tables": [f"{table['schema']}.{table['table']}" for table in schema.get("tables", [])],
            "relationships": schema.get("relationships", []),
        }
    )


@app.get("/api/databases")
def get_databases():
    result = list_databases()
    if result.get("error"):
        return jsonify({"ok": False, "error": result["error"], "databases": []}), 400
    return jsonify({"ok": True, "databases": result.get("databases", [])})


@app.post("/api/discover")
def discover_schema():
    payload = request.get_json(silent=True) or {}
    database_name = payload.get("database") or request.args.get("database") or os.getenv("SQL_DATABASE", "master")
    schema = discover_schema_from_database(database_name)
    if schema.get("error"):
        return jsonify({"ok": False, "error": schema["error"]}), 400

    STATE["schema"] = schema
    STATE["last_upload"] = None
    STATE["skills"] = load_skills()

    return jsonify(
        {
            "ok": True,
            "message": f"Discovered {len(schema.get('tables', []))} tables from '{schema.get('database', database_name)}'.",
            "database": schema.get("database", database_name),
            "tables": [f"{table['schema']}.{table['table']}" for table in schema.get("tables", [])],
            "relationships": schema.get("relationships", []),
        }
    )


@app.post("/api/profile")
def profile():
    payload = request.get_json(silent=True) or {}
    result = run_profile_flow(payload)
    return jsonify(result), (200 if result.get("ok") else 400)


@app.post("/api/query")
def run_query():
    payload = request.get_json(silent=True) or {}
    sql = payload.get("sql", "")
    schema = STATE.get("schema") or {}
    if not schema.get("tables"):
        return jsonify(
            {
                "ok": False,
                "error": "Load a SQL file or discover a database before running queries.",
            }
        ), 400

    database_name = (payload.get("database") or schema.get("database") or "").strip()
    if not database_name:
        return jsonify(
            {
                "ok": False,
                "error": "Select a database before running queries.",
            }
        ), 400

    execution = execute_sql(sql, database_name)
    return jsonify(
        {
            "ok": bool(execution.get("ok")),
            "database": database_name,
            "execution": execution,
            "error": execution.get("error"),
        }
    ), (200 if execution.get("ok") else 400)


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    result = run_profile_flow(payload)
    if result.get("ok"):
        report = result.get("report", {})
        return jsonify(
            {
                "ok": True,
                "reply": result.get("reply", ""),
                "questions": [
                    {"question": reframe_question(check.get("question")), "sql": check.get("sql")}
                    for check in result.get("checks", [])
                ],
                "execution": result.get("execution", []),
                "report": report,
                "export_url": result.get("export_url"),
                "gemini_error": result.get("gemini_error"),
            }
        )
    return jsonify(result), 400


@app.get("/api/report")
def latest_report():
    if not STATE.get("latest_report"):
        return jsonify({"ok": False, "error": "No report has been generated yet."}), 404
    return jsonify({"ok": True, "report": STATE["latest_report"], "export_url": "/api/export"})


@app.get("/api/export")
def export_report():
    report_path = STATE.get("latest_report_path")
    if not report_path or not Path(report_path).exists():
        if not STATE.get("latest_report"):
            return jsonify({"ok": False, "error": "No report has been generated yet."}), 404
        report_path = str(create_xlsx_report(STATE["latest_report"]))
        STATE["latest_report_path"] = report_path
    return send_file(report_path, as_attachment=True, download_name=Path(report_path).name)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
