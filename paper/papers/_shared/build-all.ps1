# =====================================================================
# TECT — build every paper in Docs/papers/papers/Paper-*  (PowerShell)
# =====================================================================
# Iterates the Paper-NN-* subdirectories, invokes build-paper.ps1 on
# each, and reports a final OK/FAIL summary table.
#
# Usage:   .\_shared\build-all.ps1
# =====================================================================
$ErrorActionPreference = "Stop"
$root  = Split-Path -Parent $MyInvocation.MyCommand.Path
$paperRoot = Split-Path -Parent $root

$paperDirs = Get-ChildItem -Path $paperRoot -Directory `
              | Where-Object { $_.Name -match '^Paper-[0-9]+' } `
              | Sort-Object Name

$results = @()
foreach ($d in $paperDirs) {
  $stem = Get-ChildItem -Path $d.FullName -Filter "Paper-*.tex" `
          | Select-Object -First 1
  if (-not $stem) { continue }
  $paperStem = Join-Path $d.FullName ([System.IO.Path]::GetFileNameWithoutExtension($stem.Name))
  Write-Host ""
  Write-Host "============================================================"
  Write-Host "  Building $($d.Name)\$($stem.BaseName)"
  Write-Host "============================================================"
  try {
    & "$root\build-paper.ps1" $paperStem
    $results += [pscustomobject]@{ Paper=$d.Name; Status="OK"; Code=$LASTEXITCODE }
  } catch {
    $results += [pscustomobject]@{ Paper=$d.Name; Status="FAIL"; Code=$LASTEXITCODE }
  }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "  Summary"
Write-Host "============================================================"
$results | Format-Table -AutoSize
