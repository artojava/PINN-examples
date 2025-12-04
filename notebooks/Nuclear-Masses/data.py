import logging
from typing import Any

import pandas as pd  # type: ignore
import requests  # type: ignore

logger = logging.getLogger(__name__)


class AME2020Parser:
    """Downloader and parser for AME2020 `mass_1.mas20.txt` files.
    Returns a pandas.DataFrame with coerced dtypes and estimated flags.
    """

    def __init__(self, header_lines=36):
        self.header_lines = header_lines
        # base dtypes for known columns (estimated flags added later)
        self.column_types = {
            "N-Z": int,
            "N": int,
            "Z": int,
            "A": int,
            "ELEMENT_SYMBOL": str,
            "O": str,
            "MASS EXCESS (keV)": float,
            "SIGMA MASS EXCESS (keV)": float,
            "MASS EXCESS ESTIMATED": bool,
            "BINDING ENERGY/A (keV)": float,
            "SIGMA BINDING ENERGY/A (keV)": float,
            "BINDING ENERGY ESTIMATED": bool,
            "BETA DECAY TYPE": str,
            "BETA-DECAY ENERGY (keV)": float,
            "BETA DECAY ENERGY ESTIMATED": bool,
            "SIGMA BETA-DECAY ENERGY (keV)": float,
            "ATOMIC MASS (micro-u)": float,
            "SIGMA ATOMIC MASS (micro-u)": float,
            "ATOMIC MASS ESTIMATED": bool,
        }
        self.estimated_map = {
            "MASS EXCESS (keV)": "MASS EXCESS ESTIMATED",
            "BINDING ENERGY/A (keV)": "BINDING ENERGY ESTIMATED",
            "BETA-DECAY ENERGY (keV)": "BETA DECAY ENERGY ESTIMATED",
            "ATOMIC MASS (micro-u)": "ATOMIC MASS ESTIMATED",
        }

    def download(self, url: str) -> list[str]:
        logger.info(f"Downloading and parsing AME2020 mass table from {url}")
        r = requests.get(url)
        r.raise_for_status()
        return r.text.splitlines()

    def _normalize_row(self, line: str) -> list[Any]:
        # Remove leading control char and split tokens
        row = line[1:].split()
        # combine third-last and second-last columns and remove second-last (preserves signs)
        if len(row) >= 3:
            row[-3] = row[-3] + row[-2]
            del row[-2]
        return row

    def parse(self, lines: list[str]) -> pd.DataFrame:
        data = []
        for line in lines[self.header_lines :]:
            if line.startswith("#") or line.strip() == "":
                continue
            row = self._normalize_row(line)

            # if beta-decay energy is missing (marked by '*'), fill with None and add sigma placeholder
            if len(row) >= 3 and "*" in (row[-3] or ""):
                row[-3] = None
                row.insert(-2, None)

            # ensure O column exists (5th position)
            expected_nonestimated = len(self.column_types) - len(self.estimated_map)
            if len(row) < expected_nonestimated:
                row.insert(5, None)

            entry: dict[str, Any] = {}
            detected_estimated = {v: False for v in self.estimated_map.values()}

            cols = [
                c
                for c in self.column_types.keys()
                if c not in self.estimated_map.values()
            ]
            for i, col in enumerate(cols):
                token = None
                if i < len(row):
                    token = row[i]
                if isinstance(token, str) and token != "":
                    if token.endswith("#"):
                        if col in self.estimated_map:
                            detected_estimated[self.estimated_map[col]] = True
                        token = token.rstrip("#")
                    if "*" in token:
                        token = None
                        if col in self.estimated_map:
                            detected_estimated[self.estimated_map[col]] = True
                entry[col] = token

            for flag_col in detected_estimated:
                entry[flag_col] = bool(detected_estimated[flag_col])

            data.append(entry)

        df = pd.DataFrame(data)

        # Extend column_types with estimated flags if missing
        extended_types = dict(self.column_types)
        for flag_col in self.estimated_map.values():
            if flag_col not in extended_types:
                extended_types[flag_col] = bool

        # Convert numeric-like columns to proper numeric types where possible
        numeric_cols = [c for c, t in extended_types.items() if t in (int, float)]
        for c in numeric_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # Cast boolean estimated flags
        for c, t in extended_types.items():
            if t is bool and c in df.columns:
                df[c] = df[c].fillna(False).astype(bool)

        # Try to apply dtypes where possible
        present_types = {c: t for c, t in extended_types.items() if c in df.columns}
        try:
            df = df.astype(present_types)
        except Exception:
            logger.warning(
                "Some columns could not be cast to the requested types; kept best-effort conversions."
            )

        return df

    def load(self, url: str) -> pd.DataFrame:
        lines = self.download(url)
        return self.parse(lines)
