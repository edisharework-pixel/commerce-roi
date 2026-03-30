import io
from typing import BinaryIO
import pandas as pd

def read_file(
    file: BinaryIO,
    file_type: str,
    skip_rows: int = 0,
    sheet_name: str | None = None,
    header_row: int = 0,
    password: str | None = None,
) -> pd.DataFrame:
    if file_type == "csv":
        return pd.read_csv(file, skiprows=skip_rows, encoding="utf-8-sig")
    if file_type == "xlsx":
        if password:
            import msoffcrypto
            decrypted = io.BytesIO()
            ms_file = msoffcrypto.OfficeFile(file)
            ms_file.load_key(password=password)
            ms_file.decrypt(decrypted)
            decrypted.seek(0)
            file = decrypted
        return pd.read_excel(file, sheet_name=sheet_name or 0, header=header_row + skip_rows, engine="openpyxl")
    raise ValueError(f"Unsupported file type: {file_type}")
