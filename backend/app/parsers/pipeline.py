from dataclasses import dataclass
from typing import BinaryIO

import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.file_reader import read_file


@dataclass
class ParseResult:
    data: pd.DataFrame
    row_count: int
    adapter_name: str
    data_type: str


def run_parse_pipeline(
    file: BinaryIO,
    file_type: str,
    adapter: BaseAdapter,
    password: str | None = None,
) -> ParseResult:
    rules = adapter.get_parsing_rules()
    df = read_file(
        file=file,
        file_type=file_type,
        skip_rows=rules.get("skip_rows", 0),
        sheet_name=rules.get("sheet_name"),
        header_row=rules.get("header_row", 0),
        password=password,
    )
    transformed = adapter.transform(df)
    return ParseResult(
        data=transformed,
        row_count=len(transformed),
        adapter_name=type(adapter).__name__,
        data_type=adapter.data_type,
    )
