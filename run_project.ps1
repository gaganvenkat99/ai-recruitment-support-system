$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$preferredVenv = Join-Path $projectRoot "venv_python3119\Scripts\python.exe"
$fallbackVenv = Join-Path $projectRoot "venv_clean\Scripts\python.exe"

$pythonExe = if (Test-Path $preferredVenv) { $preferredVenv } else { $fallbackVenv }

$backendPort = 8006
$frontendPort = 8501

# ==============================
# SAFE PORT KILL FUNCTION
# ==============================
function Kill-Port {
    param([int]$port)

    $connections = netstat -ano | findstr ":$port"

    foreach ($conn in $connections) {
        $parts = $conn -split "\s+"
        $processId = $parts[-1]

        # Only valid numeric PIDs
        if ($processId -match "^\d+$") {
            $pidInt = [int]$processId

            # Skip system processes (PID 0 & 4)
            if ($pidInt -gt 4) {
                try {
                    taskkill /PID $pidInt /F | Out-Null
                } catch {}
            }
        }
    }
}

# ==============================
# CHECK PYTHON
# ==============================
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python not found"
    exit 1
}

Write-Host "Cleaning ports..."

Kill-Port $backendPort
Kill-Port $frontendPort

Start-Sleep -Seconds 2

# ==============================
# START BACKEND
# ==============================
Write-Host "Starting Backend..."

$backendCommand = "Set-Location '$projectRoot'; & '$pythonExe' -m uvicorn backend.main:app --host 127.0.0.1 --port $backendPort"

Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $backendCommand `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden

# ==============================
# WAIT FOR BACKEND
# ==============================
Write-Host "Waiting for backend..."

$maxRetries = 10
$retry = 0
$ready = $false

while (-not $ready -and $retry -lt $maxRetries) {
    try {
        $res = Invoke-WebRequest -Uri "http://127.0.0.1:$backendPort" -UseBasicParsing -TimeoutSec 2
        if ($res.StatusCode -eq 200) {
            $ready = $true
        }
    } catch {
        Start-Sleep -Seconds 2
        $retry++
    }
}

# ==============================
# DEBUG MODE IF FAILED
# ==============================
if (-not $ready) {
    Write-Host "Backend failed. Running in visible mode..."

    & $pythonExe -m uvicorn backend.main:app --host 127.0.0.1 --port $backendPort

    exit 1
}

Write-Host "Backend ready"

# ==============================
# START FRONTEND
# ==============================
Write-Host "Starting Frontend..."

$frontendCommand = "Set-Location '$projectRoot'; & '$pythonExe' -m streamlit run frontend/dashboard.py --server.headless true --server.address 127.0.0.1 --server.port $frontendPort"

Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $frontendCommand `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden

Start-Sleep -Seconds 5

# ==============================
# OPEN BROWSER
# ==============================
Start-Process "http://localhost:$frontendPort"

Write-Host "================================="
Write-Host "Project started successfully"
Write-Host "Frontend: http://localhost:$frontendPort"
Write-Host "Backend: http://127.0.0.1:$backendPort"
Write-Host "================================="