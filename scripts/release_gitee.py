"""创建或补齐 Gitee Release，并上传当前 ZIP 发布包。"""

from __future__ import annotations

import argparse
import configparser
import json
import mimetypes
import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from generate_version import load_version


ROOT_DIR = Path(__file__).resolve().parent.parent
GITEE_CONFIG_PATH = ROOT_DIR / ".gitee"
GITEE_TOKEN_PATH = Path.home() / ".gitee" / "TOKEN"
API_BASE_URL = "https://gitee.com/api/v5"


def parse_arguments() -> argparse.Namespace:
    """解析发行参数。"""
    parser = argparse.ArgumentParser(description="创建 Gitee Release 并上传 ZIP 发布包")
    parser.add_argument("--notes", type=Path, help="发布说明文件，默认为 dist/release_notes.md")
    parser.add_argument("--asset", type=Path, help="ZIP 文件，默认为 dist/QSerial_v<版本号>.zip")
    parser.add_argument("--prerelease", action="store_true", help="创建 Gitee 预发布版本")
    parser.add_argument("--dry-run", action="store_true", help="仅显示 Gitee Git 同步操作，不读取令牌或创建 Release")
    return parser.parse_args()


def load_gitee_config() -> tuple[str, str, str, str]:
    """读取仓库内不含敏感信息的 Gitee 仓库配置。"""
    if not GITEE_CONFIG_PATH.is_file():
        raise RuntimeError(f"未找到 Gitee 配置文件：{GITEE_CONFIG_PATH}")

    config = configparser.ConfigParser()
    config.read(GITEE_CONFIG_PATH, encoding="utf-8")
    try:
        owner = config["gitee"]["owner"].strip()
        repo = config["gitee"]["repo"].strip()
        remote = config["gitee"]["remote"].strip()
        remote_url = config["gitee"]["url"].strip()
    except KeyError as error:
        raise RuntimeError(".gitee 必须包含 [gitee]、owner、repo、remote 和 url") from error

    if not owner or not repo or not remote or not remote_url or "/" in owner or "/" in repo:
        raise RuntimeError(".gitee 中的 owner、repo、remote 和 url 必须是有效的非空值")
    return owner, repo, remote, remote_url


def run_git(*arguments: str) -> str:
    """在项目根目录执行 Git 命令并转换失败信息。"""
    environment = os.environ.copy()
    environment.setdefault("GIT_SSH_COMMAND", "ssh -o StrictHostKeyChecking=no")
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Git 命令失败：git {' '.join(arguments)}：{detail}")
    return result.stdout.strip()


