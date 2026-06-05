"""共用 .bas 編輯工具(Big5 + CRLF byte-level safe)。

AK_CHT.bas 是 Big5 編碼 + CRLF 行結尾,Python 處理時必須:
1. 用 binary mode 讀寫,絕對不 decode 成 str
2. 行結尾以 b'\\r\\n' 為單位
3. 字串字面值若需匹配 Big5 中文,直接用 b'...' bytes

提供:
- BasFile:封裝 read/write
- find_line:依「行號:」或「Sub Name」找行 index
- insert_after / insert_before:行級插入
- replace_line:行級替換
- append_sub:檔尾追加新 Sub

所有 helper 都回傳/處理 bytes,不要洩漏 str。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

CRLF = b"\r\n"


@dataclass
class BasFile:
    path: Path
    lines: list[bytes] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | str) -> "BasFile":
        p = Path(path)
        data = p.read_bytes()
        # 用 \r\n split,保留尾段(可能無 \r\n)
        parts = data.split(CRLF)
        # 若檔尾有 \r\n,split 後最後一個是 b''
        if parts and parts[-1] == b"":
            parts = parts[:-1]
        return cls(path=p, lines=parts)

    def save(self, dst: Path | str | None = None) -> Path:
        out = Path(dst) if dst else self.path
        data = CRLF.join(self.lines) + CRLF
        out.write_bytes(data)
        return out

    def find_line(self, needle: bytes) -> int:
        """回傳第一個包含 needle 的行 index;找不到 raise ValueError。"""
        for i, line in enumerate(self.lines):
            if needle in line:
                return i
        raise ValueError(f"找不到包含 {needle!r} 的行")

    def find_line_starting_with(self, prefix: bytes) -> int:
        """回傳第一個以 prefix 開頭的行 (允許前導空白)。"""
        for i, line in enumerate(self.lines):
            stripped = line.lstrip(b" \t")
            if stripped.startswith(prefix):
                return i
        raise ValueError(f"找不到以 {prefix!r} 開頭的行")

    def find_basic_line(self, line_no: int) -> int:
        """找 BASIC 古典行號(line_no 開頭),如 1000 或 6000。

        匹配規則:行(去除前導空白)以 `<line_no> ` 或 `<line_no>:` 或單獨 `<line_no>` 開頭。
        """
        prefix1 = f"{line_no} ".encode("ascii")
        prefix2 = f"{line_no}:".encode("ascii")
        for i, line in enumerate(self.lines):
            stripped = line.lstrip(b" \t")
            if stripped.startswith(prefix1) or stripped.startswith(prefix2):
                return i
            if stripped == str(line_no).encode("ascii"):
                return i
        raise ValueError(f"找不到 BASIC 行號 {line_no}")

    def insert_after(self, index: int, new_lines: list[bytes]) -> None:
        for off, l in enumerate(new_lines):
            self.lines.insert(index + 1 + off, l)

    def insert_before(self, index: int, new_lines: list[bytes]) -> None:
        for off, l in enumerate(new_lines):
            self.lines.insert(index + off, l)

    def replace_line(self, index: int, new_line: bytes) -> None:
        self.lines[index] = new_line

    def replace_lines(self, start: int, end: int, new_lines: list[bytes]) -> None:
        """把 [start, end) 範圍取代成 new_lines。"""
        self.lines[start:end] = new_lines

    def append(self, new_lines: list[bytes]) -> None:
        self.lines.extend(new_lines)

    def append_sub(self, sub_code: str) -> None:
        """把整段 Sub 程式碼接到檔尾。sub_code 是 str(假設只含 ASCII)。

        若需中文註解請改用 append() 傳 bytes(Big5 encoded)。
        """
        for line in sub_code.splitlines():
            self.lines.append(line.encode("ascii"))


def encode_big5(text: str) -> bytes:
    """把 Python str(Unicode)轉成 Big5 bytes,以便嵌入 .bas 字串字面值。"""
    return text.encode("big5")


def big5_string_literal(text: str) -> bytes:
    """產生 BASIC 字串字面值 "..." 的 bytes(含外層引號)。"""
    return b'"' + encode_big5(text) + b'"'
