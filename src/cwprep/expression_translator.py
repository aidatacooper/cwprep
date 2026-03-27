# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""
Tableau Prep Expression → ANSI SQL Translator

Translates Tableau Prep calculation formulas to equivalent ANSI SQL expressions
using regex-based pattern matching. Covers ~80% of common scenarios; unsupported
functions are preserved with /* [UNSUPPORTED] */ SQL comments.

Usage:
    from cwprep.expression_translator import ExpressionTranslator

    translator = ExpressionTranslator()
    sql_expr = translator.translate("[Amount] > 100 AND ISNULL([Name])")
    # => "Amount" > 100 AND ("Name") IS NULL
"""

import re
from typing import List, Tuple


class ExpressionTranslator:
    """Translate Tableau Prep calculation syntax to ANSI SQL expressions."""

    # Functions that are directly compatible with ANSI SQL (no translation needed)
    _PASSTHROUGH_FUNCS = {
        # Math
        "ABS", "ROUND", "CEILING", "FLOOR", "POWER", "SQRT", "LN", "LOG",
        "EXP", "SIGN", "PI", "ACOS", "ASIN", "ATAN", "ATAN2", "COS",
        "SIN", "TAN", "COT",
        # String (ANSI compatible)
        "UPPER", "LOWER", "TRIM", "LTRIM", "RTRIM", "REPLACE",
        "LEFT", "RIGHT", "ASCII",
        # Aggregate
        "SUM", "AVG", "COUNT", "MIN", "MAX", "MEDIAN",
        "STDEV", "STDEVP", "VAR", "VARP",
    }

    # Functions that cannot be translated to standard SQL
    _UNSUPPORTED_FUNCS = [
        "REGEXP_REPLACE", "REGEXP_MATCH", "REGEXP_EXTRACT",
        "REGEXP_EXTRACT_NTH",
        "SPLIT", "FINDNTH", "SPACE", "CHAR",
        "HEXBINX", "HEXBINY", "RADIANS", "SQUARE", "DIV",
        "DATEPARSE", "DATENAME", "MAKEDATETIME", "MAKETIME",
        "ISDATE", "ISBLANK",
        "LAST_VALUE", "LOOKUP", "NTILE",
        "RANK", "RANK_DENSE", "RANK_MODIFIED", "RANK_PERCENTILE",
        "ROW_NUMBER", "RUNNING_AVG", "RUNNING_SUM",
        "PERCENTILE", "ATTR",
    ]

    def translate(self, expr: str) -> str:
        """Translate a Tableau Prep expression to ANSI SQL.

        Args:
            expr: Tableau Prep calculation formula

        Returns:
            Equivalent ANSI SQL expression
        """
        if not expr:
            return expr

        result = expr

        # Order matters: translate inner constructs before outer ones
        result = self._translate_unsupported(result)
        result = self._translate_if_then(result)
        result = self._translate_iif(result)
        result = self._translate_case_when(result)
        result = self._translate_isnull(result)
        result = self._translate_ifnull(result)
        result = self._translate_zn(result)
        result = self._translate_contains(result)
        result = self._translate_startswith(result)
        result = self._translate_endswith(result)
        result = self._translate_len(result)
        result = self._translate_mid(result)
        result = self._translate_find(result)
        result = self._translate_proper(result)
        result = self._translate_countd(result)
        result = self._translate_datepart(result)
        result = self._translate_dateadd(result)
        result = self._translate_datediff(result)
        result = self._translate_datetrunc(result)
        result = self._translate_year_month_day(result)
        result = self._translate_now_today(result)
        result = self._translate_makedate(result)
        result = self._translate_type_cast(result)
        result = self._translate_field_refs(result)
        result = self._translate_operators(result)

        return result

    # ------------------------------------------------------------------
    # Field references: [Field Name] → "Field Name"
    # ------------------------------------------------------------------
    def _translate_field_refs(self, expr: str) -> str:
        return re.sub(r'\[([^\]]+)\]', r'"\1"', expr)

    # ------------------------------------------------------------------
    # Operators: == → =
    # ------------------------------------------------------------------
    def _translate_operators(self, expr: str) -> str:
        # Replace == with = (but not inside strings)
        return re.sub(r'(?<!=)==(?!=)', '=', expr)

    # ------------------------------------------------------------------
    # IF / THEN / ELSEIF / ELSE / END → CASE WHEN
    # ------------------------------------------------------------------
    def _translate_if_then(self, expr: str) -> str:
        # Multi-step: first handle ELSEIF → WHEN
        result = re.sub(
            r'\bELSEIF\b', 'WHEN',
            expr, flags=re.IGNORECASE
        )
        # IF ... THEN → CASE WHEN ... THEN
        result = re.sub(
            r'\bIF\b\s+', 'CASE WHEN ',
            result, flags=re.IGNORECASE
        )
        # ELSE stays the same, END stays the same — compatible with SQL CASE
        return result

    # ------------------------------------------------------------------
    # CASE [field] WHEN value THEN ... — already valid SQL
    # ------------------------------------------------------------------
    def _translate_case_when(self, expr: str) -> str:
        # Tableau's CASE WHEN is already SQL-compatible
        return expr

    # ------------------------------------------------------------------
    # IIF(condition, then, else) → CASE WHEN condition THEN then ELSE else END
    # ------------------------------------------------------------------
    def _translate_iif(self, expr: str) -> str:
        pattern = re.compile(
            r'\bIIF\s*\(\s*(.+?)\s*,\s*(.+?)\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        def _replace(m):
            cond, then_val, else_val = m.group(1), m.group(2), m.group(3)
            return f"CASE WHEN {cond} THEN {then_val} ELSE {else_val} END"
        return pattern.sub(_replace, expr)

    # ------------------------------------------------------------------
    # ISNULL(expr) → (expr) IS NULL
    # ------------------------------------------------------------------
    def _translate_isnull(self, expr: str) -> str:
        pattern = re.compile(r'\bISNULL\s*\(\s*(.+?)\s*\)', re.IGNORECASE)
        return pattern.sub(r'(\1) IS NULL', expr)

    # ------------------------------------------------------------------
    # IFNULL(a, b) → COALESCE(a, b)
    # ------------------------------------------------------------------
    def _translate_ifnull(self, expr: str) -> str:
        return re.sub(r'\bIFNULL\s*\(', 'COALESCE(', expr, flags=re.IGNORECASE)

    # ------------------------------------------------------------------
    # ZN(expr) → COALESCE(expr, 0)
    # ------------------------------------------------------------------
    def _translate_zn(self, expr: str) -> str:
        pattern = re.compile(r'\bZN\s*\(\s*(.+?)\s*\)', re.IGNORECASE)
        return pattern.sub(r'COALESCE(\1, 0)', expr)

    # ------------------------------------------------------------------
    # CONTAINS(string, substring) → string LIKE '%' || substring || '%'
    # ------------------------------------------------------------------
    def _translate_contains(self, expr: str) -> str:
        pattern = re.compile(
            r'\bCONTAINS\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        return pattern.sub(r"\1 LIKE '%' || \2 || '%'", expr)

    # ------------------------------------------------------------------
    # STARTSWITH(string, sub) → string LIKE sub || '%'
    # ------------------------------------------------------------------
    def _translate_startswith(self, expr: str) -> str:
        pattern = re.compile(
            r'\bSTARTSWITH\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        return pattern.sub(r"\1 LIKE \2 || '%'", expr)

    # ------------------------------------------------------------------
    # ENDSWITH(string, sub) → string LIKE '%' || sub
    # ------------------------------------------------------------------
    def _translate_endswith(self, expr: str) -> str:
        pattern = re.compile(
            r'\bENDSWITH\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        return pattern.sub(r"\1 LIKE '%' || \2", expr)

    # ------------------------------------------------------------------
    # LEN(s) → LENGTH(s)
    # ------------------------------------------------------------------
    def _translate_len(self, expr: str) -> str:
        return re.sub(r'\bLEN\s*\(', 'LENGTH(', expr, flags=re.IGNORECASE)

    # ------------------------------------------------------------------
    # MID(s, start, len) → SUBSTRING(s FROM start FOR len)
    # MID(s, start)      → SUBSTRING(s FROM start)
    # ------------------------------------------------------------------
    def _translate_mid(self, expr: str) -> str:
        # Three-argument form
        pattern3 = re.compile(
            r'\bMID\s*\(\s*(.+?)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
            re.IGNORECASE
        )
        result = pattern3.sub(r'SUBSTRING(\1 FROM \2 FOR \3)', expr)

        # Two-argument form
        pattern2 = re.compile(
            r'\bMID\s*\(\s*(.+?)\s*,\s*(\d+)\s*\)',
            re.IGNORECASE
        )
        result = pattern2.sub(r'SUBSTRING(\1 FROM \2)', result)
        return result

    # ------------------------------------------------------------------
    # FIND(string, substring) → POSITION(substring IN string)
    # ------------------------------------------------------------------
    def _translate_find(self, expr: str) -> str:
        pattern = re.compile(
            r'\bFIND\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        return pattern.sub(r'POSITION(\2 IN \1)', expr)

    # ------------------------------------------------------------------
    # PROPER(s) → INITCAP(s)
    # ------------------------------------------------------------------
    def _translate_proper(self, expr: str) -> str:
        return re.sub(r'\bPROPER\s*\(', 'INITCAP(', expr, flags=re.IGNORECASE)

    # ------------------------------------------------------------------
    # COUNTD(expr) → COUNT(DISTINCT expr)
    # ------------------------------------------------------------------
    def _translate_countd(self, expr: str) -> str:
        pattern = re.compile(r'\bCOUNTD\s*\(\s*(.+?)\s*\)', re.IGNORECASE)
        return pattern.sub(r'COUNT(DISTINCT \1)', expr)

    # ------------------------------------------------------------------
    # DATEPART('part', date) → EXTRACT(part FROM date)
    # ------------------------------------------------------------------
    def _translate_datepart(self, expr: str) -> str:
        pattern = re.compile(
            r'\bDATEPART\s*\(\s*[\'"](\w+)[\'"]\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        return pattern.sub(r'EXTRACT(\1 FROM \2)', expr)

    # ------------------------------------------------------------------
    # DATEADD('part', n, date) → date + INTERVAL 'n' part
    # ------------------------------------------------------------------
    def _translate_dateadd(self, expr: str) -> str:
        pattern = re.compile(
            r'\bDATEADD\s*\(\s*[\'"](\w+)[\'"]\s*,\s*(.+?)\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        def _replace(m):
            part, interval, date = m.group(1), m.group(2), m.group(3)
            return f"{date} + INTERVAL '{interval}' {part.upper()}"
        return pattern.sub(_replace, expr)

    # ------------------------------------------------------------------
    # DATEDIFF('part', start, end) → approximate translation
    # ------------------------------------------------------------------
    def _translate_datediff(self, expr: str) -> str:
        pattern = re.compile(
            r'\bDATEDIFF\s*\(\s*[\'"](\w+)[\'"]\s*,\s*(.+?)\s*,\s*(.+?)\s*\)',
            re.IGNORECASE
        )
        def _replace(m):
            part, start, end = m.group(1), m.group(2), m.group(3)
            return f"/* DATEDIFF({part}) */ EXTRACT(EPOCH FROM ({end}) - ({start}))"
        return pattern.sub(_replace, expr)

    # ------------------------------------------------------------------
    # DATETRUNC('part', date) → DATE_TRUNC('part', date)
    # ------------------------------------------------------------------
    def _translate_datetrunc(self, expr: str) -> str:
        return re.sub(
            r'\bDATETRUNC\s*\(', "DATE_TRUNC(",
            expr, flags=re.IGNORECASE
        )

    # ------------------------------------------------------------------
    # YEAR(d)/MONTH(d)/DAY(d) → EXTRACT(YEAR/MONTH/DAY FROM d)
    # ------------------------------------------------------------------
    def _translate_year_month_day(self, expr: str) -> str:
        for part in ("YEAR", "MONTH", "DAY"):
            pattern = re.compile(
                rf'\b{part}\s*\(\s*(.+?)\s*\)',
                re.IGNORECASE
            )
            expr = pattern.sub(rf'EXTRACT({part} FROM \1)', expr)
        return expr

    # ------------------------------------------------------------------
    # NOW() → CURRENT_TIMESTAMP, TODAY() → CURRENT_DATE
    # ------------------------------------------------------------------
    def _translate_now_today(self, expr: str) -> str:
        expr = re.sub(r'\bNOW\s*\(\s*\)', 'CURRENT_TIMESTAMP', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bTODAY\s*\(\s*\)', 'CURRENT_DATE', expr, flags=re.IGNORECASE)
        return expr

    # ------------------------------------------------------------------
    # MAKEDATE(y, m, d) → MAKE_DATE(y, m, d)  (SQL:2003)
    # ------------------------------------------------------------------
    def _translate_makedate(self, expr: str) -> str:
        return re.sub(
            r'\bMAKEDATE\s*\(', 'MAKE_DATE(',
            expr, flags=re.IGNORECASE
        )

    # ------------------------------------------------------------------
    # INT(x) → CAST(x AS INTEGER)
    # FLOAT(x) → CAST(x AS REAL)
    # STR(x) → CAST(x AS VARCHAR)
    # DATE(x) → CAST(x AS DATE)
    # DATETIME(x) → CAST(x AS TIMESTAMP)
    # ------------------------------------------------------------------
    def _translate_type_cast(self, expr: str) -> str:
        cast_map = {
            "INT": "INTEGER",
            "FLOAT": "REAL",
            "STR": "VARCHAR",
            "DATE": "DATE",
            "DATETIME": "TIMESTAMP",
        }
        for func, sql_type in cast_map.items():
            pattern = re.compile(
                rf'\b{func}\s*\(\s*(.+?)\s*\)',
                re.IGNORECASE
            )
            expr = pattern.sub(rf'CAST(\1 AS {sql_type})', expr)
        return expr

    # ------------------------------------------------------------------
    # Unsupported functions → /* [UNSUPPORTED: FUNC] */ original
    # ------------------------------------------------------------------
    def _translate_unsupported(self, expr: str) -> str:
        for func in self._UNSUPPORTED_FUNCS:
            pattern = re.compile(
                rf'(\b{func}\s*\([^)]*\))',
                re.IGNORECASE
            )
            expr = pattern.sub(rf'/* UNSUPPORTED: {func} */ \1', expr)
        return expr
