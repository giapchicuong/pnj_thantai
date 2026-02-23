#!/usr/bin/env python3
"""
Import VPS từ Excel, cập nhật config và chạy 5 workers toàn bộ 1-70.
Chạy: python3 import_excel_and_run.py /path/to/file.xlsx
"""
import xml.etree.ElementTree as ET
import zipfile
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _get_si_text(si, ns) -> str:
    """Lấy text từ thẻ <si> (có thể có <t> hoặc <r><t>)."""
    t = si.find("main:t", ns)
    if t is not None and t.text:
        return t.text
    parts = []
    for r in si.findall("main:r", ns):
        rt = r.find("main:t", ns)
        if rt is not None and rt.text:
            parts.append(rt.text)
    return "".join(parts) if parts else ""


def parse_xlsx(xlsx_path: str) -> dict[int, tuple[str, str]]:
    """Parse Excel, trả về {instance_num: (ip, password)} cho 1-70."""
    result = {}
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(xlsx_path, "r") as zf:
        with zf.open("xl/sharedStrings.xml") as f:
            tree = ET.parse(f)
            strings = [_get_si_text(si, ns) for si in tree.getroot().findall(".//main:si", ns)]

        with zf.open("xl/worksheets/sheet1.xml") as f:
            tree = ET.parse(f)
            for row in tree.getroot().findall(".//main:row", ns):
                cells = {}
                for c in row.findall("main:c", ns):
                    ref = c.get("r", "")
                    col = ref[0] if ref else ""
                    v = c.find("main:v", ns)
                    if v is not None and v.text is not None:
                        val = v.text
                        if c.get("t") == "s":
                            val = strings[int(val)] if int(val) < len(strings) else ""
                        cells[col] = str(val)
                instance_name = cells.get("B", "")
                ip = cells.get("D", "") or cells.get("C", "")
                pw = cells.get("F", "") or cells.get("E", "")
                m = re.search(r"pn[jg]_than_tai_(\d+)", instance_name, re.I)
                if m and ip and pw and re.match(r"\d+\.\d+\.\d+\.\d+", ip):
                    num = int(m.group(1))
                    if 1 <= num <= 70:
                        result[num] = (ip.strip(), pw.strip())
    return result


def update_check_script(data: dict[int, tuple[str, str]]):
    """Cập nhật get_ip và get_pw trong check_and_fix_1_70.sh"""
    path = SCRIPT_DIR / "check_and_fix_1_70.sh"
    text = path.read_text(encoding="utf-8")

    ip_lines = [f'    {i}) echo "{ip}";;' for i in sorted(data) for (ip, _) in [data[i]]]
    pw_lines = [f'    {i}) echo "{pw}";;' for i in sorted(data) for (_, pw) in [data[i]]]

    new_get_ip = "get_ip() {\n  case \"$1\" in\n" + "\n".join(ip_lines) + "\n    *) echo \"\";;\n  esac\n}"
    new_get_pw = "get_pw() {\n  case \"$1\" in\n" + "\n".join(pw_lines) + "\n    *) echo \"\";;\n  esac\n}"

    text = re.sub(r"get_ip\(\) \{[^}]*\n  esac\n\}", new_get_ip, text, count=1, flags=re.DOTALL)
    text = re.sub(r"get_pw\(\) \{[^}]*\n  esac\n\}", new_get_pw, text, count=1, flags=re.DOTALL)
    path.write_text(text, encoding="utf-8")
    print("[*] Đã cập nhật check_and_fix_1_70.sh")


def main():
    args = sys.argv[1:]
    no_run = "--no-run" in args
    if "--no-run" in args:
        args.remove("--no-run")
    xlsx = args[0] if args else "/Users/giapchicuong/Desktop/3829864_260223155302.xlsx"

    if not Path(xlsx).exists():
        print(f"[!] Không tìm thấy: {xlsx}")
        sys.exit(1)

    print(f"[*] Đọc Excel: {xlsx}")
    data = parse_xlsx(xlsx)

    if len(data) < 70:
        print(f"[!] Tìm thấy {len(data)}/70 instance. Thiếu: {set(range(1,71)) - set(data.keys())}")
    else:
        print(f"[*] Tìm thấy {len(data)} instance: {sorted(data.keys())}")
    for k in sorted(data.keys()):
        ip, pw = data[k]
        print(f"    {k}: {ip}")

    update_check_script(data)

    if no_run:
        print("[*] (--no-run) Bỏ qua chạy. Chạy thủ công: bash check_and_fix_1_70.sh --all")
    else:
        print("[*] Chạy: bash check_and_fix_1_70.sh --all")
        subprocess.run(["bash", str(SCRIPT_DIR / "check_and_fix_1_70.sh"), "--all"], cwd=SCRIPT_DIR)


if __name__ == "__main__":
    main()
