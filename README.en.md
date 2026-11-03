<div align="center">
  <h1>🌱 Happybin Auto · 콩콩줍줍</h1>
  <p><strong>A Windows desktop tool for running and monitoring NAVER Happybean workflows in a visible browser</strong></p>
  <p>Blog · Cafe · Bean banners · Happybean</p>
  <p><a href="README.md">한국어</a> · <a href="README.en.md">English</a></p>
  <p>
    <img src="https://img.shields.io/badge/OS-Windows-0078D4?logo=windows&logoColor=white" alt="Windows">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Browser-Playwright-2EAD33?logo=playwright&logoColor=white" alt="Playwright">
    <img src="https://img.shields.io/badge/Mode-Desktop%20%2B%20CLI-2D8C61" alt="Desktop and CLI">
  </p>
</div>

> **Project status** · Source code and a Windows x64 distribution are available. Download the latest ZIP and SHA-256 checksum from [Releases](../../releases).

> **Notice** · This is an unofficial project and is not affiliated with, endorsed by, or sponsored by NAVER or Happybean. Use it only with accounts and destinations you are authorized to access, and follow NAVER's Terms of Service and applicable policies. Successful collection, continued service access, and account standing are not guaranteed. The software is provided as is, without warranties to the extent permitted by applicable law.

## At a glance

Happybin Auto uses a visible Chromium browser to check the login state and run configured tasks in sequence. The desktop interface shows progress and logs and can request a stop. The CLI runs the same automation flow and can report local profile and session-backup information.

| Area | Current capabilities |
| --- | --- |
| Desktop UI | Start and stop, per-stage progress, logs, results observed during the run |
| Sign-in | Prompts for QR sign-in first, with manual sign-in in the browser when needed |
| Blog | Creates a post from the configured template and attempts to select private visibility |
| Cafe | Creates a post and checks bean banners at the cafe configured through environment variables |
| Bean banners | Scans post pages and known blog and cafe pages |
| Happybean | Checks the home page for popups, bean collection banners, and Today's Pick |
| Profiles | Manages per-user Chromium profiles and local settings |
| CLI status | Uses <code>--status</code> to show whether a local session backup exists and its age |

### Workflow

~~~mermaid
flowchart LR
    A[Check sign-in] --> B[Publish blog post]
    B --> C[Publish cafe post<br/>when configured]
    C --> D[Scan blog and cafe<br/>bean banners]
    D --> E[Collect on the<br/>Happybean home page]
~~~

The cafe stage navigates to a destination only when both <code>HAPPYBIN_CAFE_ID</code> and <code>HAPPYBIN_CAFE_URL</code> are set. Blog and cafe workflows can publish real posts. Review the account, destination, and post template before running the automation.

## Technology

- **Python 3.10 or later** for the automation flow and interface.
- **Playwright sync API + Chromium** launches a visible, Playwright-managed Chromium persistent context. The application does not use system Chrome.
- **Tkinter** provides the Windows desktop interface with stages, progress, logs, start, and stop controls.
- **Shared orchestration** lets the UI and <code>--cli</code> use the same step-by-step runner in <code>automation.py</code>.
- **Windows display APIs** are used to read screen dimensions and position the browser. A Windows desktop session is required for the full workflow.
- **Minimal external dependencies** — <code>requirements.txt</code> declares Playwright as the only external Python package.

Post titles and bodies are defined in <code>content/templates.py</code>. The current defaults use fixed titles and randomized numeric bodies, so review the content before starting the automation.

## Install and start

Run these commands in Windows PowerShell:

~~~powershell
git clone https://github.com/sontheo/happybin_auto_public.git
cd happybin_auto_public

python -m venv .venv
$env:PLAYWRIGHT_BROWSERS_PATH = "0"

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium

# Inspect the options, then launch the desktop UI
.\.venv\Scripts\python.exe main.py --help
.\.venv\Scripts\python.exe main.py
~~~

<code>PLAYWRIGHT_BROWSERS_PATH=0</code> installs Chromium where the application looks for it by default. Install and run from the same PowerShell session. When the browser opens, follow its prompts to sign in. Avoid interacting with its tabs while automation is running.

## Usage

~~~powershell
# Desktop UI
.\.venv\Scripts\python.exe main.py

# Run the same workflow from the CLI
.\.venv\Scripts\python.exe main.py --cli

# Run with a separate local profile
.\.venv\Scripts\python.exe main.py --cli --user my-profile

# Show local session-backup information
.\.venv\Scripts\python.exe main.py --status

# List registered local profiles
.\.venv\Scripts\python.exe main.py --list-users

