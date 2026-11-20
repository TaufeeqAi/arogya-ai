# Restarts the Aarogya backend as a detached process (keeps ngrok running).
$root = Split-Path -Parent $PSScriptRoot
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'uvicorn|spawn_main' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -Confirm:$false -ErrorAction SilentlyContinue }
Start-Sleep 2
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$root\backend`" && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > `"$root\server.log`" 2>&1" -WindowStyle Hidden
$ok = $false
for ($i = 0; $i -lt 45 -and -not $ok; $i++) {
  Start-Sleep 2
  try { $h = Invoke-RestMethod http://localhost:8000/api/health -TimeoutSec 3; $ok = $true } catch {}
}
if ($ok) { "backend up: " + ($h | ConvertTo-Json -Compress) } else { "backend FAILED - see server.log"; Get-Content "$root\server.log" -Tail 20 }
