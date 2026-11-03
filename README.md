<div align="center">
  <h1>🌱 콩콩줍줍</h1>
  <p><strong>네이버 해피빈 작업을 한눈에 살펴보고, 브라우저에서 차례로 실행하는 Windows 자동화 도구</strong></p>
  <p>블로그 · 카페 · 콩배너 · 해피빈</p>
  <p><a href="README.md">한국어</a> · <a href="README.en.md">English</a></p>
  <p>
    <img src="https://img.shields.io/badge/OS-Windows-0078D4?logo=windows&logoColor=white" alt="Windows">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Browser-Playwright-2EAD33?logo=playwright&logoColor=white" alt="Playwright">
    <img src="https://img.shields.io/badge/Mode-Desktop%20%2B%20CLI-2D8C61" alt="Desktop and CLI">
  </p>
</div>

> **프로젝트 상태** · 소스 코드와 Windows x64 배포본을 제공합니다. [릴리스](../../releases)에서 최신 ZIP과 SHA-256 체크섬을 확인하세요.

> **안내** · 이 프로젝트는 NAVER 또는 해피빈과 제휴·승인·후원 관계가 없는 비공식 도구입니다. 권한이 있는 계정과 목적지에서만 사용하고 NAVER 이용약관 및 관련 정책을 따르세요. 실행 결과나 콩 적립, 서비스의 지속적인 이용 가능성은 보장되지 않습니다. 소프트웨어는 관련 법률이 허용하는 범위에서 보증 없이 제공됩니다.

## 한눈에 보기

콩콩줍줍은 눈에 보이는 Chromium 브라우저를 사용해 로그인 상태를 확인하고, 설정된 작업을 순서대로 실행합니다. 데스크톱 화면에서는 단계별 진행 상태와 로그를 보고 실행을 중지할 수 있고, CLI에서는 같은 자동화 흐름을 실행하거나 로컬 프로필과 세션 백업 상태를 확인할 수 있습니다.

| 영역 | 현재 기능 |
| --- | --- |
| 데스크톱 UI | 실행·중지, 단계별 진행률, 로그, 이번 실행에서 감지한 결과 |
| 로그인 | QR 로그인을 먼저 안내하고, 필요한 경우 브라우저에서 직접 로그인 |
| 블로그 | 템플릿으로 게시물을 작성하고 비공개 설정을 선택해 발행 시도 |
| 카페 | 환경변수로 지정한 카페에서 게시물 작성 및 콩배너 확인 |
| 콩배너 | 게시물 페이지와 알려진 블로그·카페 페이지에서 배너 탐색 |
| 해피빈 | 메인 페이지의 팝업·콩 받기 배너·오늘의 Pick 확인 |
| 프로필 | Windows 사용자별 Chromium 프로필과 로컬 설정 관리 |
| CLI 상태 | <code>--status</code>로 세션 백업 파일의 존재와 경과 정보를 확인 |

### 실행 순서

~~~mermaid
flowchart LR
    A[로그인 확인] --> B[블로그 게시]
    B --> C[카페 게시<br/>목적지 설정 시]
    C --> D[블로그·카페<br/>콩배너 탐색]
    D --> E[해피빈 메인<br/>콩 수집]
~~~

카페 단계는 <code>HAPPYBIN_CAFE_ID</code>와 <code>HAPPYBIN_CAFE_URL</code>을 모두 설정했을 때 목적지로 이동합니다. 블로그·카페 글쓰기는 실제 게시 동작을 수행할 수 있습니다. 실행 전 계정, 목적지, 게시물 템플릿을 직접 확인하세요.

## 기술 구성

- **Python 3.10 이상** — 자동화 흐름과 UI를 구성합니다.
- **Playwright 동기 API + Chromium** — Playwright가 관리하는 Chromium을 화면에 표시하고 persistent browser context로 실행합니다. 시스템 Chrome은 사용하지 않습니다.
- **Tkinter** — 단계, 진행률, 로그, 실행·중지 기능을 제공하는 Windows 데스크톱 UI입니다.
- **공통 실행 흐름** — UI와 <code>--cli</code>가 <code>automation.py</code>의 같은 단계별 실행 함수를 사용합니다.
- **Windows 화면 API** — 화면 크기와 브라우저 배치를 위해 Windows <code>user32</code> API를 사용합니다. 전체 기능에는 대화형 Windows 데스크톱이 필요합니다.
- **최소 외부 패키지** — <code>requirements.txt</code>에는 Playwright만 선언되어 있습니다.