# Clear login data for the selected profile
.\.venv\Scripts\python.exe main.py --reset-login --user my-profile
~~~

| Option | Description |
| --- | --- |
| <code>--cli</code> | Run automation in the terminal instead of opening the desktop UI |
| <code>--user NAME</code> | Select a local data profile; this is not a NAVER login ID |
| <code>--status</code> | Show whether the <code>session.json</code> backup exists and how old it is |
| <code>--list-users</code> | List profiles with a locally registered settings file |
| <code>--reset-login</code> | Delete the selected profile's session backup and Chromium profile |
| <code>--help</code> | Show command-line options |

<code>--status</code> summarizes the saved session backup. It does not connect to NAVER to verify the current account or login state. The browser checks login when automation starts. <code>--reset-login</code> deletes the selected profile's local browser login data.

## Cafe configuration

Cafe automation is disabled until both the ID and URL are set in the **same PowerShell session**:

~~~powershell
$env:HAPPYBIN_CAFE_ID = "12345678"
$env:HAPPYBIN_CAFE_URL = "https://cafe.naver.com/your-cafe"

.\.venv\Scripts\python.exe main.py
~~~

Set <code>HAPPYBIN_CAFE_ID</code> to a positive numeric ID and <code>HAPPYBIN_CAFE_URL</code> to the matching cafe URL. If either value is missing, cafe posting and cafe home-page banner scanning are skipped. The application does not load <code>.env</code> files automatically. Do not put a real personal or organization destination in source code or public examples.

## Local data and privacy

Profile data is stored outside the source directory:

~~~text
%LOCALAPPDATA%/HappyBeanAuto/<profile>/
├── browser/          # Chromium profile, including login state
├── session.json      # Playwright session backup; may contain cookies
└── user_config.json  # Local profile settings
~~~

If <code>LOCALAPPDATA</code> is unavailable, the fallback is <code>~/AppData/Local/HappyBeanAuto/</code>. If the new data root does not exist and a legacy <code>user_data/</code> folder is present beside the application, the first run attempts to migrate it.

The application does **not** encrypt <code>session.json</code>. Treat browser profiles and cookies as account-access data, and protect them with operating-system permissions, especially on shared computers. Do not commit or upload session files, browser profiles, <code>.env</code> files, authenticated page captures, or logs containing sensitive information.

## Repository structure

| Path | Role |
| --- | --- |
| <code>main.py</code> | Entry point, UI/CLI selection, profile and session-status options |
| <code>automation.py</code> | Shared workflow, progress callbacks, and cancellation handling |
| <code>ui.py</code> | Tkinter desktop UI, logs, and progress display |
| <code>config.py</code> | Cafe environment variables and shared timing settings |
| <code>content/templates.py</code> | Blog and cafe post titles and body templates |
| <code>modules/login.py</code> | Persistent Chromium context and QR/browser sign-in |
| <code>modules/session_manager.py</code> | Session backup, cookie checks, login state, and CAPTCHA detection |
| <code>modules/user_manager.py</code> | Local profile, settings, and browser-data management |
| <code>modules/paths.py</code> | Application and user-data paths, including legacy migration |
| <code>modules/blog.py</code> · <code>modules/cafe.py</code> | Blog/cafe publishing and post-publication banner checks |
| <code>modules/bean_banner.py</code> | Bean banner discovery, expansion, clicking, and per-page results |
| <code>modules/happybean.py</code> | Happybean home-page popups and bean collection content |
| <code>modules/kin.py</code> | Bean banner helper for Knowledge iN pages |
| <code>modules/utils.py</code> | Navigation and Windows screen/window helpers |
| <code>test_*.py</code>, <code>verify_*.py</code>, <code>check_banners.py</code> | Manual integration scripts that use a signed-in browser |
| <code>requirements.txt</code> | External Python dependency |

## Before you run

- **Real posts may be created.** The default workflow attempts to publish a blog post. If cafe automation is configured, it can also publish to that cafe.
- **Private blog visibility is not guaranteed.** The workflow attempts to select the private option, but it does not verify that the setting was successfully applied. Do not use sensitive content in the template.
- **Banner detection and bean credits are not guaranteed.** Page structure, campaign availability, login state, and network conditions can change. Reported results are automation observations; verify actual credits in Happybean.
- **Manual integration scripts use a real signed-in browser.** Files named <code>test</code> or <code>verify</code> are not isolated unit tests. Some can publish blog/cafe posts or click banners. Inspect a script before running it.
- **Service UI changes can interrupt automation.** Selectors and navigation depend on NAVER pages.

## License

No project license is designated in this repository. This README does not grant additional rights to the project code or third-party software. Dependencies and third-party assets remain subject to their own licenses and terms.
