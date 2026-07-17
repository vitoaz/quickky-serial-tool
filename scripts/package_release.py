"""创建包含可执行文件与许可证的 ZIP 发布包。"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from generate_version import VERSION


ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
EXE_FILE = DIST_DIR / "QSerial.exe"
LICENSE_FILE = DIST_DIR / "LICENSE"
LICENSES_DIR = DIST_DIR / "licenses"
ARCHIVE_FILE = DIST_DIR / f"QSerial_v{VERSION}.zip"


def package_release() -> None:
    """将发布所需的 EXE 和许可证压缩为 ZIP 文件。"""
    required_paths = (EXE_FILE, LICENSE_FILE, LICENSES_DIR)
    missing_paths = [str(path) for path in required_paths if not path.exists()]
    if missing_paths:
        raise FileNotFoundError("缺少发布文件：" + "、".join(missing_paths))

    with ZipFile(ARCHIVE_FILE, "w", ZIP_DEFLATED) as archive:
        archive.write(EXE_FILE, EXE_FILE.name)
        archive.write(LICENSE_FILE, LICENSE_FILE.name)
        for license_file in LICENSES_DIR.rglob("*"):
            if license_file.is_file():
                archive.write(license_file, license_file.relative_to(DIST_DIR).as_posix())

    print(f"发布包已生成：{ARCHIVE_FILE}")


if __name__ == "__main__":
    package_release()