블로그 게시물의 제목과 본문 템플릿은 <code>content/templates.py</code>에 있습니다. 현재 기본 템플릿은 고정 제목과 임의 숫자 본문을 사용하므로, 자동 실행 전에 내용을 살펴보세요.

## 설치 및 시작

Windows PowerShell에서 실행합니다.

~~~powershell
git clone https://github.com/sontheo/happybin_auto.git
cd happybin_auto

python -m venv .venv
$env:PLAYWRIGHT_BROWSERS_PATH = "0"

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium

# 옵션 확인 후 데스크톱 UI 실행
.\.venv\Scripts\python.exe main.py --help
.\.venv\Scripts\python.exe main.py
~~~

<code>PLAYWRIGHT_BROWSERS_PATH=0</code>은 Chromium을 애플리케이션의 기본 검색 위치에 설치하도록 지정합니다. 설치와 실행을 같은 PowerShell 세션에서 진행하세요. 브라우저가 열리면 화면 안내에 따라 로그인합니다. 자동화가 동작하는 동안 브라우저 탭을 직접 조작하지 마세요.

## 사용 방법

~~~powershell
# 데스크톱 UI
.\.venv\Scripts\python.exe main.py

# UI 없이 같은 자동화 흐름 실행
.\.venv\Scripts\python.exe main.py --cli

# 별도 로컬 프로필로 CLI 실행
.\.venv\Scripts\python.exe main.py --cli --user my-profile

# 로컬 세션 백업 정보 확인
.\.venv\Scripts\python.exe main.py --status

# 등록된 로컬 프로필 확인
.\.venv\Scripts\python.exe main.py --list-users

# 선택한 프로필의 로그인 데이터 초기화
.\.venv\Scripts\python.exe main.py --reset-login --user my-profile
~~~

| 옵션 | 설명 |
| --- | --- |
| <code>--cli</code> | 데스크톱 UI 대신 CLI로 자동화 실행 |
| <code>--user NAME</code> | NAVER 로그인 ID가 아닌 로컬 데이터 프로필 선택 |
| <code>--status</code> | <code>session.json</code> 백업의 존재 여부와 경과 정보를 표시 |
| <code>--list-users</code> | 로컬에 설정 파일이 등록된 프로필 목록 표시 |
| <code>--reset-login</code> | 선택한 프로필의 세션 백업과 Chromium 프로필 삭제 |
| <code>--help</code> | 옵션 표시 |

<code>--status</code>는 저장된 세션 백업 파일을 요약합니다. NAVER에 실시간 접속해 로그인 여부나 계정 상태를 확인하는 명령은 아닙니다. 실제 로그인 상태는 자동화 시작 시 브라우저에서 확인합니다. <code>--reset-login</code>을 실행하면 해당 프로필의 브라우저 로그인 데이터가 삭제됩니다.

## 카페 설정

카페 자동화는 기본으로 비활성화되어 있습니다. 권한이 있는 목적지의 ID와 URL을 **같은 PowerShell 세션**에 설정한 다음 실행하세요.

~~~powershell
$env:HAPPYBIN_CAFE_ID = "12345678"
$env:HAPPYBIN_CAFE_URL = "https://cafe.naver.com/your-cafe"

.\.venv\Scripts\python.exe main.py
~~~

<code>HAPPYBIN_CAFE_ID</code>에는 양의 숫자 ID를, <code>HAPPYBIN_CAFE_URL</code>에는 그 ID와 일치하는 카페 URL을 지정합니다. 한쪽이라도 빠지면 카페 글쓰기와 카페 메인 배너 탐색은 건너뜁니다. 이 프로그램은 <code>.env</code> 파일을 자동으로 읽지 않습니다. 개인·조직의 실제 카페 주소를 소스 코드나 공개 예제에 넣지 마세요.

## 로컬 데이터와 개인정보

프로필별 데이터는 소스 폴더 밖의 다음 위치에 저장됩니다.

~~~text
%LOCALAPPDATA%/HappyBeanAuto/<profile>/
├── browser/          # 로그인 상태를 포함한 Chromium 프로필
├── session.json      # 쿠키가 포함될 수 있는 Playwright 세션 백업
└── user_config.json  # 로컬 프로필 설정
~~~

