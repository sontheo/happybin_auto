"""Check official releases and stage a verified Windows distribution."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

from app_version import VERSION

API = "https://api.github.com/repos/sontheo/happybin_auto/releases/latest"
ASSET = "HappybinAuto-windows-x64.zip"
MAX_ARCHIVE = 1024 * 1024 * 1024
MAX_EXTRACTED = 3 * 1024 * 1024 * 1024


def version_tuple(value: str) -> tuple[int, ...]:
    if not re.fullmatch(r"v?\d+\.\d+\.\d+", value):
        raise ValueError("버전은 x.y.z 형식이어야 합니다")
    return tuple(map(int, value.lstrip("v").split(".")))


def check_update() -> dict | None:
    request = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": "HappybinAuto-Updater"})
    with urllib.request.urlopen(request, timeout=10) as response:
        release = json.load(response)
    if release.get("draft") or release.get("prerelease") or version_tuple(release["tag_name"]) <= version_tuple(VERSION):
        return None
    for asset in release.get("assets", []):
        digest = asset.get("digest") or ""
        url = asset.get("browser_download_url", "")
        tag = release["tag_name"]
        expected_url = f"https://github.com/sontheo/happybin_auto/releases/download/{tag}/{ASSET}"
        if asset.get("name") == ASSET and url == expected_url and re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            return {"version": tag, "url": url, "digest": digest[7:]}
    return None


def stage_update(release: dict) -> Path:
    stage = Path(tempfile.mkdtemp(prefix="happybin-update-"))
    try:
        archive = stage / ASSET
        request = urllib.request.Request(release["url"], headers={"User-Agent": "HappybinAuto-Updater"})
        digest = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(request, timeout=30) as response, archive.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_ARCHIVE:
                    raise ValueError("업데이트 파일이 너무 큽니다")
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != release["digest"]:
            raise ValueError("업데이트 파일의 SHA-256 검증에 실패했습니다")
        with zipfile.ZipFile(archive) as zipped:
            total = 0
            for item in zipped.infolist():
                path = PurePosixPath(item.filename)
                total += item.file_size
                if (not path.parts or path.parts[0] != "HappybinAuto" or
                    any(part in ("..", ".") or ":" in part or "\\" in part for part in path.parts) or
                    (item.external_attr >> 16) & 0o170000 == 0o120000 or total > MAX_EXTRACTED):
                    raise ValueError("안전하지 않은 업데이트 압축 파일입니다")
            zipped.extractall(stage)
        app = stage / "HappybinAuto"
        if not (app / "HappybinAuto.exe").is_file() or not (app / "_internal").is_dir():
            raise ValueError("업데이트 배포 파일이 올바르지 않습니다")
        return stage
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


# The helper runs independently so the application can release its files first.
_SCRIPT = r'''
param([int]$AppPid, [string]$AppDir, [string]$Stage)
$ErrorActionPreference = 'Stop'
$backup = Join-Path $Stage 'backup'
$new = Join-Path $Stage 'HappybinAuto'
New-Item -ItemType Directory -Path $backup | Out-Null
try {
    Wait-Process -Id $AppPid -ErrorAction SilentlyContinue
    foreach ($name in @('HappybinAuto.exe', '_internal')) {
        Move-Item -LiteralPath (Join-Path $AppDir $name) -Destination $backup
    }
    foreach ($name in @('HappybinAuto.exe', '_internal')) {
        Move-Item -LiteralPath (Join-Path $new $name) -Destination $AppDir
    }
    Start-Process -FilePath (Join-Path $AppDir 'HappybinAuto.exe') -WorkingDirectory $AppDir
    Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue
} catch {
    foreach ($name in @('HappybinAuto.exe', '_internal')) {
        $old = Join-Path $backup $name
        if (Test-Path -LiteralPath $old) {
            Remove-Item -LiteralPath (Join-Path $AppDir $name) -Recurse -Force -ErrorAction SilentlyContinue
            Move-Item -LiteralPath $old -Destination $AppDir -ErrorAction SilentlyContinue
        }
    }
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show('업데이트에 실패했습니다. 기존 파일 복원을 시도했습니다. 재실행이 안 되면 최신 릴리스를 다시 내려받으세요.', '업데이트 실패') | Out-Null
}
'''


def launch_installer(stage: Path) -> None:
    app_dir = Path(sys.executable).resolve().parent
    if not (app_dir / "_internal").is_dir():
        raise ValueError("설치 폴더를 찾을 수 없습니다")
    script = stage / "install.ps1"
    script.write_text(_SCRIPT, encoding="utf-8-sig")
    subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "B", "-File", str(script),
                      str(os.getpid()), str(app_dir), str(stage)], creationflags=subprocess.CREATE_NO_WINDOW)
