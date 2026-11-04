"""콩콩줍줍 Windows UI."""
from __future__ import annotations

import getpass
import ctypes
import queue
import sys
import threading
import tkinter as tk
from contextlib import redirect_stderr, redirect_stdout
from tkinter import messagebox, ttk

from automation import run_automation
from modules.session_manager import clear_session
from modules.user_manager import clear_browser_data, get_or_create_config, save_config
import config
from modules import updater


# A restrained, high-contrast palette shared by the main window and settings.
BG = "#f0f4f2"
SURFACE = "#fafcfb"
TEXT = "#172b24"
MUTED = "#465f53"
GREEN = "#126c4a"
GREEN_DARK = "#0b5137"
GREEN_SOFT = "#e1f0e8"
AMBER_SOFT = "#f7efdb"
AMBER_TEXT = "#634c1d"
BORDER = "#c9d8d0"
RED = "#a33036"


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


class _QueueStream:
    def __init__(self, events: queue.Queue) -> None:
        self.events = events

    def write(self, text: str) -> int:
        if text and not text.isspace():
            self.events.put(("log", text.rstrip()))
        return len(text)

    def flush(self) -> None:
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
        super().__init__()
        self.title("콩콩줍줍")
        # Tk uses point-sized fonts; size the window for the active display DPI.
        scale = max(1.0, self.winfo_fpixels("1i") / 96.0)
        width = min(int(620 * scale), self.winfo_screenwidth() - 32)
        height = min(int(750 * scale), self.winfo_screenheight() - 64)
        self.geometry(f"{width}x{height}+24+24")
        self.minsize(min(width, int(520 * scale)), min(height, int(580 * scale)))
        self.resizable(True, True)
        self.configure(bg=BG)
        self.events: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.username = getpass.getuser()
        self.status = tk.StringVar(value="준비됨 — 실행하면 로그인 상태를 확인합니다.")
        self.bean_detail = tk.StringVar(value="아직 확인된 콩 획득 내역이 없습니다")
        self.bean_total = tk.StringVar(value="+0콩")
        self.step_states: dict[str, tk.StringVar] = {}
        self.step_icons: dict[str, tk.Label] = {}
        self._configure_style()
        self._build()
        self.after(100, self._drain_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        if sys.platform == "win32" and getattr(sys, "frozen", False):
            threading.Thread(target=self._check_update, daemon=True).start()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("HB.Horizontal.TProgressbar", troughcolor="#cbe9d6", background=GREEN,
                        bordercolor="#cbe9d6", lightcolor=GREEN, darkcolor=GREEN, thickness=7)

    @staticmethod
    def _label(parent, text: str | tk.StringVar, **kwargs) -> tk.Label:
        defaults = {"bg": parent.cget("bg"), "fg": TEXT, "font": ("맑은 고딕", 10)}
        defaults.update(kwargs)
        if isinstance(text, tk.Variable):
            return tk.Label(parent, textvariable=text, **defaults)
        return tk.Label(parent, text=text, **defaults)

    def _build(self) -> None:
        viewport = tk.Frame(self, bg=BG)
        viewport.pack(fill="both", expand=True)
        canvas = tk.Canvas(viewport, bg=BG, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(viewport, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        outer = tk.Frame(canvas, bg=BG, padx=22, pady=18)
        window = canvas.create_window((0, 0), window=outer, anchor="nw")
        def resize_content(event=None):
            canvas.itemconfigure(window, width=canvas.winfo_width(),
                                 height=max(canvas.winfo_height(), outer.winfo_reqheight()))
            canvas.configure(scrollregion=canvas.bbox("all"))
        outer.bind("<Configure>", resize_content)
        canvas.bind("<Configure>", resize_content)
        def scroll_page(event):
            if event.widget.winfo_toplevel() != self or event.widget is self.log:
                return
            amount = -1 if getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0 else 1
            canvas.yview_scroll(amount, "units")
            return "break"
        self.bind_all("<MouseWheel>", scroll_page)
        self.bind_all("<Button-4>", scroll_page)
        self.bind_all("<Button-5>", scroll_page)

        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 16))
        icon_scale = max(1.0, self.winfo_fpixels("1i") / 96.0)
        mark = tk.Canvas(header, width=int(42 * icon_scale), height=int(42 * icon_scale), bg=BG, highlightthickness=0)
        mark.pack(side="left", padx=(0, 12))
        mark.create_oval(2, 2, 40, 40, fill=GREEN, outline=GREEN)
        mark.create_oval(12, 12, 21, 29, fill=SURFACE, outline=SURFACE)
        mark.create_oval(21, 12, 30, 29, fill=SURFACE, outline=SURFACE)
        mark.scale("all", 0, 0, icon_scale, icon_scale)
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        self._label(brand, "콩콩줍줍", font=("맑은 고딕", 18, "bold")).pack(anchor="w")
        self._label(brand, "해피빈 자동 수집", fg=MUTED, font=("맑은 고딕", 9)).pack(anchor="w")
        live = tk.Frame(header, bg=BG)
        live.pack(side="right")
        self.live_dot = self._label(live, "●", fg=MUTED, font=("맑은 고딕", 10))
        self.live_dot.pack(side="left")
        self.live_text = self._label(live, "준비", fg=MUTED, font=("맑은 고딕", 9, "bold"))
        self.live_text.pack(side="left", padx=(5, 0))

        self.stage = tk.Frame(outer, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=17, pady=14)
        self.stage.pack(fill="x")
        self._label(self.stage, "현재 작업", bg=SURFACE, fg=MUTED, font=("맑은 고딕", 9, "bold")).pack(anchor="w")
        self.stage_title = self._label(self.stage, "실행할 준비가 되었습니다", bg=SURFACE, font=("맑은 고딕", 14, "bold"))
        self.stage_title.pack(anchor="w", pady=(5, 2))
        self.stage_detail = self._label(self.stage, self.status, bg=SURFACE, fg=MUTED, font=("맑은 고딕", 9), anchor="w")
        self.stage_detail.pack(fill="x")
        self.progress = ttk.Progressbar(self.stage, style="HB.Horizontal.TProgressbar", mode="determinate", maximum=100, value=0)
        self.progress.pack(fill="x", pady=(12, 0))

        actions = tk.Frame(outer, bg=BG)
        actions.pack(fill="x", pady=(12, 16))
        self.run_button = tk.Button(actions, text="자동 수집 시작", command=self._start, bg=GREEN, fg=SURFACE,
                                    activebackground=GREEN_DARK, activeforeground=SURFACE, relief="flat",
                                    font=("맑은 고딕", 10, "bold"), pady=9, cursor="hand2")
        self.run_button.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.cancel_button = tk.Button(actions, text="중지", command=self._cancel, state="disabled", bg=SURFACE,
                                       fg=RED, activebackground=AMBER_SOFT, relief="flat", padx=20, pady=9,
                                       font=("맑은 고딕", 10, "bold"), cursor="hand2")
        self.cancel_button.pack(side="right")

        summary = tk.Frame(outer, bg=BG)
        summary.pack(fill="x", pady=(0, 12))
        bean = tk.Frame(summary, bg=BG)
        bean.pack(side="left", fill="x", expand=True)
        self._label(bean, "이번 실행에서 확인한 콩", fg=MUTED, font=("맑은 고딕", 9)).pack(anchor="w")
        row = tk.Frame(bean, bg=BG)
        row.pack(fill="x", pady=(2, 0))
        self._label(row, self.bean_total, fg=GREEN_DARK, font=("맑은 고딕", 16, "bold")).pack(side="left")
        self._label(row, self.bean_detail, fg=MUTED, font=("맑은 고딕", 9)).pack(side="left", padx=(10, 0))
        self.cafe_button = tk.Button(summary, text="카페 설정", command=self._edit_cafe, bg=BG, fg=GREEN_DARK,
                                     activebackground=GREEN_SOFT, relief="flat", padx=8, pady=8,
                                     font=("맑은 고딕", 9, "bold"), cursor="hand2")
        self.cafe_button.pack(side="right")

        self._label(outer, "진행 단계", fg=MUTED, font=("맑은 고딕", 9, "bold")).pack(anchor="w", pady=(0, 5))
        steps = tk.Frame(outer, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        steps.pack(fill="x")
        for index, key in enumerate(self.STEP_ORDER):
            if index:
                tk.Frame(steps, bg=BG, height=1).pack(fill="x")
            row = tk.Frame(steps, bg=SURFACE, padx=14, pady=3)
            row.pack(fill="x")
            icon = self._label(row, "○", bg=SURFACE, fg=MUTED, font=("맑은 고딕", 10))
            icon.pack(side="left", padx=(0, 10))
            self.step_icons[key] = icon
            self._label(row, self.STEP_TITLES[key], bg=SURFACE, font=("맑은 고딕", 9)).pack(side="left")
            state = tk.StringVar(value="대기")
            self.step_states[key] = state
            self._label(row, state, bg=SURFACE, fg=MUTED, font=("맑은 고딕", 9)).pack(side="right")

        self._label(outer, "진행 로그", fg=MUTED, font=("맑은 고딕", 9, "bold")).pack(anchor="w", pady=(12, 5))
        log_box = tk.Frame(outer, bg="#20372d", padx=2, pady=2)
        log_box.pack(fill="both", expand=True)
        self.log = tk.Text(log_box, height=3, state="disabled", wrap="word", bg="#20372d", fg="#e5f2eb",
                           insertbackground=SURFACE, relief="flat", font=("맑은 고딕", 9), padx=10, pady=8)
        scroll = ttk.Scrollbar(log_box, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill="x", pady=(8, 0))
        self._label(footer, "작업 중에는 브라우저를 직접 조작하지 마세요.", fg=MUTED, font=("맑은 고딕", 9)).pack(side="left")
        self.reset_button = tk.Button(footer, text="로그인 초기화", command=self._reset_login, bg=BG, fg=MUTED,
                                      activebackground=BG, relief="flat", font=("맑은 고딕", 9, "underline"), cursor="hand2")
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
        self._label(dialog, "카페 설정", bg=SURFACE, font=("맑은 고딕", 15, "bold")).pack(anchor="w")
        self._label(dialog, "글쓰기와 카페 배너 확인에 사용할 카페입니다.", bg=SURFACE, fg=MUTED,
                    font=("맑은 고딕", 9)).pack(anchor="w", pady=(5, 14))
        for label, variable in (("카페 숫자 ID", id_var), ("카페 주소", url_var)):
            self._label(dialog, label, bg=SURFACE, font=("맑은 고딕", 9, "bold")).pack(anchor="w", pady=(4, 3))
            tk.Entry(dialog, textvariable=variable, width=45, font=("맑은 고딕", 10), relief="solid", bd=1).pack(fill="x", ipady=5, pady=(0, 8))
        self._label(dialog, "같은 카페의 ID와 주소를 입력하세요. 둘 다 비우면 건너뜁니다.", bg=SURFACE, fg=MUTED,
                    font=("맑은 고딕", 9)).pack(anchor="w", pady=(0, 12))
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
        tk.Button(buttons, text="저장", command=save, bg=GREEN, fg=SURFACE, relief="flat", padx=18, pady=6,
                  font=("맑은 고딕", 9, "bold")).pack(side="right")
        tk.Button(buttons, text="취소", command=dialog.destroy, bg=SURFACE, fg=TEXT, relief="flat", padx=12, pady=6,
                  font=("맑은 고딕", 9)).pack(side="right", padx=(0, 6))
        dialog.grab_set()
        dialog.wait_window()

    def _check_update(self) -> None:
        try:
            release = updater.check_update()
            if release:
                self.events.put(("update", release))
        except Exception:
            pass  # An unavailable release service must not block startup.

    def _offer_update(self, release: dict) -> None:
        if self.worker and self.worker.is_alive():
            self.after(2000, lambda: self._offer_update(release))
            return
        if not messagebox.askyesno("업데이트", f"새 버전 {release['version']}이 있습니다. 지금 업데이트할까요?\n\n다운로드 후 프로그램을 다시 시작합니다.", parent=self):
            return
        self.run_button.configure(state="disabled")
        self.reset_button.configure(state="disabled")
        self.cafe_button.configure(state="disabled")
        self.status.set("업데이트를 다운로드하고 검증하는 중입니다.")
        def download() -> None:
            try:
                self.events.put(("update_ready", updater.stage_update(release)))
            except Exception as exc:
                self.events.put(("update_error", str(exc)))
        threading.Thread(target=download, daemon=True).start()

    def _start(self) -> None:
        self.cancel_event.clear()
        self.run_button.configure(state="disabled", text="자동 수집 진행 중")
        self.reset_button.configure(state="disabled")
        self.cafe_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.live_dot.configure(fg="#16b364")
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
        stream = _QueueStream(self.events)

        def progress(state: str, message: str) -> None:
            self.events.put(("progress", state, message))

        with redirect_stdout(stream), redirect_stderr(stream):
            results = run_automation(username, progress, self.cancel_event)
        self.events.put(("finished", results))

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.status.set("중지 요청됨 — 현재 작업을 정리한 뒤 안전하게 종료합니다.")
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
        self.status.set(message.replace("\n", " "))
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
            while True:
                event = self.events.get_nowait()
                if event[0] == "log":
                    self._append_log(event[1])
                elif event[0] == "progress":
                    self._show_progress(event[1], event[2])
                elif event[0] == "update":
                    self._offer_update(event[1])
                elif event[0] == "update_ready":
                    try:
                        updater.launch_installer(event[1])
                        self.destroy()
                        return
                    except Exception as exc:
                        self.events.put(("update_error", str(exc)))
                elif event[0] == "update_error":
                    self.run_button.configure(state="normal")
                    self.reset_button.configure(state="normal")
                    self.cafe_button.configure(state="normal")
                    self.status.set("업데이트에 실패했습니다. 기존 버전을 계속 사용할 수 있습니다.")
                    messagebox.showerror("업데이트 실패", event[1], parent=self)
                elif event[0] == "finished":
                    self._finish(event[1])
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + ("" if text.endswith("\n") else "\n"))
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
        else:
            success = sum(1 for value in results.values() if value)
            self.stage_title.configure(text="자동 수집이 완료되었습니다")
            self.status.set(f"완료 — {len(results)}개 중 {success}개 성공")
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
        self.destroy()


def launch_ui() -> None:
    enable_dpi_awareness()
    HappyBeanApp().mainloop()
