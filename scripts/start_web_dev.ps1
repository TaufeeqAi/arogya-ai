# Starts the Expo web dev server on :8081 as a detached process.
$root = Split-Path -Parent $PSScriptRoot
$c = Get-NetTCPConnection -LocalPort 8081 -State Listen -ErrorAction SilentlyContinue
foreach ($p in ($c.OwningProcess | Select-Object -Unique)) { Stop-Process -Id $p -Force -Confirm:$false -ErrorAction SilentlyContinue }
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$root\app`" && set `"CI=1`"&& npx expo start --web --port 8081 > `"$root\web.log`" 2>&1" -WindowStyle Hidden
$ok = $false
for ($i = 0; $i -lt 50 -and -not $ok; $i++) {
  Start-Sleep 2
  try { Invoke-WebRequest http://localhost:8081 -UseBasicParsing -TimeoutSec 3 | Out-Null; $ok = $true } catch {}
}
"expo web dev up: $ok"
