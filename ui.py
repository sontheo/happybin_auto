"""콩콩줍줍 Windows UI."""
from __future__ import annotations

import getpass
from pathlib import Path
import ctypes
import queue
import shutil
import sys
import threading
import tkinter as tk
from contextlib import redirect_stderr, redirect_stdout
from tkinter import font as tkfont, messagebox, ttk

from automation import run_automation
from modules.session_manager import clear_session
from modules.user_manager import clear_browser_data, get_or_create_config, save_config
import config
from modules import updater


# A restrained, high-contrast palette shared by the main window and settings.
BG = "#eff1f5"
SURFACE = "#ffffff"
TEXT = "#1d2533"
MUTED = "#354254"
GREEN = "#2469ca"
GREEN_DARK = "#174e9b"
GREEN_SOFT = "#e5efff"
AMBER_SOFT = "#f7efdb"
AMBER_TEXT = "#634c1d"
BORDER = "#dde2ea"
RED = "#a33036"
BODY_FONT = "맑은 고딕"


def enable_dpi_awareness() -> None:
    """Opt in before creating any Tk window so Windows does not bitmap-scale it."""
    if sys.platform != "win32":
        return
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def load_packaged_fonts() -> bool:
    """Register Pretendard for this process before creating Tk on Windows."""
    if sys.platform != "win32":
        return False
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    paths = [root / "assets" / "fonts" / name for name in
             ("Pretendard-Regular.otf", "Pretendard-Bold.otf")]
    try:
        add_font = ctypes.windll.gdi32.AddFontResourceExW
        return all(add_font(str(path), 0x10, None) > 0 for path in paths)
    except (AttributeError, OSError):
        return False


class RoundedPanel(tk.Canvas):
    """A solid rounded surface which follows its content and the window width."""
    def __init__(self, parent, *, padx=0, pady=0, stretch=False):
        super().__init__(parent, bg=BG, highlightthickness=0, bd=0)
        self.stretch = stretch
        self.body = tk.Frame(self, bg=SURFACE, padx=padx, pady=pady)
        self.shape = self.create_polygon(0, 0, 0, 0, smooth=True, splinesteps=24, fill=SURFACE, outline=SURFACE)
        self.content = self.create_window(8, 8, anchor="nw", window=self.body)
        self.body.bind("<Configure>", self._resize)
        self.bind("<Configure>", self._resize)

    def _resize(self, event=None):
        width = max(self.winfo_width(), 32)
        requested = self.body.winfo_reqheight() + 16
        height = max(requested, self.winfo_height()) if self.stretch else requested
        self.itemconfigure(self.content, width=max(width - 16, 1), height=max(height - 16, 1) if self.stretch else 0)
        if self.winfo_reqheight() != requested:
            self.configure(height=requested)
        r = 16
        self.coords(self.shape, 0, r, 0, 0, r, 0, width-r, 0, width, 0, width, r,
                    width, height-r, width, height, width-r, height, r, height,
                    0, height, 0, height-r)


