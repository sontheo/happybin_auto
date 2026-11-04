"""
공통 설정

카페 목적지는 사용자 설정을 우선하고 환경변수를 기본값으로 사용합니다.
"""
import os
from urllib.parse import urlsplit
from modules.user_manager import get_or_create_config

# ──────────────────────────────────────────────
# 카페 설정 (미설정 시 카페 작업 건너뜀)
# ──────────────────────────────────────────────
DEFAULT_CAFE_ID = int(os.environ.get("HAPPYBIN_CAFE_ID", "0"))
DEFAULT_CAFE_URL = os.environ.get("HAPPYBIN_CAFE_URL", "").strip().rstrip("/")
CAFE_ID, CAFE_URL = DEFAULT_CAFE_ID, DEFAULT_CAFE_URL
CAFE_WRITE_URL = (
    f"https://cafe.naver.com/ca-fe/cafes/{CAFE_ID}/articles/write?boardType=L"
    if CAFE_ID > 0 and CAFE_URL else ""
)


def validate_cafe(id_text: str, url: str) -> tuple[int, str]:
    """Validate a destination without requiring access to NAVER."""
    id_text, url = str(id_text).strip(), url.strip().rstrip("/")
    if id_text in ("", "0") and not url:
        return 0, ""
    if not id_text.isascii() or not id_text.isdigit() or int(id_text) <= 0:
        raise ValueError("카페 ID는 양의 정수여야 합니다.")
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname != "cafe.naver.com" or
            parts.username or parts.password or parts.port not in (None, 443) or
            not parts.path.strip("/") or parts.query or parts.fragment):
        raise ValueError("카페 주소는 https://cafe.naver.com/ 으로 시작하는 카페 주소여야 합니다.")
    path = parts.path.strip("/").split("/")
    if len(path) >= 3 and path[:2] == ["ca-fe", "cafes"] and path[2] != id_text:
        raise ValueError("카페 주소의 숫자 ID가 입력한 ID와 다릅니다.")
    return int(id_text), url


def cafe_for_user(username: str | None = None) -> tuple[int, str]:
    from modules.user_manager import load_config
    saved = load_config(username) or {}
    if "cafe" in saved:
        cafe = saved["cafe"]
        return validate_cafe(str(cafe.get("id", "")), cafe.get("url", ""))
    return DEFAULT_CAFE_ID, DEFAULT_CAFE_URL


def apply_cafe_for_user(username: str | None = None) -> None:
    global CAFE_ID, CAFE_URL, CAFE_WRITE_URL
    CAFE_ID, CAFE_URL = cafe_for_user(username)
    CAFE_WRITE_URL = (f"https://cafe.naver.com/ca-fe/cafes/{CAFE_ID}/articles/write?boardType=L"
                      if CAFE_ID > 0 and CAFE_URL else "")


# ──────────────────────────────────────────────
# 타이밍 설정
# ──────────────────────────────────────────────
TIMEOUT = 30000
WAIT_AFTER_PUBLISH = 2000

# ──────────────────────────────────────────────
# 사용자 설정
# ──────────────────────────────────────────────
_user_config = None


def get_user_config(username: str = None) -> dict:
    """사용자 설정 가져오기 (캐시)"""
    global _user_config
    if _user_config is None:
        _user_config = get_or_create_config(username)
    return _user_config
