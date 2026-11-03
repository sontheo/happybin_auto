<div align="center">
  <h1>🌱 Happybin Auto · 콩콩줍줍</h1>
  <p><strong>A Windows tool for running and monitoring NAVER Happybean workflows in a browser</strong></p>
  <p>Blog · Cafe · Bean banners · Happybean</p>
  <p><a href="https://github.com/sontheo/happybin_auto/blob/main/README.md">한국어</a> · <a href="https://github.com/sontheo/happybin_auto/blob/main/README.en.md">English</a></p>
  <p>
    <img src="https://img.shields.io/badge/OS-Windows%20x64-0078D4?logo=windows&logoColor=white" alt="Windows x64">
    <img src="https://img.shields.io/badge/Browser-Playwright-2EAD33?logo=playwright&logoColor=white" alt="Playwright">
    <img src="https://img.shields.io/badge/Mode-Desktop%20%2B%20CLI-2D8C61" alt="Desktop and CLI">
    <img src="https://img.shields.io/badge/License-MIT-blue" alt="MIT License">
  </p>
</div>

> **Legal notice** · This is an unofficial project. It is not affiliated with, endorsed by, or sponsored by NAVER or Happybean. [NAVER's posting policy](https://policy.naver.com/policy/service_group.html) identifies posts made with automated means without NAVER's prior permission as subject to posting restrictions. This program can publish posts automatically; check the policy and obtain any required permission before use. See [Legal notice and responsibility](#legal-notice-and-responsibility).

## Get started

You need **Windows x64 and an interactive desktop**. The release ZIP includes the application and Playwright's Chromium; a separate Python or Git installation is not required.

1. Download `HappybinAuto-windows-x64.zip` from the [latest release](https://github.com/sontheo/happybin_auto/releases/latest).
2. Extract the ZIP and run `HappybinAuto.exe` inside the `HappybinAuto` folder. Keep the included `_internal` folder beside the executable.
3. Select **자동 수집 시작** (start collection). When the browser opens, follow its prompts to sign in to NAVER. Do not manually operate its tabs while automation is running.
4. Review the progress and logs. The stop button requests that the current run stop.

## Before running

- **Real posts may be published.** The default workflow attempts to publish a blog post; it can also publish to a configured cafe. The default post uses a fixed title and a random numeric body.
- **Private blog visibility is not guaranteed.** The program attempts to select private visibility but does not verify that it was applied. Do not post sensitive content.
- **Check results in the services.** The interface reports signals observed by the automation. Check NAVER and Happybean directly for publication, visibility, and credited beans.
- **Changes to a service's interface or policies can break automation.** Accounts or posts may be restricted, sign-in may be requested, and collection can fail.

## Workflow

Check sign-in → attempt blog publication → attempt cafe publication if configured → scan blog and cafe bean banners → check collection content on the Happybean home page. Outcomes depend on sign-in and service state.

## Cafe configuration

Cafe operations are disabled by default. Set the numeric ID and URL of an authorized cafe in the same PowerShell session before launching the program. These values are examples:

```powershell
$env:HAPPYBIN_CAFE_ID = "12345678"
$env:HAPPYBIN_CAFE_URL = "https://cafe.naver.com/your-cafe"
.\HappybinAuto.exe
```

Both values are required for cafe posting and the cafe home-page banner scan. The ID must be a positive integer and the URL should identify the same cafe. The application does not automatically load `.env` files. Unless saved separately, these environment variables disappear when the PowerShell window closes.

## Command-line options

Open PowerShell in the extracted `HappybinAuto` folder. `--user` selects a local profile, not a NAVER ID.

```powershell
.\HappybinAuto.exe --help
.\HappybinAuto.exe --cli
.\HappybinAuto.exe --status
.\HappybinAuto.exe --list-users
.\HappybinAuto.exe --reset-login --user my-profile
.\HappybinAuto.exe --check-browser
```

`--cli` can perform real automation and posting. `--status` reports the existence and age of the local `session.json` backup; it does not check live login status. `--reset-login` deletes the selected profile's session backup and browser data. `--check-browser` checks that the bundled Chromium starts.

## Login and local data

Profile data is stored under `%LOCALAPPDATA%\HappyBeanAuto\<profile>\`. `browser` contains the browser profile, while `session.json` is a session backup that may include cookies. If `LOCALAPPDATA` is unavailable, the program uses `AppData\Local\HappyBeanAuto` under the user's home directory. It attempts a one-time migration if the old `user_data` folder exists beside the application and the new data folder does not.

**The application does not encrypt the session backup.** Protect cookies, browser profiles, and logs containing login data as account credentials. Do not share session files or authenticated screenshots in GitHub, issues, or with other people.

## Legal notice and responsibility

- **Service policies:** Review [NAVER's Terms of Service](https://policy.naver.com/policy/service.html), [posting policy](https://policy.naver.com/policy/service_group.html), [account policy](https://policy.naver.com/rules/service_group2.html), and any service-specific policies. The posting policy identifies automated posts made without prior permission as subject to restrictions. Distribution of this tool and its MIT license do not grant NAVER's permission.
- **User responsibility:** Use only accounts and destinations you are authorized to access, obtain any required permissions, and check your content, other parties' rights, and applicable laws. Accounts or posts may be restricted.
- **Trademarks and third-party rights:** NAVER, Happybean, and other names and marks belong to their respective owners. The project license does not grant rights to third-party services, trademarks, or content.
- **Warranty and liability:** The project is provided as is under the MIT License. To the extent permitted by applicable law, it is provided without express or implied warranties; the [MIT License text](https://github.com/sontheo/happybin_auto/blob/main/LICENSE) governs author and copyright-holder liability. Rights that cannot be excluded by mandatory law are unaffected.

## License and third-party software

Project code is distributed under the [MIT License](https://github.com/sontheo/happybin_auto/blob/main/LICENSE). Copies or substantial portions must retain the copyright and license notices. Playwright, Chromium, and other components have their own licenses and notices; the MIT License does not replace them.

Source code and build configuration are available in the [repository](https://github.com/sontheo/happybin_auto). The repository's `test_*.py`, `verify_*.py`, and `check_banners.py` files are manual integration tools that may perform real sign-ins, posts, or clicks.
