# =====================================================================
# TECT — Master paper-track build pipeline (PowerShell, v2.0)
# =====================================================================
# Builds every TeX paper in the repository's four canonical categories:
#
#   Docs/papers/papers/Paper-*/Paper-*.tex      (Wave 1-7 main papers)
#   Docs/papers/papers/Paper-*/Paper-*-ext.tex  (extension papers)
#   Docs/papers/auxiliary/Auxiliary-*/Auxiliary-*.tex
#   Docs/papers/top_impact/Paper-TI-*/Paper-TI-*.tex
#   Docs/papers/epochs/Epoch-*/Epoch-*.tex
#
# Usage (from repo root):
#   .\Codes\scripts\build-all-papers.ps1
#   .\Codes\scripts\build-all-papers.ps1 -Filter 'Paper-0[0-3]'
#   .\Codes\scripts\build-all-papers.ps1 -Categories papers,top_impact -Clean
#   .\Codes\scripts\build-all-papers.ps1 -Quiet -Parallel 4
#   .\Codes\scripts\build-all-papers.ps1 -ListOnly
#
# Output:
#   - Per-paper PDFs alongside their .tex source
#   - Per-paper *.build.log alongside their .tex source
#   - Master JSON log at Runs/build_logs/build-<timestamp>.json
#   - Console summary table
# =====================================================================
[CmdletBinding()]
param(
  [string]$Filter        = '',
  [string[]]$Categories  = @('papers', 'auxiliary', 'top_impact', 'epochs'),
  [switch]$Clean,
  [switch]$NoBibtex,
  [switch]$Quiet,
  [switch]$ListOnly,
  [int]$Parallel         = 1,    # >=2 enables ForEach-Object -Parallel (PS 7+)
  [string]$LogDir        = ''    # default: <repo>/Runs/build_logs/
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------
# Locate repo root robustly
# ---------------------------------------------------------------------
$scriptPath = $MyInvocation.MyCommand.Path
if (-not $scriptPath) { Write-Host "[FATAL] cannot locate script path"; exit 6 }
$repoRoot = Resolve-Path (Join-Path (Split-Path $scriptPath) '..\..')

$papersRoot = Join-Path $repoRoot 'Docs\papers'
if (-not (Test-Path -LiteralPath $papersRoot -PathType Container)) {
  Write-Host "[FATAL] Docs/papers not found at $papersRoot" -ForegroundColor Red; exit 6
}

# ---------------------------------------------------------------------
# Build target list
# ---------------------------------------------------------------------
$catMap = @{
  'papers'     = @{ Root = (Join-Path $papersRoot 'papers');     Pattern = 'Paper-*';     IgnoreLeaves = @('_shared','_legacy') }
  'auxiliary'  = @{ Root = (Join-Path $papersRoot 'auxiliary');  Pattern = 'Auxiliary-*'; IgnoreLeaves = @() }
  'top_impact' = @{ Root = (Join-Path $papersRoot 'top_impact'); Pattern = 'Paper-TI-*';  IgnoreLeaves = @() }
  'epochs'     = @{ Root = (Join-Path $papersRoot 'epochs');     Pattern = 'Epoch-*';     IgnoreLeaves = @() }
}

$targets = @()
foreach ($cat in $Categories) {
  if (-not $catMap.ContainsKey($cat)) {
    Write-Host "[WARN] unknown category: $cat (skipped)" -ForegroundColor Yellow; continue
  }
  $info = $catMap[$cat]
  if (-not (Test-Path -LiteralPath $info.Root -PathType Container)) {
    Write-Host "[WARN] category root missing: $($info.Root)" -ForegroundColor Yellow; continue
  }
  $dirs = Get-ChildItem -LiteralPath $info.Root -Directory `
            | Where-Object { $_.Name -like $info.Pattern -and ($_.Name -notin $info.IgnoreLeaves) } `
            | Sort-Object Name
  foreach ($d in $dirs) {
    # Find every .tex matching the category pattern in this dir
    $texFiles = Get-ChildItem -LiteralPath $d.FullName -Filter '*.tex' `
                  | Where-Object { $_.Name -like ($info.Pattern + '.tex') } `
                  | Sort-Object Name
    foreach ($t in $texFiles) {
      $stem = [IO.Path]::GetFileNameWithoutExtension($t.Name)
      if ($Filter -and ($stem -notmatch $Filter) -and ($d.Name -notmatch $Filter)) { continue }
      $targets += [pscustomobject]@{
        Category = $cat
        Dir      = $d.FullName
        Stem     = $stem
        TexPath  = $t.FullName
      }
    }
  }
}

if (-not $targets) {
  Write-Host "[INFO] no targets matched Filter='$Filter' Categories=$($Categories -join ',')" -ForegroundColor Yellow
  exit 0
}

Write-Host "[TECT-build-all] $($targets.Count) targets selected" -ForegroundColor Cyan

if ($ListOnly) {
  $targets | Format-Table Category, Stem, Dir -AutoSize
  exit 0
}

# ---------------------------------------------------------------------
# Resolve build-paper.ps1 location
# ---------------------------------------------------------------------
$builder = Join-Path $papersRoot 'papers\_shared\build-paper.ps1'
if (-not (Test-Path -LiteralPath $builder -PathType Leaf)) {
  Write-Host "[FATAL] builder script not found: $builder" -ForegroundColor Red; exit 6
}

# ---------------------------------------------------------------------
# Per-target build runner
# ---------------------------------------------------------------------
function Invoke-OneTarget {
  param(
    [Parameter(Mandatory=$true)] $Target,
    [Parameter(Mandatory=$true)] [string]$Builder,
    [bool]$Clean, [bool]$NoBibtex, [bool]$Quiet
  )
  $start = Get-Date
  $stem  = $Target.Stem
  $dir   = $Target.Dir
  $stemPath = Join-Path $dir $stem
  # NOTE: $args is a PowerShell automatic variable inside functions; use a
  # different name. Also, we splat via a HASHTABLE (not an array) so that
  # switches like -Clean are bound as named parameters, not as positional
  # literals (which fails with "Cannot find positional parameter that
  # accepts '-Clean'").
  $builderArgs = @{ PaperStem = $stemPath }
  if ($Clean)    { $builderArgs.Clean    = $true }
  if ($NoBibtex) { $builderArgs.NoBibtex = $true }
  if ($Quiet)    { $builderArgs.Quiet    = $true }
  try {
    & $Builder @builderArgs
    $exitCode = $LASTEXITCODE
  } catch {
    $exitCode = 99
    Write-Host "[EXCEPTION] $($Target.Category)/$stem :: $($_.Exception.Message)" -ForegroundColor Red
  }
  $end = Get-Date
  $pdfPath = Join-Path $dir "$stem.pdf"
  $pdfSize = if (Test-Path -LiteralPath $pdfPath) { (Get-Item -LiteralPath $pdfPath).Length } else { 0 }
  return [pscustomobject]@{
    Category   = $Target.Category
    Stem       = $stem
    Dir        = $dir
    ExitCode   = $exitCode
    Status     = switch ($exitCode) { 0 {'OK'} default {'FAIL'} }
    PdfBytes   = $pdfSize
    DurationMs = [int]($end - $start).TotalMilliseconds
    StartedAt  = $start.ToString('o')
  }
}

# ---------------------------------------------------------------------
# Execute (sequential or parallel)
# ---------------------------------------------------------------------
$results = @()
$grandStart = Get-Date

if ($Parallel -ge 2 -and $PSVersionTable.PSVersion.Major -ge 7) {
  Write-Host "[TECT-build-all] running with -Parallel $Parallel (ForEach-Object -Parallel)" -ForegroundColor Cyan
  $bldr   = $builder
  $cln    = $Clean.IsPresent
  $noBib  = $NoBibtex.IsPresent
  $qt     = $Quiet.IsPresent
  $results = $targets | ForEach-Object -Parallel {
    $t = $_
    $start = Get-Date
    $stemPath = Join-Path $t.Dir $t.Stem
    # Hashtable splat → named parameters (switches bind correctly).
    $argsLocal = @{ PaperStem = $stemPath }
    if ($using:cln)   { $argsLocal.Clean    = $true }
    if ($using:noBib) { $argsLocal.NoBibtex = $true }
    if ($using:qt)    { $argsLocal.Quiet    = $true }
    try {
      & $using:bldr @argsLocal | Out-Null
      $rc = $LASTEXITCODE
    } catch {
      $rc = 99
      Write-Host "[EXCEPTION] $($t.Category)/$($t.Stem) :: $($_.Exception.Message)" -ForegroundColor Red
    }
    $end = Get-Date
    $pdfPath = Join-Path $t.Dir "$($t.Stem).pdf"
    $sz = if (Test-Path -LiteralPath $pdfPath) { (Get-Item -LiteralPath $pdfPath).Length } else { 0 }
    [pscustomobject]@{
      Category=$t.Category; Stem=$t.Stem; Dir=$t.Dir; ExitCode=$rc
      Status= if ($rc -eq 0) {'OK'} else {'FAIL'}
      PdfBytes=$sz; DurationMs=[int]($end-$start).TotalMilliseconds
      StartedAt=$start.ToString('o')
    }
  } -ThrottleLimit $Parallel
} else {
  if ($Parallel -ge 2) {
    Write-Host "[INFO] -Parallel $Parallel ignored (requires PowerShell 7+)" -ForegroundColor Yellow
  }
  $i = 0
  foreach ($t in $targets) {
    $i++
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "[$i/$($targets.Count)] $($t.Category) :: $($t.Stem)" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    $results += Invoke-OneTarget -Target $t -Builder $builder `
                  -Clean:$Clean -NoBibtex:$NoBibtex -Quiet:$Quiet
  }
}

$grandEnd = Get-Date
$elapsedSec = [math]::Round(($grandEnd - $grandStart).TotalSeconds, 1)

# ---------------------------------------------------------------------
# Summary table + JSON log
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Summary  ($elapsedSec s elapsed)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
$results | Sort-Object Category, Stem |
  Format-Table @{Name='Category';Expression={$_.Category}}, `
               @{Name='Stem';Expression={$_.Stem}}, `
               @{Name='Status';Expression={$_.Status};Width=6}, `
               @{Name='Exit';Expression={$_.ExitCode};Width=4}, `
               @{Name='PDF KB';Expression={[math]::Round($_.PdfBytes/1024,1)}}, `
               @{Name='ms';Expression={$_.DurationMs}} `
               -AutoSize

$nOK   = ($results | Where-Object { $_.Status -eq 'OK' }   ).Count
$nFAIL = ($results | Where-Object { $_.Status -eq 'FAIL' } ).Count
Write-Host ""
Write-Host ("[Total] OK={0}  FAIL={1}  ({2} files)" -f $nOK, $nFAIL, $results.Count) `
  -ForegroundColor $(if ($nFAIL -eq 0) {'Green'} else {'Yellow'})

# Group by category
Write-Host ""
$results | Group-Object Category | Sort-Object Name | ForEach-Object {
  $catOK   = ($_.Group | Where-Object { $_.Status -eq 'OK' }).Count
  $catFAIL = ($_.Group | Where-Object { $_.Status -eq 'FAIL' }).Count
  Write-Host ("  [{0,-12}] OK={1,2}  FAIL={2,2}  total={3,2}" -f $_.Name, $catOK, $catFAIL, $_.Count)
}

# Failed targets (verbose pointer)
if ($nFAIL -gt 0) {
  Write-Host ""
  Write-Host "[FAILED targets — see *.build.log for details]" -ForegroundColor Red
  $results | Where-Object { $_.Status -eq 'FAIL' } | ForEach-Object {
    Write-Host "  $($_.Category)  $($_.Stem)  exit=$($_.ExitCode)  log=$(Join-Path $_.Dir ($_.Stem + '.build.log'))" -ForegroundColor Red
  }
}

# JSON log
if (-not $LogDir) { $LogDir = Join-Path $repoRoot 'Runs\build_logs' }
if (-not (Test-Path -LiteralPath $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$ts = (Get-Date -Format 'yyyyMMdd-HHmmss')
$jsonPath = Join-Path $LogDir "build-$ts.json"
$payload = [pscustomobject]@{
  schema      = 'tect-build-all-papers-v2.0'
  timestamp   = $grandStart.ToString('o')
  finished    = $grandEnd.ToString('o')
  elapsed_sec = $elapsedSec
  filter      = $Filter
  categories  = $Categories
  clean       = $Clean.IsPresent
  no_bibtex   = $NoBibtex.IsPresent
  parallel    = $Parallel
  total       = $results.Count
  ok          = $nOK
  fail        = $nFAIL
  results     = $results
}
$payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonPath -Encoding utf8
Write-Host ""
Write-Host "[log] $jsonPath" -ForegroundColor DarkGray

if ($nFAIL -eq 0) { exit 0 } else { exit 1 }
