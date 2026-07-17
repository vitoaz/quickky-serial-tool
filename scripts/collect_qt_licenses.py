"""复制随源码保存的 Qt/PySide6 发布许可证文本。"""

import shutil
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        raise SystemExit("用法: python3 scripts/collect_qt_licenses.py <目标目录>")
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent / "licenses"
    for filename in ("LGPL-3.0.txt", "GPL-3.0.txt"):
        source = root / filename
        if not source.exists() or source.stat().st_size < 1000:
            raise RuntimeError(f"缺少完整许可证文本: {source}")
        shutil.copy2(source, target / filename)
    print(f"已复制 LGPLv3 与 GPLv3 完整许可证文本到 {target}")


if __name__ == "__main__":
    main()
