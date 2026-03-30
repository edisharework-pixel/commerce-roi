import pandas as pd

def apply_column_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    reverse = {}
    for target, source in mapping.items():
        if source in df.columns:
            reverse[source] = target
    return df.rename(columns=reverse)

def apply_null_values(df: pd.DataFrame, null_values: list[str]) -> pd.DataFrame:
    return df.replace(null_values, pd.NA)

def parse_date_column(df: pd.DataFrame, column: str, date_format: str | None = None) -> pd.DataFrame:
    df = df.copy()
    if column not in df.columns:
        return df
    if date_format == "YYYY.MM.DD.":
        df[column] = df[column].astype(str).str.rstrip(".")
        df[column] = pd.to_datetime(df[column], format="%Y.%m.%d")
    else:
        df[column] = pd.to_datetime(df[column])
    return df
