import io
import pytest
import pandas as pd
from app.parsers.file_reader import read_file

def test_read_csv_file():
    csv_content = "이름,수량,금액\n상품A,10,50000\n상품B,20,80000"
    buffer = io.BytesIO(csv_content.encode("utf-8-sig"))
    df = read_file(buffer, file_type="csv")
    assert len(df) == 2
    assert list(df.columns) == ["이름", "수량", "금액"]

def test_read_csv_with_skip_rows():
    csv_content = "제목행 무시\n이름,수량\n상품A,10\n상품B,20"
    buffer = io.BytesIO(csv_content.encode("utf-8-sig"))
    df = read_file(buffer, file_type="csv", skip_rows=1)
    assert len(df) == 2
    assert "이름" in df.columns

def test_read_xlsx_file(tmp_path):
    df_orig = pd.DataFrame({"상품명": ["A", "B"], "금액": [1000, 2000]})
    path = tmp_path / "test.xlsx"
    df_orig.to_excel(path, index=False)
    with open(path, "rb") as f:
        df = read_file(f, file_type="xlsx")
    assert len(df) == 2

def test_read_file_unsupported_type():
    buffer = io.BytesIO(b"data")
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_file(buffer, file_type="json")
