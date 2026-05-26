@echo off
setlocal

REM =====================================================
REM  tsumitate-navi : ONE-TIME domain migration helper
REM  Use AFTER you Pull origin in GitHub Desktop.
REM
REM  What this does:
REM    1) Copies OneDrive -^> C:\GITHub\tsumitate-navi (/E, no delete)
REM    2) Runs PowerShell URL fix on C:\GITHub\tsumitate-navi
REM       (catches the 5/24 article and anything else still
REM        referencing jehita17-debug.github.io/tsumitate-navi)
REM =====================================================

set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"
set "DST=C:\GITHub\tsumitate-navi"

echo.
echo =====================================================
echo  Domain migration: -^> tsumitate-navi.net
echo =====================================================
echo  From : %SRC%
echo  To   : %DST%
echo.
echo  Pre-flight checklist (please confirm before proceeding):
echo    [ ] You clicked "Pull origin" in GitHub Desktop.
echo    [ ] o-namae.com DNS records are saved.
echo.

if not exist "%DST%" (
  echo ERROR: %DST% not found.
  pause
  exit /b 1
)

set /p CONFIRM="Pulled origin already? Proceed? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
  echo Cancelled.
  pause
  exit /b 0
)

echo.
echo --- Step 1/2 : Robocopy OneDrive -^> GitHub repo ---
echo.

REM Exclude feed/index/sitemap so we keep the freshly pulled versions
REM (they contain the 5/24 entry from GitHub Actions). URL fix runs next.
robocopy "%SRC%" "%DST%" /E /XD .git node_modules /XF sync_to_github.bat migrate_to_net_domain.bat *.log feed.xml index.html sitemap.xml /R:2 /W:1 /NFL /NDL

set RC=%ERRORLEVEL%
if %RC% GEQ 8 (
  echo.
  echo Robocopy ERROR ^(exit %RC%^). Aborting.
  pause
  exit /b 1
)

echo.
echo --- Step 2/2 : PowerShell URL fix on GitHub repo ---
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$root='%DST%'; $exts=@('.html','.xml','.txt','.svg','.py','.md'); $total=0; Get-ChildItem -Path $root -Recurse -File | Where-Object { $exts -contains $_.Extension -and $_.FullName -notmatch '\\\.git\\' -and $_.FullName -notmatch '\\node_modules\\' } | ForEach-Object { $c=Get-Content $_.FullName -Raw -Encoding UTF8; if ($c -and ($c -match 'jehita17-debug\.github\.io')) { $c2=$c -replace 'https://jehita17-debug\.github\.io/tsumitate-navi','https://tsumitate-navi.net' -replace 'jehita17-debug\.github\.io/tsumitate-navi','tsumitate-navi.net'; [System.IO.File]::WriteAllText($_.FullName, $c2, (New-Object System.Text.UTF8Encoding $false)); Write-Host ('  fixed: ' + $_.FullName.Substring($root.Length+1)); $script:total++ } }; Write-Host '---'; Write-Host ('Files fixed: ' + $total)"

echo.
echo =====================================================
echo  Done.
echo.
echo  Next steps in GitHub Desktop:
echo    1^) Review the diff (CNAME / many URL changes)
echo    2^) Commit Summary: domain migration to tsumitate-navi.net
echo    3^) Push origin
echo.
echo  Then wait 10-30 min and try:
echo    https://tsumitate-navi.net/
echo =====================================================
echo.

pause
endlocal