class RoundedButton(tk.Canvas):
    """Keyboard-accessible pill button with a real disabled state."""
    def __init__(self, parent, *, text="", textvariable=None, command=None,
                 fill=GREEN_SOFT, foreground=GREEN_DARK, hover=GREEN_SOFT,
                 state="normal", min_width=76, height=36):
        self._text = text
        self._variable = textvariable
        self._command = command
        self._fill = fill
        self._foreground = foreground
        self._hover_color = hover
        self._hovered = False
        self._pressed = False
        self._font = tkfont.Font(parent, family=BODY_FONT, size=10, weight="bold")
        scale = max(1.0, parent.winfo_fpixels("1i") / 96.0)
        self._minimum = int(min_width * scale)
        self._height = max(int(height * scale), self._font.metrics("linespace") + 8)
        super().__init__(parent, bg=parent.cget("bg"), highlightthickness=2,
                         highlightbackground=parent.cget("bg"), highlightcolor=GREEN,
                         bd=0, height=self._height, width=self._minimum,
                         state=state, takefocus=True, cursor="hand2")
        self._shape = self.create_polygon(0, 0, 0, 0, smooth=True, splinesteps=24, outline="")
        self._label_id = self.create_text(0, 0, text="", font=self._font)
        if self._variable is not None:
            self._trace = self._variable.trace_add("write", lambda *_: self._redraw())
            self.bind("<Destroy>", self._untrace, add="+")
        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<space>", self._key_invoke)
        self.bind("<Return>", self._key_invoke)
        self._redraw()

    def _untrace(self, event):
        if event.widget is self and self._variable is not None:
            try:
                self._variable.trace_remove("write", self._trace)
            except tk.TclError:
                pass

    def _set_hover(self, hovered):
        self._hovered = hovered
        self._redraw()

    def _press(self, event):
        if self.cget("state") != "disabled":
            self.focus_set()
            self._pressed = True
            self._redraw()

    def _release(self, event):
        pressed = self._pressed
        self._pressed = False
        self._redraw()
        if pressed and 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height():
            self.invoke()

    def _key_invoke(self, event):
        self.invoke()
        return "break"

    def invoke(self):
        if self.cget("state") != "disabled" and self._command:
            return self._command()

    def configure(self, cnf=None, **kwargs):
        if "text" in kwargs:
            self._text = kwargs.pop("text")
        result = super().configure(cnf, **kwargs)
        if hasattr(self, "_label_id"):
            self._redraw()
        return result

    config = configure

    def _redraw(self, event=None):
        if not self.winfo_exists():
            return
        text = self._variable.get() if self._variable is not None else self._text
        wanted = max(self._minimum, self._font.measure(text) + 28)
        if int(super().cget("width")) != wanted:
            super().configure(width=wanted)
        w, h = max(self.winfo_width(), 1), max(self.winfo_height(), 1)
        r = h / 2
        self.coords(self._shape, 0, r, 0, 0, r, 0, w-r, 0, w, 0, w, r,
                    w, h-r, w, h, w-r, h, r, h, 0, h, 0, h-r)
        disabled = self.cget("state") == "disabled"
        fill = "#e9ecf1" if disabled else (self._hover_color if self._hovered or self._pressed else self._fill)
        self.itemconfigure(self._shape, fill=fill)
        self.coords(self._label_id, w / 2, h / 2)
        self.itemconfigure(self._label_id, text=text, fill="#8b95a3" if disabled else self._foreground)


class _QueueStream:
    # All output is kept in the activity feed; milestones also update the status.
    MILESTONES = (
        ("QR코드 로그인을 실행해주세요", "네이버 앱에서 QR 로그인을 진행해 주세요."),
        ("브라우저에서 직접 로그인해주세요", "브라우저에서 직접 로그인해 주세요."),
        ("이미 로그인되어 있습니다", "로그인 상태를 확인했습니다."),
        ("로그인 성공!", "로그인이 완료되었습니다."),
        ("[블로그] 발행 완료!", "블로그 글이 발행되었습니다."),
        ("[카페] 등록 완료!", "카페 글이 등록되었습니다."),
        ("카페 작업을 건너뜁니다", "카페 설정이 없어 카페 작업을 건너뜁니다."),
        ("콩 획득 확인!", "콩 획득을 확인했습니다."),
    )

    def __init__(self, events: queue.Queue, original=None) -> None:
        self.events = events
        self.original = original

    def write(self, text: str) -> int:
        if self.original is not None:
            try:
                self.original.write(text)
            except (OSError, ValueError):
                pass
        if text:
            self.events.put(("log", text))
        for marker, summary in self.MILESTONES:
            if marker in text:
                self.events.put(("activity", summary))
                break
        return len(text)

    def flush(self) -> None:
        if self.original is not None:
            try:
                self.original.flush()
            except (OSError, ValueError):
                pass


