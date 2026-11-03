<div align="center">
  <h1>🌱 콩콩줍줍</h1>
  <p><strong>네이버 해피빈 작업을 브라우저에서 실행하고 살펴보는 Windows 자동화 도구</strong></p>
  <p>블로그 · 카페 · 콩배너 · 해피빈</p>
  <p><a href="https://github.com/sontheo/happybin_auto/blob/main/README.md">한국어</a> · <a href="https://github.com/sontheo/happybin_auto/blob/main/README.en.md">English</a></p>
  <p>
    <img src="https://img.shields.io/badge/OS-Windows%20x64-0078D4?logo=windows&logoColor=white" alt="Windows x64">
    <img src="https://img.shields.io/badge/Browser-Playwright-2EAD33?logo=playwright&logoColor=white" alt="Playwright">
    <img src="https://img.shields.io/badge/Mode-Desktop%20%2B%20CLI-2D8C61" alt="Desktop and CLI">
    <img src="https://img.shields.io/badge/License-MIT-blue" alt="MIT License">
  </p>
</div>

> **법적 고지** · 이 프로젝트는 NAVER 또는 해피빈의 공식 제품이 아니며, 이들의 제휴·승인·후원을 받지 않았습니다. [네이버 게시물 운영정책](https://policy.naver.com/policy/service_group.html)은 네이버의 사전 허락 없이 자동화 수단으로 게재한 게시물을 게재 제한 대상으로 명시합니다. 이 프로그램은 실제 게시물을 자동 작성하므로 사용 전에 해당 정책과 필요한 허락을 확인하세요. 자세한 내용은 [법적 고지와 이용 책임](#법적-고지와-이용-책임)을 참조하세요.

## 시작하기

**Windows x64와 대화형 데스크톱 환경**이 필요합니다. 배포 ZIP에는 프로그램과 Playwright용 Chromium이 포함되어 있으므로 Python이나 Git을 따로 설치할 필요가 없습니다.

1. [최신 릴리스](https://github.com/sontheo/happybin_auto/releases/latest)에서 `HappybinAuto-windows-x64.zip`을 다운로드합니다.
2. ZIP을 폴더째 압축 해제하고, `HappybinAuto` 폴더의 `HappybinAuto.exe`를 실행합니다. 함께 제공되는 `_internal` 폴더를 실행 파일과 같은 위치에 두세요.
3. 화면에서 **자동 수집 시작**을 누르고, 브라우저가 열리면 안내에 따라 NAVER에 로그인합니다. 자동화 중에는 브라우저 탭을 직접 조작하지 마세요.
4. 진행 상태와 로그를 확인합니다. 중지 버튼은 진행 중인 작업에 중지 요청을 보냅니다.

## 실행 전에 확인하세요

- **실제 글이 게시될 수 있습니다.** 기본 흐름은 블로그 글 발행을 시도하고, 카페 목적지를 설정하면 카페에도 글을 발행할 수 있습니다. 기본 게시물에는 고정 제목과 임의 숫자 본문이 사용됩니다.
- **블로그 비공개 발행은 보장되지 않습니다.** 비공개 선택을 시도하지만 선택이 실제로 적용됐는지 확인하지 않습니다. 민감한 내용은 게시하지 마세요.
- **결과는 서비스에서 직접 확인하세요.** 화면에는 자동화가 감지한 결과가 표시됩니다. 게시 여부와 공개 범위, 콩 적립 내역은 NAVER와 해피빈에서 확인해야 합니다.
- **서비스 화면이나 정책이 바뀌면 동작하지 않을 수 있습니다.** 계정 제한, 게시물 제한, 로그인 요청 또는 적립 실패가 발생할 수 있습니다.

## 동작 순서

로그인 확인 → 블로그 게시 시도 → 카페 게시 시도(설정된 경우) → 블로그·카페 콩배너 탐색 → 해피빈 메인 콩 받기 콘텐츠 확인. 각 단계의 실행 결과는 로그인 상태와 서비스 화면에 따라 달라집니다.

## 카페 설정

카페 작업은 기본적으로 꺼져 있습니다. 허락받은 카페의 숫자 ID와 URL을 같은 PowerShell 세션에 설정한 뒤 그 세션에서 실행하세요. 아래 값은 예시입니다.

```powershell
$env:HAPPYBIN_CAFE_ID = "12345678"
$env:HAPPYBIN_CAFE_URL = "https://cafe.naver.com/your-cafe"
.\HappybinAuto.exe
```

두 값이 모두 있어야 카페 글쓰기와 카페 메인 배너 탐색을 시도합니다. ID는 양의 정수여야 하며 URL은 같은 카페를 가리켜야 합니다. 이 프로그램은 `.env` 파일을 자동으로 읽지 않습니다. 값을 영구 저장하지 않으면 해당 PowerShell 창을 닫을 때 설정이 사라집니다.

## 명령줄 옵션

압축을 푼 `HappybinAuto` 폴더에서 PowerShell을 열고 실행합니다. `--user`는 NAVER ID가 아니라 로컬 프로필 이름입니다.

```powershell
.\HappybinAuto.exe --help
.\HappybinAuto.exe --cli
.\HappybinAuto.exe --status
.\HappybinAuto.exe --list-users
.\HappybinAuto.exe --reset-login --user my-profile
.\HappybinAuto.exe --check-browser
```

`--cli`도 실제 자동화와 게시를 수행할 수 있습니다. `--status`는 로컬 `session.json` 백업의 존재와 경과 정보를 표시하며 실시간 로그인 상태를 확인하지 않습니다. `--reset-login`은 선택한 프로필의 세션 백업과 브라우저 데이터를 삭제합니다. `--check-browser`는 번들 Chromium의 실행을 확인합니다.

## 로그인 정보와 로컬 데이터

프로필 데이터는 `%LOCALAPPDATA%\HappyBeanAuto\<profile>\`에 저장됩니다. `browser`에는 브라우저 프로필이, `session.json`에는 쿠키가 포함될 수 있는 세션 백업이 저장됩니다. `LOCALAPPDATA`가 없으면 사용자 홈의 `AppData\Local\HappyBeanAuto`를 사용합니다. 기존 실행 폴더에 `user_data`가 있고 새 데이터 폴더가 없으면 첫 실행 때 이전을 시도합니다.

**세션 백업은 프로그램에서 암호화하지 않습니다.** 쿠키, 브라우저 프로필과 로그인 정보가 포함된 로그는 계정 접근 정보처럼 보호하세요. 세션 파일이나 인증된 화면 캡처를 GitHub, 이슈 또는 다른 사람에게 공유하지 마세요.

## 법적 고지와 이용 책임

- **서비스 정책:** [네이버 이용약관](https://policy.naver.com/policy/service.html), [게시물 운영정책](https://policy.naver.com/policy/service_group.html), [계정 운영정책](https://policy.naver.com/rules/service_group2.html) 및 개별 서비스 정책을 확인하세요. 게시물 운영정책은 사전 허락 없는 자동화 게시물을 게재 제한 대상으로 정합니다. 이 도구의 제공이나 MIT 라이선스는 NAVER의 허락을 의미하지 않습니다.
- **이용자 책임:** 권한이 있는 계정과 목적지만 사용하고, 필요한 허락을 확보하며, 게시물 내용과 타인의 권리 및 관련 법령을 확인할 책임은 이용자에게 있습니다. 계정이나 게시물에 제한이 생길 수 있습니다.
- **상표와 제3자 권리:** NAVER와 해피빈 등 명칭과 상표는 각 권리자에게 속합니다. 프로젝트 라이선스는 제3자 서비스·상표·콘텐츠의 사용 권리를 부여하지 않습니다.
- **보증 및 책임:** 프로젝트는 MIT 라이선스의 조건에 따라 현 상태로 제공됩니다. 적용 법률이 허용하는 범위에서 명시적·묵시적 보증을 하지 않으며, 저작자와 저작권자의 책임에 대해서는 [MIT 라이선스 원문](https://github.com/sontheo/happybin_auto/blob/main/LICENSE)이 적용됩니다. 강행법규상 배제할 수 없는 권리는 영향을 받지 않습니다.

## 라이선스와 제3자 소프트웨어

프로젝트 코드는 [MIT License](https://github.com/sontheo/happybin_auto/blob/main/LICENSE)로 배포됩니다. 배포·복제 시 저작권 표시와 라이선스 고지를 포함해야 합니다. Playwright, Chromium 및 그 밖의 구성요소에는 각자의 라이선스와 고지가 별도로 적용됩니다. MIT 라이선스는 이들의 라이선스를 대체하지 않습니다.

소스 코드와 빌드 구성은 [저장소](https://github.com/sontheo/happybin_auto)에서 확인할 수 있습니다. 저장소의 `test_*.py`, `verify_*.py`, `check_banners.py`는 실제 로그인이나 게시·클릭을 수행할 수 있는 수동 점검 스크립트입니다.