<code>LOCALAPPDATA</code>가 없으면 <code>~/AppData/Local/HappyBeanAuto/</code>를 사용합니다. 새 데이터 위치가 없고 실행 폴더에 기존 <code>user_data/</code>가 있으면 첫 실행 때 이전을 시도합니다.

<code>session.json</code>은 애플리케이션에서 암호화하지 않습니다. 브라우저 프로필과 쿠키는 계정 접근 정보로 취급하고, 공유 컴퓨터에서는 운영체제 계정과 폴더 권한을 보호하세요. 세션 파일, 브라우저 프로필, <code>.env</code>, 인증된 페이지 캡처, 민감 정보가 남은 로그를 Git이나 이슈에 올리지 마세요.

## 저장소 구조

| 경로 | 역할 |
| --- | --- |
| <code>main.py</code> | 실행 진입점, UI/CLI 선택, 프로필·세션 상태 옵션 |
| <code>automation.py</code> | 로그인부터 수집까지 공통 실행 순서, 진행 콜백과 중지 처리 |
| <code>ui.py</code> | Tkinter 데스크톱 UI와 로그·진행 상태 표시 |
| <code>config.py</code> | 카페 환경변수 및 공통 타이밍 설정 |
| <code>content/templates.py</code> | 블로그·카페 게시물 제목과 본문 템플릿 |
| <code>modules/login.py</code> | Chromium persistent context와 QR/브라우저 로그인 |
| <code>modules/session_manager.py</code> | 세션 백업, 쿠키 확인, 로그인 상태 및 CAPTCHA 감지 |
| <code>modules/user_manager.py</code> | 로컬 프로필·설정·브라우저 데이터 관리 |
| <code>modules/paths.py</code> | 실행 경로와 사용자 데이터 위치 결정 및 이전 |
| <code>modules/blog.py</code> · <code>modules/cafe.py</code> | 블로그·카페 게시물 작성과 발행 후 배너 확인 |
| <code>modules/bean_banner.py</code> | 콩배너 탐색, 확장, 클릭 및 페이지별 결과 수집 |
| <code>modules/happybean.py</code> | 해피빈 메인 페이지 팝업과 콩 받기 콘텐츠 처리 |
| <code>modules/kin.py</code> | 지식인 페이지용 콩배너 도우미 |
| <code>modules/utils.py</code> | 페이지 이동과 Windows 화면 크기·창 배치 유틸리티 |
| <code>test_*.py</code>, <code>verify_*.py</code>, <code>check_banners.py</code> | 로그인 브라우저를 사용하는 수동 통합 점검 스크립트 |
| <code>requirements.txt</code> | Python 외부 의존성 |

## 실행 전 확인할 점

- **실제 게시물이 생성될 수 있습니다.** 기본 전체 흐름은 블로그 글쓰기와 게시를 시도합니다. 카페를 설정했다면 카페에도 글을 등록할 수 있습니다.
- **블로그 비공개 설정은 보장되지 않습니다.** 게시 과정에서 비공개 선택을 시도하지만, 선택 결과가 성공적으로 적용됐는지 확인하지 않습니다. 민감한 내용은 템플릿으로 사용하지 마세요.
- **배너 탐지와 콩 적립은 보장되지 않습니다.** 페이지 구조, 캠페인 노출, 로그인·네트워크 상태가 달라질 수 있습니다. 화면의 실행 결과는 자동화가 관찰한 신호이며, 실제 적립 내역은 해피빈에서 확인하세요.
- **수동 점검 스크립트도 실제 계정에 접속합니다.** 이름에 <code>test</code>나 <code>verify</code>가 있어도 격리된 단위 테스트가 아닙니다. 일부 스크립트는 블로그·카페 게시와 배너 클릭을 수행할 수 있으므로 내용을 확인하기 전에 실행하지 마세요.
- **서비스 UI가 바뀌면 자동화가 중단될 수 있습니다.** 선택자와 페이지 흐름이 NAVER 화면에 의존합니다.

## 라이선스

저장소에 프로젝트 라이선스가 지정되어 있지 않습니다. 이 README는 프로젝트 코드나 제3자 소프트웨어에 별도의 사용 권한을 부여하지 않습니다. 의존성과 제3자 자산에는 각각의 라이선스 및 이용 조건이 적용됩니다.
