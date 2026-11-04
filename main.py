"""해피빈 자동화 진입점. 기본 실행은 Windows UI다."""
import argparse
import getpass
import sys

# Windows의 비한국어 콘솔에서도 한글 메시지 출력이 실패하지 않도록 한다.
for stream in (sys.stdout, sys.stderr):
    if stream is not None and hasattr(stream, "reconfigure"):
        stream.reconfigure(errors="replace")

from automation import run_automation
from modules.session_manager import clear_session, get_session_info
from modules.user_manager import clear_browser_data, get_user_dir, list_users


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="해피빈 콩 자동 수집기")
    parser.add_argument("--user", type=str, help="Windows 사용자 이름")
    parser.add_argument("--cli", action="store_true", help="UI 대신 콘솔에서 실행")
    parser.add_argument("--reset-login", action="store_true", help="로그인 캐시 초기화")
    parser.add_argument("--list-users", action="store_true", help="등록 사용자 목록")
    parser.add_argument("--status", action="store_true", help="캐시 상태 표시")
    parser.add_argument("--check-browser", action="store_true", help="설치된 Chromium 실행 확인")
    return parser.parse_args()


def show_status(username: str) -> None:
    print(f"사용자: {username}")
    print(f"데이터 디렉토리: {get_user_dir(username)}")
    info = get_session_info(username)
    if not info.get("exists"):
        print("세션 백업: 없음 (실행 시 브라우저 프로필도 함께 확인합니다)")
        return
    print(f"세션 백업: 존재함 / {info.get('age_days', 0):.1f}일 경과")
    print("상태: " + ("재로그인 필요 가능" if info.get("expired") else "쿠키 저장됨"))


def hide_owned_console() -> None:
    """Hide the EXE's own GUI console; keep an existing terminal visible."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    try:
        import ctypes
        processes = (ctypes.c_ulong * 2)()
        count = ctypes.windll.kernel32.GetConsoleProcessList(processes, len(processes))
        get_window = ctypes.windll.kernel32.GetConsoleWindow
        get_window.restype = ctypes.c_void_p
        hwnd = get_window()
        if count == 1 and hwnd:
            ctypes.windll.user32.ShowWindow(ctypes.c_void_p(hwnd), 0)
    except (AttributeError, OSError):
        pass


def main() -> None:
    args = parse_args()
    username = args.user or getpass.getuser()
    if args.check_browser:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<title>Happybin Auto browser check</title>")
            assert page.title() == "Happybin Auto browser check"
            browser.close()
        print("Chromium 실행 확인 완료")
        return
    if args.list_users:
        users = list_users()
        print("등록된 사용자:")
        print("\n".join(f"- {user}" for user in users) if users else "없음")
        return
    if args.reset_login:
        clear_session(username)
        clear_browser_data(username)
        print("로그인 캐시를 초기화했습니다.")
        return
    if args.status:
        show_status(username)
        return
    if args.cli:
        run_automation(username)
        return

    hide_owned_console()
    from ui import launch_ui
    launch_ui()


if __name__ == "__main__":
    main()
