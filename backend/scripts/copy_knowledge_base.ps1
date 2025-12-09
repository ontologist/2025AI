# Script to copy all AI-300 course materials to knowledge base
# Run from project root directory

$ErrorActionPreference = "Continue"

Write-Host "Copying AI-300 course materials to knowledge base..." -ForegroundColor Green

# Get project root (parent of backend directory)
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$kbPath = Join-Path $projectRoot "backend\knowledge_base"

Write-Host "Project root: $projectRoot" -ForegroundColor Yellow
Write-Host "Knowledge base: $kbPath" -ForegroundColor Yellow

# Create knowledge base directories
$directories = @("docs", "weeks", "resources")
foreach ($dir in $directories) {
    $destPath = Join-Path $kbPath $dir
    if (!(Test-Path $destPath)) {
        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
        Write-Host "Created directory: $destPath" -ForegroundColor Cyan
    }
}

# Copy docs folder (main course website)
$docsSource = Join-Path $projectRoot "docs"
$docsDest = Join-Path $kbPath "docs"

if (Test-Path $docsSource) {
    Write-Host "Copying docs folder..." -ForegroundColor Cyan
    Copy-Item -Path "$docsSource\*" -Destination $docsDest -Recurse -Force -ErrorAction SilentlyContinue
    
    $fileCount = (Get-ChildItem -Path $docsDest -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "  ✓ Copied $fileCount files from docs" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Source not found: $docsSource" -ForegroundColor Yellow
}

# Copy PDF if exists
$pdfSource = Join-Path $projectRoot "大用先生_人工知能基礎.pdf"
if (Test-Path $pdfSource) {
    Write-Host "Copying course PDF..." -ForegroundColor Cyan
    $pdfDest = Join-Path $kbPath "resources"
    Copy-Item -Path $pdfSource -Destination $pdfDest -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Copied course PDF" -ForegroundColor Green
}

# Copy README
$readmeSource = Join-Path $projectRoot "README.md"
if (Test-Path $readmeSource) {
    Copy-Item -Path $readmeSource -Destination $kbPath -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Copied README.md" -ForegroundColor Green
}

# Summary
$totalFiles = (Get-ChildItem -Path $kbPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "`nTotal files in knowledge base: $totalFiles" -ForegroundColor Green

Write-Host "`nKnowledge base structure:" -ForegroundColor Cyan
Get-ChildItem -Path $kbPath -Directory | ForEach-Object {
    $fileCount = (Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "  $($_.Name): $fileCount files" -ForegroundColor Gray
}

Write-Host "`nDone! Now run 'python scripts/load_knowledge_base.py' to ingest into vector database." -ForegroundColor Green

