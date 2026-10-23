# Stop only FastAPI/ngrok processes previously started by this project's One-Click launcher.
# Windows PowerShell 5.1+; no extra software required.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$hadError = $false
$expectedPython = [System.IO.Path]::GetFullPath((Join-Path $root '.venv\Scripts\python.exe'))

foreach ($label in @('uvicorn', 'ngrok')) {
    $pidFile = Join-Path $root ".demo-$label.pid"
    if (-not (Test-Path -LiteralPath $pidFile)) {
        Write-Host "[INFO] No recorded $label process."
        continue
    }

    $saved = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    $processId = 0
    if (-not [int]::TryParse($saved, [ref]$processId) -or $processId -le 0) {
        Write-Host "[WARN] Invalid PID in $pidFile; deleting stale file."
        Remove-Item -LiteralPath $pidFile -Force
        continue
    }

    try {
        $processInfo = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $processId" -ErrorAction Stop
        if ($null -eq $processInfo) {
            Write-Host "[INFO] $label already stopped (PID $processId)."
            Remove-Item -LiteralPath $pidFile -Force
            continue
        }

        $line = [string]$processInfo.CommandLine
        $binary = [string]$processInfo.ExecutablePath
        $match = $false
        if ($label -eq 'uvicorn') {
            # Verify the PID is running the *project's* Python environment and uvicorn on port 8000.
            $match = (($binary -ieq $expectedPython) -and
                      ($line -match '(?i)\buvicorn\b') -and
                      ($line -match '(?i)main:app') -and
                      ($line -match '(?i)--port\s+8000\b'))
        } else {
            # The ngrok PID must have been recorded by this launcher and be forwarding port 8000.
            $match = (($binary -match '(?i)ngrok(?:\.exe)?$') -and
                      ($line -match '(?i)\bhttp\s+8000\b'))
        }

        if ($match) {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host "[OK] Stopped $label (PID $processId)."
            Remove-Item -LiteralPath $pidFile -Force
        } else {
            Write-Host "[SAFE] PID $processId does not match the expected $label command; nothing killed."
            Write-Host "       Remove the stale PID file only after checking the process."
        }
    } catch {
        Write-Host "[ERROR] Failed to check/stop $label (PID $processId): $($_.Exception.Message)"
        $hadError = $true
    }
}

Write-Host '[NOTE] This does NOT stop ngrok or FastAPI started manually in separate terminals.'
if ($hadError) { exit 1 }
exit 0
