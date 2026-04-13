# RAC - Source Update Script (Windows)
# Downloads latest src/ from remote and replaces bundled source.
# No git required - downloads a zip archive.
#
# Usage: .\update.ps1 [branch]
#   branch: git branch to download (default: main)

param(
    [string]$Branch = "main"
)

$RepoUrl = "https://github.com/januvary/RAC/archive/refs/heads/$Branch.zip"

$AppDir = Split-Path -Parent $PSScriptRoot
$SrcDir = Join-Path $AppDir "_internal\src"
$BackupDir = Join-Path $AppDir "_internal\src_backup"
$TempDir = Join-Path $env:TEMP "rac_update_$(Get-Random)"

Write-Host "=== RAC Update ===" -ForegroundColor Cyan
Write-Host "Branch: $Branch"
Write-Host ""

if (-not (Test-Path $SrcDir)) {
    Write-Host "[ERROR] Cannot find _internal\src\ - is this the right directory?" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Downloading latest source..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
$ZipPath = Join-Path $TempDir "source.zip"

try {
    Invoke-WebRequest -Uri $RepoUrl -OutFile $ZipPath -UseBasicParsing
} catch {
    Write-Host "[ERROR] Download failed: $_" -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir
    exit 1
}

if (-not (Test-Path $ZipPath) -or (Get-Item $ZipPath).Length -eq 0) {
    Write-Host "[ERROR] Downloaded file is empty. Check REPO_URL and Branch." -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir
    exit 1
}

Write-Host "[2/4] Extracting..." -ForegroundColor Yellow
$ExtractDir = Join-Path $TempDir "extracted"
Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

$ExtractedSrc = Get-ChildItem -Path $ExtractDir -Recurse -Directory -Filter "src" |
    Where-Object { $_.FullName -match "RAC-[^\\]+\\src$" } |
    Select-Object -First 1

if (-not $ExtractedSrc) {
    Write-Host "[ERROR] Could not find src\ in downloaded archive." -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir
    exit 1
}

Write-Host "[3/4] Replacing source files..." -ForegroundColor Yellow
if (Test-Path $BackupDir) {
    Remove-Item -Recurse -Force $BackupDir
}
Move-Item -Path $SrcDir -Destination $BackupDir
Copy-Item -Path $ExtractedSrc.FullName -Destination $SrcDir -Recurse

Get-ChildItem -Path $SrcDir -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force

Write-Host "[4/4] Cleaning up..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $TempDir

Write-Host ""
Write-Host "Update complete!" -ForegroundColor Green
Write-Host "Backup saved to _internal\src_backup\"
Write-Host "Restart RAC to apply changes."
Write-Host ""
Write-Host "To rollback: Move-Item '_internal\src_backup\' '_internal\src\'"
