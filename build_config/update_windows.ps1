# RAC - Script de Atualizacao (Windows)
# Baixa o src/ mais recente do repositorio e substitui os arquivos.
# Nao precisa de git - usa a API do GitHub.
#
# Uso: .\update.ps1 [branch]
#   branch: branch do git para baixar (padrao: master)

param(
    [string]$Branch = "master"
)

$AppDir = $PSScriptRoot
$SrcDir = Join-Path $AppDir "_internal\src"
$BackupDir = Join-Path $AppDir "_internal\src_backup"
$TempBase = if ($env:TEMP) { $env:TEMP } elseif ($env:TMPDIR) { $env:TMPDIR } else { "/tmp" }
$TempDir = Join-Path $TempBase "rac_update_$(Get-Random)"

Write-Host "=== Atualizacao RAC ===" -ForegroundColor Cyan
Write-Host "Branch: $Branch"
Write-Host ""

if (-not (Test-Path $SrcDir)) {
    Write-Host "[ERRO] Nao foi possivel encontrar _internal\src\. Diretorio correto?" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Baixando codigo fonte..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
$ZipPath = Join-Path $TempDir "source.zip"

try {
    $Headers = @{}
    $Token = $env:GITHUB_TOKEN
    if ($Token) {
        $Headers["Authorization"] = "Bearer $Token"
    } elseif (Get-Command gh -ErrorAction SilentlyContinue) {
        $Token = (gh auth token 2>$null)
        if ($Token) {
            $Headers["Authorization"] = "Bearer $Token"
        }
    }

    Invoke-WebRequest -Uri "https://api.github.com/repos/januvary/RAC/zipball/$Branch" -OutFile $ZipPath -Headers $Headers -UseBasicParsing
} catch {
    Write-Host "[ERRO] Falha no download: $_" -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    exit 1
}

if (-not (Test-Path $ZipPath) -or (Get-Item $ZipPath).Length -eq 0) {
    Write-Host "[ERRO] Arquivo baixado esta vazio. Verifique acesso ao repositorio." -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "[2/4] Extraindo..." -ForegroundColor Yellow
$ExtractDir = Join-Path $TempDir "extracted"
Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

$ExtractedSrc = Get-ChildItem -Path $ExtractDir -Recurse -Directory -Filter "src" |
    Where-Object { $_.FullName -match "januvary-RAC-[a-f0-9]+[/\\]src$" } |
    Select-Object -First 1

if (-not $ExtractedSrc) {
    Write-Host "[ERRO] Nao foi possivel encontrar src\ no arquivo baixado." -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "[3/4] Substituindo arquivos..." -ForegroundColor Yellow
if (Test-Path $BackupDir) {
    Remove-Item -Recurse -Force $BackupDir
}
Move-Item -Path $SrcDir -Destination $BackupDir
Copy-Item -Path $ExtractedSrc.FullName -Destination $SrcDir -Recurse

Get-ChildItem -Path $SrcDir -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force

Write-Host "[4/4] Limpando..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $TempDir

Write-Host ""
Write-Host "Atualizacao concluida!" -ForegroundColor Green
Write-Host "Backup salvo em _internal\src_backup\"
Write-Host "Reinicie o RAC para aplicar as alteracoes."
Write-Host ""
Write-Host "Para reverter: Move-Item '_internal\src_backup\' '_internal\src\'"
Write-Host ""
Read-Host "Pressione Enter para fechar"