def ensure_gitee_remote(remote: str, remote_url: str) -> None:
    """确保本地 Gitee 远程存在且地址与仓库配置一致。"""
    result = subprocess.run(
        ["git", "remote", "get-url", remote],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        run_git("remote", "add", remote, remote_url)
        print(f"已添加 Gitee 远程：{remote}")
        return

    existing_url = result.stdout.strip()
    if existing_url != remote_url:
        raise RuntimeError(
            f"Gitee 远程 {remote} 地址不一致：当前为 {existing_url}，配置为 {remote_url}"
        )


def push_gitee_repository(remote: str, remote_url: str) -> None:
    """同步全部本地分支与标签到 Gitee，再进行 Release 操作。"""
    ensure_gitee_remote(remote, remote_url)
    run_git("push", remote, "--all")
    run_git("push", remote, "--tags")
    print("已同步全部本地分支和标签到 Gitee")


def load_token() -> str:
    """在运行时读取用户目录下的 Gitee 令牌，不输出令牌内容。"""
    if not GITEE_TOKEN_PATH.is_file():
        raise RuntimeError(f"未找到 Gitee 令牌文件：{GITEE_TOKEN_PATH}")

    token = GITEE_TOKEN_PATH.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError(f"Gitee 令牌文件为空：{GITEE_TOKEN_PATH}")
    return token


def request_json(
    method: str,
    endpoint: str,
    token: str,
    data: dict[str, str] | None = None,
    multipart_body: bytes | None = None,
    multipart_content_type: str | None = None,
) -> Any:
    """调用 Gitee OpenAPI，并将错误转换为不含令牌的提示。"""
    url = f"{API_BASE_URL}{endpoint}"
    request_data = None
    headers = {"Accept": "application/json"}

    if method == "GET":
        query = urlencode({"access_token": token})
        url = f"{url}?{query}"
    elif multipart_body is not None:
        request_data = multipart_body
        headers["Content-Type"] = multipart_content_type or "multipart/form-data"
    else:
        request_data = urlencode({"access_token": token, **(data or {})}).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = Request(url, data=request_data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=90) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("message", detail)
        except json.JSONDecodeError:
            message = detail
        raise RuntimeError(f"Gitee API 请求失败（HTTP {error.code}）：{message}") from error
    except URLError as error:
        raise RuntimeError(f"无法连接 Gitee API：{error.reason}") from error

    return json.loads(payload) if payload else None


def verify_tag(owner: str, repo: str, tag_name: str, token: str) -> None:
    """确认镜像仓库已经同步待发布标签。"""
    tags = request_json("GET", f"/repos/{quote(owner)}/{quote(repo)}/tags", token)
    if not any(tag.get("name") == tag_name for tag in tags):
        raise RuntimeError(f"Gitee 仓库尚未同步标签 {tag_name}，请先同步镜像后重试")


def find_release(owner: str, repo: str, tag_name: str, token: str) -> dict[str, Any] | None:
    """按标签查找既有 Release，保证重复执行不会重复创建。"""
    releases = request_json("GET", f"/repos/{quote(owner)}/{quote(repo)}/releases", token)
    return next((release for release in releases if release.get("tag_name") == tag_name), None)


def get_release(owner: str, repo: str, release_id: int, token: str) -> dict[str, Any]:
    """读取 Release 详情，以便准确检查已上传附件。"""
    endpoint = f"/repos/{quote(owner)}/{quote(repo)}/releases/{release_id}"
    return request_json("GET", endpoint, token)


def create_release(
    owner: str,
    repo: str,
    tag_name: str,
    version: str,
    notes: str,
    prerelease: bool,
    token: str,
) -> dict[str, Any]:
    """创建 Gitee Release。"""
    data = {
        "tag_name": tag_name,
        "target_commitish": "master",
        "name": f"QSerial v{version}",
        "body": notes,
        "prerelease": str(prerelease).lower(),
    }
    return request_json("POST", f"/repos/{quote(owner)}/{quote(repo)}/releases", token, data)


def encode_multipart(token: str, asset_path: Path) -> tuple[bytes, str]:
    """使用标准库构造包含令牌与 ZIP 文件的 multipart 请求。"""
    boundary = f"----QSerial{secrets.token_hex(16)}"
    chunks: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )

    add_field("access_token", token)
    content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                "Content-Disposition: form-data; "
                f'name="file"; filename="{asset_path.name}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            asset_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def upload_asset(owner: str, repo: str, release_id: int, asset_path: Path, token: str) -> None:
    """向指定 Release 上传 ZIP 附件。"""
    body, content_type = encode_multipart(token, asset_path)
    endpoint = f"/repos/{quote(owner)}/{quote(repo)}/releases/{release_id}/attach_files"
    request_json("POST", endpoint, token, multipart_body=body, multipart_content_type=content_type)


def has_asset(release: dict[str, Any], asset_name: str) -> bool:
    """判断既有 Release 是否已包含同名附件。"""
    assets = release.get("assets") or release.get("attach_files") or []
    return any(asset.get("name") == asset_name for asset in assets)


def main() -> int:
    """执行 Gitee Release 发布流程。"""
    arguments = parse_arguments()
    version = load_version().removeprefix("v")
    tag_name = f"v{version}"
    notes_path = arguments.notes or ROOT_DIR / "dist" / "release_notes.md"
    asset_path = arguments.asset or ROOT_DIR / "dist" / f"QSerial_v{version}.zip"

    if not notes_path.is_file():
        raise RuntimeError(f"未找到发布说明：{notes_path}")
    if not asset_path.is_file():
        raise RuntimeError(f"未找到 ZIP 发布包：{asset_path}")

    owner, repo, remote, remote_url = load_gitee_config()
    if arguments.dry_run:
        print(f"将执行：git push {remote} --all")
        print(f"将执行：git push {remote} --tags")
        print(f"Gitee 远程地址：{remote_url}")
        return 0

    push_gitee_repository(remote, remote_url)
    token = load_token()
    notes = notes_path.read_text(encoding="utf-8")
    verify_tag(owner, repo, tag_name, token)

    release = find_release(owner, repo, tag_name, token)
    if release is None:
        release = create_release(owner, repo, tag_name, version, notes, arguments.prerelease, token)
        print(f"已创建 Gitee Release：{release.get('html_url', tag_name)}")
    else:
        print(f"复用已有 Gitee Release：{release.get('html_url', tag_name)}")

    release = get_release(owner, repo, int(release["id"]), token)
    if has_asset(release, asset_path.name):
        print(f"Release 已包含附件：{asset_path.name}")
    else:
        upload_asset(owner, repo, int(release["id"]), asset_path, token)
        print(f"已上传附件：{asset_path.name}")

    print(f"Gitee Release 发布完成：{tag_name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"发布失败：{error}", file=sys.stderr)
        raise SystemExit(1)
