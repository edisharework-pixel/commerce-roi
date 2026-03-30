from abc import ABC, abstractmethod
import pandas as pd


class BaseAdapter(ABC):
    platform_name: str
    data_type: str

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def get_column_mapping(self) -> dict[str, str]:
        return {}

    def get_parsing_rules(self) -> dict:
        return {}