class HappyBeanApp(tk.Tk):
    STEP_ORDER = ("로그인", "블로그", "카페", "배너", "해피빈")
    STEP_TITLES = {
        "로그인": "로그인 상태 확인",
        "블로그": "블로그 글쓰기 및 콩배너",
        "카페": "카페 글쓰기 및 콩배너",
        "배너": "메인 페이지 배너 스캔",
        "해피빈": "해피빈 콩 수집",
    }
    PROGRESS = {"login": ("로그인", 8), "blog": ("블로그", 25), "cafe": ("카페", 45),
                "banners": ("배너", 68), "happybean": ("해피빈", 84), "complete": ("", 100)}

    def __init__(self) -> None:
        packaged_font = load_packaged_fonts()
        super().__init__()
        global BODY_FONT
        families = set(tkfont.families(self))
        BODY_FONT = "Pretendard" if packaged_font else next((family for family in ("Pretendard", "맑은 고딕", "Malgun Gothic", "Noto Sans CJK KR") if family in families), "TkDefaultFont")
        self.title("콩콩줍줍")
        # Tk uses point-sized fonts; size the window for the active display DPI.
        scale = max(1.0, self.winfo_fpixels("1i") / 96.0)
        width = min(int(700 * scale), self.winfo_screenwidth() - 32)
        height = min(int(680 * scale), self.winfo_screenheight() - 48)
        self.geometry(f"{width}x{height}+24+24")
        self.minsize(width, height)
        self.resizable(True, False)
        self.configure(bg=BG)
        self.events: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.closed_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.update_release = None
        self.update_stage = None
        self.update_state = "idle"
        self.update_status = tk.StringVar(value="업데이트 확인")
        self.username = getpass.getuser()
        self.status = tk.StringVar(value="준비됨 — 실행하면 로그인 상태를 확인합니다.")
        self.bean_detail = tk.StringVar(value="아직 확인된 콩 획득 내역이 없습니다")
        self.bean_total = tk.StringVar(value="+0콩")
        self.current_status = tk.StringVar(value="수집 대기 중")
        self.last_progress_state = "idle"
        self.step_states: dict[str, tk.StringVar] = {}
        self.step_icons: dict[str, tk.Label] = {}
        self.step_rows: list[tk.Frame] = []
        self._configure_style()
        self._build()
        self.after(100, self._drain_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        if sys.platform == "win32" and getattr(sys, "frozen", False):
            self._begin_update_check()
        else:
            self.update_status.set("Windows 배포본에서 업데이트 확인")

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("HB.Horizontal.TProgressbar", troughcolor="#e4e8ef", background=GREEN,
                        bordercolor="#e4e8ef", lightcolor=GREEN, darkcolor=GREEN, thickness=6)

    @staticmethod
    def _label(parent, text: str | tk.StringVar, **kwargs) -> tk.Label:
        defaults = {"bg": parent.cget("bg"), "fg": TEXT, "font": (BODY_FONT, 10)}
        defaults.update(kwargs)
        if isinstance(text, tk.Variable):
            return tk.Label(parent, textvariable=text, **defaults)
        return tk.Label(parent, text=text, **defaults)

    def _build(self) -> None:
        outer = tk.Frame(self, bg=BG, padx=18, pady=10)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 8))
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        self._label(brand, "콩콩줍줍", font=(BODY_FONT, 17, "bold")).pack(anchor="w")
        self._label(brand, "나의 해피빈 수집", fg=MUTED, font=(BODY_FONT, 10)).pack(anchor="w", pady=(1, 0))
        self.update_button = RoundedButton(header, textvariable=self.update_status, command=self._update_action,
                                           fill="#e4ebf7", hover="#d7e5fa", min_width=120)
        self.update_button.pack(side="right")

        # A single primary surface keeps the current task, result and action together.
        hero_panel = RoundedPanel(outer, padx=8, pady=0)
        hero_panel.pack(fill="x")
        hero = hero_panel.body
        top = tk.Frame(hero, bg=SURFACE)
        top.pack(fill="x")
        self._label(top, "오늘의 수집", bg=SURFACE, fg=MUTED, font=(BODY_FONT, 10, "bold")).pack(side="left")
        live = tk.Frame(top, bg=SURFACE)
        live.pack(side="right")
        self.live_dot = self._label(live, "●", bg=SURFACE, fg=MUTED, font=(BODY_FONT, 10))
        self.live_dot.pack(side="left")
        self.live_text = self._label(live, "준비", bg=SURFACE, fg=MUTED, font=(BODY_FONT, 10, "bold"))
        self.live_text.pack(side="left", padx=(5, 0))
        self._label(hero, self.bean_total, bg=SURFACE, fg=TEXT, font=(BODY_FONT, 18, "bold")).pack(anchor="w")
        self._label(hero, self.bean_detail, bg=SURFACE, fg=MUTED, font=(BODY_FONT, 10)).pack(anchor="w")
        tk.Frame(hero, bg=BG, height=1).pack(fill="x", pady=(3, 3))
        self.stage = tk.Frame(hero, bg=SURFACE)
        self.stage.pack(fill="x")
        self.stage_title = self._label(self.stage, "실행할 준비가 되었습니다", bg=SURFACE, font=(BODY_FONT, 12, "bold"))
        self.stage_title.pack(anchor="w")
        self.progress = ttk.Progressbar(self.stage, style="HB.Horizontal.TProgressbar", mode="determinate", maximum=100, value=0)
        self.progress.pack(fill="x", pady=(3, 0))
        actions = tk.Frame(hero, bg=SURFACE)
        actions.pack(fill="x", pady=(4, 0))
        self.run_button = RoundedButton(actions, text="자동 수집 시작", command=self._start,
                                        fill=GREEN, foreground=SURFACE, hover=GREEN_DARK, min_width=190)
        self.run_button.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.cancel_button = RoundedButton(actions, text="중지", command=self._cancel, state="disabled",
                                           fill=BG, foreground=RED, hover="#f8e8e9")
        self.cancel_button.pack(side="right")

        sections = tk.Frame(outer, bg=BG)
        sections.pack(fill="both", expand=True, pady=(7, 0))
        sections.columnconfigure(0, weight=6, uniform="sections")
        sections.columnconfigure(1, weight=5, uniform="sections")
        sections.rowconfigure(0, weight=1)
        left = tk.Frame(sections, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right = tk.Frame(sections, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        title_row = tk.Frame(left, bg=BG)
        title_row.pack(fill="x", pady=(0, 3))
        self._label(title_row, "수집 과정", font=(BODY_FONT, 12, "bold")).pack(side="left")
        self.cafe_button = RoundedButton(title_row, text="카페 설정  ›", command=self._edit_cafe,
                                         fill="#e4ebf7", hover="#d7e5fa", min_width=95)
        self.cafe_button.pack(side="right")
        steps_panel = RoundedPanel(left, padx=5, pady=0, stretch=True)
        self.steps_panel = steps_panel
        steps_panel.pack(fill="both", expand=True)
        steps = steps_panel.body
        for index, key in enumerate(self.STEP_ORDER):
            if index:
                tk.Frame(steps, bg=BG, height=1).pack(fill="x")
            row = tk.Frame(steps, bg=SURFACE, pady=1)
            row.pack(fill="both", expand=True)
            self.step_rows.append(row)
            icon = self._label(row, "○", bg=SURFACE, fg=MUTED, font=(BODY_FONT, 10))
            icon.pack(side="left", padx=(0, 12))
            self.step_icons[key] = icon
            self._label(row, self.STEP_TITLES[key], bg=SURFACE, font=(BODY_FONT, 10, "bold")).pack(side="left")
            state = tk.StringVar(value="대기")
            self.step_states[key] = state
            self._label(row, state, bg=SURFACE, fg=MUTED, font=(BODY_FONT, 10, "bold")).pack(side="right")

        right_heading = tk.Frame(right, bg=BG, height=self.cafe_button._height + 7)
        right_heading.pack(fill="x")
        right_heading.pack_propagate(False)
        self._label(right_heading, "현재 상황", font=(BODY_FONT, 12, "bold")).pack(side="left")
        current_panel = RoundedPanel(right, padx=2, pady=0)
        current_panel.pack(fill="x")
        self._label(current_panel.body, self.current_status, bg=SURFACE, fg=TEXT,
                    font=(BODY_FONT, 11, "bold"), anchor="w", justify="left", height=1).pack(fill="x")
        self._label(right, "활동 기록", font=(BODY_FONT, 10, "bold"), fg=MUTED).pack(anchor="w", pady=(4, 3))
        log_panel = RoundedPanel(right, padx=2, pady=0, stretch=True)
        self.log_panel = log_panel
        log_panel.pack(fill="both", expand=True)
        log_box = log_panel.body
        self.log = tk.Text(log_box, height=1, state="disabled", wrap="word", bg=SURFACE, fg=TEXT,
                           insertbackground=TEXT, relief="flat", highlightthickness=0, font=(BODY_FONT, 10), padx=4, pady=0)
        self.log.pack(fill="both", expand=True)
        footer = tk.Frame(outer, bg=BG)
        footer.pack(side="bottom", fill="x", pady=(3, 0), before=sections)
        self._label(footer, "수집 중에는 브라우저를 직접 조작하지 마세요.", fg=MUTED, font=(BODY_FONT, 10, "bold")).pack(side="left")
        self.reset_button = RoundedButton(footer, text="로그인 초기화", command=self._reset_login,
                                          fill=BG, foreground=MUTED, hover=BORDER, height=28)
        self.reset_button.pack(side="right")

    def _edit_cafe(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("카페 설정")
        dialog.configure(bg=SURFACE, padx=22, pady=20)
        dialog.transient(self)
        dialog.resizable(False, False)
        try:
            cafe_id, cafe_url = config.cafe_for_user(self.username)
        except (ValueError, TypeError, AttributeError):
            cafe_id, cafe_url = 0, ""
        id_var = tk.StringVar(value=str(cafe_id) if cafe_id else "")
        url_var = tk.StringVar(value=cafe_url)
        self._label(dialog, "카페 설정", bg=SURFACE, font=(BODY_FONT, 15, "bold")).pack(anchor="w")
        self._label(dialog, "글쓰기와 카페 배너 확인에 사용할 카페입니다.", bg=SURFACE, fg=MUTED,
                    font=(BODY_FONT, 10)).pack(anchor="w", pady=(5, 14))
        for label, variable in (("카페 숫자 ID", id_var), ("카페 주소", url_var)):
            self._label(dialog, label, bg=SURFACE, font=(BODY_FONT, 10, "bold")).pack(anchor="w", pady=(4, 3))
            tk.Entry(dialog, textvariable=variable, width=45, font=(BODY_FONT, 10), relief="solid", bd=1).pack(fill="x", ipady=5, pady=(0, 8))
        def fill_cafe() -> None:
            id_var.set("31172912")
            url_var.set("https://cafe.naver.com/dpbokji1")
        self.preset_button = RoundedButton(dialog, text="dpbokji1 카페 자동완성", command=fill_cafe,
                                           fill=GREEN_SOFT, hover="#d7e5fa", min_width=180)
        self.preset_button.pack(anchor="w", pady=(0, 8))
        self._label(dialog, "같은 카페의 ID와 주소를 입력하세요. 둘 다 비우면 건너뜁니다.", bg=SURFACE, fg=MUTED,
                    font=(BODY_FONT, 10)).pack(anchor="w", pady=(0, 12))
        def save() -> None:
            try:
                cafe_id, cafe_url = config.validate_cafe(id_var.get(), url_var.get())
                user = get_or_create_config(self.username)
                user["cafe"] = {"id": cafe_id, "url": cafe_url}
                save_config(user, self.username)
            except (ValueError, OSError) as exc:
                messagebox.showerror("카페 설정", str(exc), parent=dialog)
                return
            self._append_log("카페 설정을 저장했습니다." if cafe_id else "카페 작업을 사용하지 않습니다.")
            dialog.destroy()
        buttons = tk.Frame(dialog, bg=SURFACE)
        buttons.pack(fill="x")
        RoundedButton(buttons, text="저장", command=save, fill=GREEN, foreground=SURFACE,
                      hover=GREEN_DARK).pack(side="right")
        RoundedButton(buttons, text="취소", command=dialog.destroy, fill=BG, foreground=TEXT,
                      hover=BORDER).pack(side="right", padx=(0, 6))
        dialog.grab_set()
        dialog.wait_window()

    def _begin_update_check(self) -> None:
        if self.update_state in ("checking", "downloading"):
            return
        self.update_state = "checking"
        self.update_status.set("업데이트 확인 중…")
        def check() -> None:
            try:
                self.events.put(("update_checked", updater.check_update()))
            except updater.UpdateUnavailable:
                self.events.put(("update_unavailable",))
            except Exception:
                self.events.put(("update_check_error",))
        threading.Thread(target=check, daemon=True).start()

    def _update_action(self) -> None:
        if sys.platform != "win32" or not getattr(sys, "frozen", False):
            self.update_status.set("Windows 배포본에서 업데이트 확인")
        elif self.update_state == "available":
            self.update_state = "downloading"
            self.update_status.set("업데이트 다운로드 중…")
            release = self.update_release
            def download() -> None:
                try:
                    stage = updater.stage_update(release)
                    if self.closed_event.is_set():
                        shutil.rmtree(stage, ignore_errors=True)
                    else:
                        self.events.put(("update_ready", stage))
                except Exception:
                    self.events.put(("update_download_error",))
            threading.Thread(target=download, daemon=True).start()
        elif self.update_state == "ready":
            if self.worker and self.worker.is_alive():
                self.update_status.set("수집 종료 후 설치할 수 있어요")
                return
            if not messagebox.askyesno("업데이트 설치", "업데이트를 설치하고 앱을 다시 시작할까요?", parent=self):
                return
            try:
                updater.launch_installer(self.update_stage)
                self.update_stage = None
                self.destroy()
            except Exception:
                self.update_status.set("설치 실패 · 다시 시도")
        elif self.update_state not in ("checking", "downloading"):
            self._begin_update_check()

    def _start(self) -> None:
        self.cancel_event.clear()
        self.last_progress_state = "starting"
        self.current_status.set("수집을 시작합니다.")
        self.run_button.configure(state="disabled", text="자동 수집 진행 중")
        self.reset_button.configure(state="disabled")
        self.cafe_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.live_dot.configure(fg=GREEN)
        self.live_text.configure(text="실행 중", fg=GREEN_DARK)
        self.progress.configure(value=3)
        self.bean_detail.set("작업 결과를 확인하는 중입니다")
        self.bean_total.set("+0콩")
        self._set_step_state("로그인", "진행 중")
        for key in self.STEP_ORDER[1:]:
            self._set_step_state(key, "대기")
        self._append_log("\n실행 시작")
        self.worker = threading.Thread(target=self._run_worker, args=(self.username,), daemon=True)
        self.worker.start()

    def _run_worker(self, username: str) -> None:
        stdout = _QueueStream(self.events, sys.stdout)
        stderr = _QueueStream(self.events, sys.stderr)

        def progress(state: str, message: str) -> None:
            self.events.put(("progress", state, message))

        with redirect_stdout(stdout), redirect_stderr(stderr):
            results = run_automation(username, progress, self.cancel_event)
        self.events.put(("finished", results))

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.status.set("중지 요청됨 — 현재 작업을 정리한 뒤 안전하게 종료합니다.")
        self.current_status.set("현재 작업을 정리하고 있습니다.")
        self._append_log("중지를 요청했습니다.")
        self.stage_title.configure(text="중지 요청됨")
        self.cancel_button.configure(state="disabled", text="중지 요청됨")

    def _reset_login(self) -> None:
        if not messagebox.askyesno("로그인 초기화", "저장된 로그인 캐시를 삭제하고 다음 실행에서 다시 로그인할까요?"):
            return
        try:
            clear_session(self.username)
            clear_browser_data(self.username)
            self.status.set("로그인 캐시를 초기화했습니다.")
            self._append_log("로그인 캐시를 초기화했습니다.")
        except OSError as exc:
            messagebox.showerror("초기화 실패", str(exc))

    def _set_step_state(self, key: str, value: str) -> None:
        self.step_states[key].set(value)
        icon = self.step_icons[key]
        if value == "진행 중":
            icon.configure(text="●", fg="#d7890b")
        elif value == "대기":
            icon.configure(text="○", fg=MUTED)
        else:
            icon.configure(text="✓", fg=GREEN)

    def _show_progress(self, state: str, message: str) -> None:
        self.last_progress_state = state
        if state in self.PROGRESS and state != "complete":
            current, _ = self.PROGRESS[state]
            summary = self.STEP_TITLES[current] + " 중"
            self.status.set(message.replace("\n", " "))
            self.current_status.set(summary)
        elif state == "failed":
            self.status.set("실행 중 문제가 발생했습니다.")
            self.current_status.set("실행 실패 · 활동 기록 확인")
            self._append_log("실행 중 문제가 발생했습니다.")
        elif state == "cancelled":
            self.current_status.set("수집이 중지되었습니다.")
        if state not in self.PROGRESS:
            return
        current, amount = self.PROGRESS[state]
        self.progress.configure(value=amount)
        if current:
            self.stage_title.configure(text=self.STEP_TITLES[current])
            current_index = self.STEP_ORDER.index(current)
            for index, key in enumerate(self.STEP_ORDER):
                if index < current_index:
                    self._set_step_state(key, "완료")
                elif index == current_index:
                    self._set_step_state(key, "진행 중")
                    break

    def _drain_events(self) -> None:
        try:
            for _ in range(250):
                event = self.events.get_nowait()
                if event[0] == "log":
                    self._append_raw_log(event[1])
                elif event[0] == "activity":
                    current = event[1]
                    if "QR 로그인" in current:
                        current = "QR 로그인 필요"
                    elif "직접 로그인" in current:
                        current = "브라우저에서 로그인 필요"
                    elif "카페 설정이 없어" in current:
                        current = "카페 작업 건너뜀"
                    self.current_status.set(current)
                elif event[0] == "progress":
                    self._show_progress(event[1], event[2])
                elif event[0] == "update_checked":
                    self.update_release = event[1]
                    self.update_state = "available" if event[1] else "current"
                    self.update_status.set(f"업데이트 가능 · {event[1]['version']} ↓" if event[1] else "최신 버전입니다  ↻")
                elif event[0] == "update_unavailable":
                    self.update_state = "unavailable"
                    self.update_status.set("새 버전 준비 중  ↻")
                elif event[0] == "update_check_error":
                    self.update_state = "error"
                    self.update_status.set("확인 실패 · 다시 시도  ↻")
                elif event[0] == "update_ready":
                    self.update_stage = event[1]
                    self.update_state = "ready"
                    self.update_status.set("설치하고 다시 시작  ↗")
                elif event[0] == "update_download_error":
                    self.update_state = "available"
                    self.update_status.set("다운로드 실패 · 다시 시도  ↻")
                elif event[0] == "finished":
                    self._finish(event[1])
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _append_raw_log(self, text: str) -> None:
        at_bottom = self.log.yview()[1] >= 0.99
        self.log.configure(state="normal")
        self.log.insert("end", text)
        if at_bottom:
            self.log.see("end")
        self.log.configure(state="disabled")

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.strip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _finish(self, results: dict) -> None:
        self.run_button.configure(state="normal", text="자동 수집 다시 시작")
        self.reset_button.configure(state="normal")
        self.cafe_button.configure(state="normal")
        self.cancel_button.configure(state="disabled", text="중지")
        self.live_dot.configure(fg=MUTED)
        self.live_text.configure(text="완료", fg=MUTED)
        bean_items = [
            name for name, ok in results.items()
            if ok and (
                "콩" in name
                or name.startswith("배너_")
                or name in {"오늘의Pick", "팝업_콩받기"}
            )
        ]
        self.bean_total.set(f"+{len(bean_items)}콩")
        if bean_items:
            self.bean_detail.set(" · ".join(bean_items[:2]) + " 적립 확인")
        elif self.cancel_event.is_set():
            self.bean_detail.set("사용자 요청으로 작업을 중지했습니다")
        else:
            self.bean_detail.set("확인된 콩 획득 내역이 없습니다")
        if self.cancel_event.is_set():
            self.stage_title.configure(text="실행이 중지되었습니다")
            self.status.set("중지됨")
            self.current_status.set("수집이 중지되었습니다.")
            self._append_log("수집이 중지되었습니다.")
        elif self.last_progress_state == "failed":
            self.live_text.configure(text="오류", fg=RED)
            self.stage_title.configure(text="수집을 완료하지 못했습니다")
        else:
            success = sum(1 for value in results.values() if value)
            self.stage_title.configure(text="자동 수집이 완료되었습니다")
            self.status.set(f"완료 — {len(results)}개 중 {success}개 성공")
            self.current_status.set(f"수집 완료 · {success}/{len(results)} 성공")
            self._append_log(f"수집 완료: {len(results)}개 중 {success}개 성공")
            self.progress.configure(value=100)
            if results.get("블로그 콩배너"):
                self._set_step_state("블로그", "+1콩 획득")
            elif self.step_states["블로그"].get() != "대기":
                self._set_step_state("블로그", "완료")
            if results.get("카페 콩배너"):
                self._set_step_state("카페", "+1콩 획득")
            elif self.step_states["카페"].get() != "대기":
                self._set_step_state("카페", "완료")
            banner_count = sum(1 for name, ok in results.items() if ok and name.startswith("콩배너_"))
            if banner_count:
                self._set_step_state("배너", f"+{banner_count}콩 획득")
            happybean_count = sum(
                1 for name, ok in results.items()
                if ok and (name.startswith("배너_") or name in {"오늘의Pick", "팝업_콩받기"})
            )
            if happybean_count:
                self._set_step_state("해피빈", f"+{happybean_count}콩 획득")
            for key in self.STEP_ORDER:
                if self.step_states[key].get() == "진행 중":
                    self._set_step_state(key, "완료")

    def _on_close(self) -> None:
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno("실행 중", "실행을 중지하고 창을 닫을까요?"):
                return
            self.cancel_event.set()
        self.closed_event.set()
        if self.update_stage is not None:
            shutil.rmtree(self.update_stage, ignore_errors=True)
        self.destroy()


def launch_ui() -> None:
    enable_dpi_awareness()
    HappyBeanApp().mainloop()
