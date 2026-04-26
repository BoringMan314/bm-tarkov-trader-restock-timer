import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
APP_NAME = "bm-tarkov-trader-restock-timer"
DISPLAY_TITLE = "[B.M] 塔科夫商人補貨計時 V1.0 By. [B.M] 圓周率 3.14"
APP_VERSION = "1.0.0.0"
VERSION_FILE = PROJECT_ROOT / "version_info.txt"


def clear_dir(path):
    path.mkdir(exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def add_data_arg(source, target):
    return str(source) + os.pathsep + target


def replace_exe(built_exe, final_exe):
    if final_exe.exists():
        final_exe.unlink()
    shutil.move(str(built_exe), str(final_exe))


def write_version_file():
    VERSION_FILE.write_text(
        f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040404B0',
          [
            StringStruct('CompanyName', '[B.M] 圓周率 3.14'),
            StringStruct('FileDescription', '{DISPLAY_TITLE}'),
            StringStruct('FileVersion', '1.0'),
            StringStruct('InternalName', '{APP_NAME}'),
            StringStruct('ProductName', '{DISPLAY_TITLE}'),
            StringStruct('ProductVersion', '1.0'),
            StringStruct('OriginalFilename', '{APP_NAME}.exe'),
          ],
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [0x0404, 1200])]),
  ],
)
""",
        encoding="utf-8",
    )


def check_python(mode):
    version = sys.version_info
    if mode == "win7" and not (version.major == 3 and version.minor == 8):
        raise SystemExit("Win7 build requires Python 3.8.x.")
    if mode == "win10" and not (version.major == 3 and version.minor >= 10):
        raise SystemExit("Win10 build requires Python 3.10+.")


def build(mode):
    check_python(mode)
    write_version_file()
    clear_dir(BUILD_DIR)
    clear_dir(DIST_DIR)

    exe_name = APP_NAME if mode == "win10" else APP_NAME + "_win7"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        exe_name,
        "--icon",
        str(PROJECT_ROOT / "icons" / "icon.ico"),
        "--version-file",
        str(VERSION_FILE),
        "--workpath",
        str(BUILD_DIR),
        "--distpath",
        str(DIST_DIR),
        "--specpath",
        str(PROJECT_ROOT),
        "--add-data",
        add_data_arg(PROJECT_ROOT / "icons", "icons"),
    ]

    command.append(str(PROJECT_ROOT / "main.py"))
    subprocess.check_call(command, cwd=str(PROJECT_ROOT))

    built_exe = DIST_DIR / (exe_name + ".exe")
    final_exe = PROJECT_ROOT / (exe_name + ".exe")
    replace_exe(built_exe, final_exe)

    clear_dir(BUILD_DIR)
    clear_dir(DIST_DIR)
    print("Built " + final_exe.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["win10", "win7"])
    args = parser.parse_args()
    build(args.mode)


if __name__ == "__main__":
    main()
