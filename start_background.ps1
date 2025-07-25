# Fantasy Baseball App Background Starter
# This script starts the Streamlit app in the background and keeps it running

param(
    [string]$Port = "8501",
    [switch]$Force
)

# Get the script directory (where this PowerShell script is located)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Configuration
$AppName = "FantasyBaseballApp"
$VenvPath = ".\.venv"
$MainScript = "src\main_app.py"
$LogFile = "output\app.log"
$PidFile = "output\app.pid"

# Ensure output directory exists
if (!(Test-Path "output")) {
    New-Item -ItemType Directory -Path "output" -Force | Out-Null
}

# Function to check if app is already running
function Test-AppRunning {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            return $true
        }
        else {
            # Clean up stale PID file
            Remove-Item $PidFile -ErrorAction SilentlyContinue
            return $false
        }
    }
    return $false
}

# Function to stop existing app
function Stop-App {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid) {
            Write-Host "Stopping existing app (PID: $pid)..."
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        Remove-Item $PidFile -ErrorAction SilentlyContinue
    }
    
    # Also kill any streamlit processes running our script
    Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*streamlit*main_app.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue
}

# Check if already running
if (Test-AppRunning -and !$Force) {
    Write-Host "$AppName is already running. Use -Force to restart." -ForegroundColor Yellow
    $pid = Get-Content $PidFile
    Write-Host "Current PID: $pid" -ForegroundColor Green
    Write-Host "App should be accessible at: http://localhost:$Port" -ForegroundColor Green
    exit 0
}

# Stop existing instance if force restart
if ($Force) {
    Stop-App
}

Write-Host "Starting $AppName..." -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Activate virtual environment
$ActivateScript = "$VenvPath\Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & $ActivateScript
}
else {
    Write-Error "Virtual environment activation script not found"
    exit 1
}

# Install/update requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing/updating requirements..." -ForegroundColor Cyan
    pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Some packages may have failed to install, but continuing..."
    }
}

# Check if main script exists
if (!(Test-Path $MainScript)) {
    Write-Error "Main script not found: $MainScript"
    exit 1
}

# Start the app in background
Write-Host "Launching Streamlit app on port $Port..." -ForegroundColor Green

# Create the background process
$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$ProcessInfo.FileName = "python"
$ProcessInfo.Arguments = "-m streamlit run `"$MainScript`" --server.port $Port --server.headless true --server.runOnSave false"
$ProcessInfo.WorkingDirectory = $ScriptDir
$ProcessInfo.UseShellExecute = $false
$ProcessInfo.CreateNoWindow = $true
$ProcessInfo.RedirectStandardOutput = $true
$ProcessInfo.RedirectStandardError = $true

$Process = New-Object System.Diagnostics.Process
$Process.StartInfo = $ProcessInfo

# Start the process
$Process.Start() | Out-Null

# Save PID for later management
$Process.Id | Out-File -FilePath $PidFile -Encoding ASCII

# Log initial startup info
$StartupInfo = @"
=== Fantasy Baseball App Started ===
Timestamp: $(Get-Date)
PID: $($Process.Id)
Port: $Port
Working Directory: $ScriptDir
Command: python -m streamlit run "$MainScript" --server.port $Port --server.headless true
=== End Startup Info ===

"@

$StartupInfo | Out-File -FilePath $LogFile -Encoding UTF8

Write-Host "App started successfully!" -ForegroundColor Green
Write-Host "PID: $($Process.Id)" -ForegroundColor Cyan
Write-Host "Log file: $LogFile" -ForegroundColor Cyan
Write-Host "App will be accessible at: http://localhost:$Port" -ForegroundColor Green
Write-Host ""
Write-Host "To stop the app later, run: Stop-Process -Id $($Process.Id)" -ForegroundColor Yellow
Write-Host "Or delete the PID file: $PidFile" -ForegroundColor Yellow

# Wait a moment to check if it started successfully
Start-Sleep -Seconds 3
if (!$Process.HasExited) {
    Write-Host "App is running in the background." -ForegroundColor Green
}
else {
    Write-Error "App failed to start. Check the log file: $LogFile"
    Remove-Item $PidFile -ErrorAction SilentlyContinue
    exit 1
}