# =====================================================================
# TECT canonical paper build script (PowerShell, v2.0)
# =====================================================================
# Usage:
#   .\_shared\build-paper.ps1 <PaperStem>
#   .\_shared\build-paper.ps1 <PaperStem> -Clean
#   .\_shared\build-paper.ps1 <PaperStem> -NoBibtex -Quiet
#
# <PaperStem> is the path WITHOUT the .tex extension, e.g.
#   Paper-03-Pillar3-Emergent-Gravity\Paper-03
#
# Smart pass-counting:
#   pass 1 : pdflatex generates .aux with all \label entries.
#   bibtex : run only if (a) source contains \bibliography{...} AND
#            (b) the .bbl is missing or older than the .tex source.
#   pass 2 : pdflatex resolves \ref / \cref forward references.
#   pass 3 : run only if pass-2 .log still reports undefined references
#            (typical for cleveref + bibliography 3-pass cycles).
#
# Exit codes:
#   0   build succeeded, PDF produced.
#   1   pdflatex failed on pass 1.
#   2   bibtex failed.
#   3   pdflatex failed on pass 2.
#   4   pdflatex failed on pass 3 (auto-triggered).
#   5   no PDF produced despite no error.
# =====================================================================
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true, Position=0)]
  [string]$PaperStem,

  [switch]$Clean,                # remove aux/bbl/blg/toc/log/out before build
  [switch]$NoBibtex,             # skip bibtex pass (use stale .bbl if any)
  [switch]$Quiet,                # suppress per-pass stdout (still capture to .build.log)
  [int]$MaxRefPasses = 3         # cap on extra pdflatex passes for ref resolution
)

$ErrorActionPreference = 'Stop'

$base = Split-Path -Leaf  $PaperStem
$dir  = Split-Path -Parent $PaperStem
if ([string]::IsNullOrEmpty($dir)) { $dir = '.' }

if (-not (Test-Path -LiteralPath $dir -PathType Container)) {
  Write-Host "[TECT-build] ERROR: directory not found: $dir" -ForegroundColor Red
  exit 5
}

Push-Location -LiteralPath $dir
$src = "$base.tex"
if (-not (Test-Path -LiteralPath $src -PathType Leaf)) {
  Write-Host "[TECT-build] ERROR: source not found: $dir\$src" -ForegroundColor Red
  Pop-Location
  exit 5
}

# ---------------------------------------------------------------------
# Logging utilities
# ---------------------------------------------------------------------
$buildLog = "$base.build.log"
"# TECT build log for $base ($(Get-Date -Format o))" | Set-Content -LiteralPath $buildLog -Encoding utf8

function Write-Phase([string]$msg, [string]$color = 'Cyan') {
  if (-not $Quiet) { Write-Host "[TECT-build] $msg" -ForegroundColor $color }
  "[TECT-build] $msg" | Add-Content -LiteralPath $buildLog -Encoding utf8
}

function Invoke-LatexCommand([string]$cmd, [string[]]$cmdArgs) {
  # Stream output to both console (if not Quiet) and build log; return exit code.
  # Defensive: Start-Process can throw under quotacheck / antivirus interference;
  # catch and report as exit code 250 so the parent script can record FAIL with
  # diagnostic context rather than crashing.
  $tmp = New-TemporaryFile
  try {
    try {
      $proc = Start-Process -FilePath $cmd -ArgumentList $cmdArgs `
        -NoNewWindow -PassThru -RedirectStandardOutput $tmp.FullName `
        -Wait -ErrorAction Continue
    } catch {
      "[TECT-build] EXCEPTION launching '$cmd': $($_.Exception.Message)" |
        Add-Content -LiteralPath $buildLog -Encoding utf8
      Write-Host "[TECT-build] EXCEPTION launching '$cmd': $($_.Exception.Message)" -ForegroundColor Red
      return 250
    }
    $output = Get-Content -LiteralPath $tmp.FullName -Raw -ErrorAction SilentlyContinue
    if ($null -ne $output) {
      $output | Add-Content -LiteralPath $buildLog -Encoding utf8
      if (-not $Quiet) {
        # Show only the most informative trailing lines for streaming UX
        $tailLines = ($output -split "`r?`n") | Select-Object -Last 8
        $tailLines | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
      }
    }
    return $proc.ExitCode
  } finally {
    Remove-Item -LiteralPath $tmp.FullName -ErrorAction SilentlyContinue
  }
}

function Get-UndefinedRefCount([string]$logPath) {
  if (-not (Test-Path -LiteralPath $logPath)) { return 0 }
  # pdflatex emits "LaTeX Warning: There were undefined references." OR
  # individual "LaTeX Warning: Reference `xxx' on page Y undefined ..."
  $cnt = 0
  Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_ -match 'Reference `[^'']+'' on page \d+ undefined' -or
        $_ -match 'Citation `[^'']+'' on page \d+ undefined'  -or
        $_ -match 'There were undefined references') {
      $script:cnt++
    }
  }
  return $cnt
}

try {
  # -------------------------------------------------------------------
  # 0. Optional clean
  # -------------------------------------------------------------------
  if ($Clean) {
    Write-Phase "clean: removing aux/bbl/blg/toc/log/out for $base" 'Yellow'
    $exts = @('aux','bbl','blg','toc','log','out','run.xml','synctex.gz','fls','fdb_latexmk')
    foreach ($e in $exts) {
      $f = "$base.$e"
      if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -ErrorAction SilentlyContinue }
    }
  }

  # -------------------------------------------------------------------
  # 1. pdflatex pass 1
  # -------------------------------------------------------------------
  Write-Phase "pass 1: pdflatex $base"
  $rc = Invoke-LatexCommand 'pdflatex' @('-interaction=nonstopmode','-halt-on-error',$src)
  if ($rc -ne 0) {
    Write-Phase "ERROR: pdflatex pass 1 failed (exit $rc); see $buildLog" 'Red'
    Pop-Location; exit 1
  }

  # -------------------------------------------------------------------
  # 2. bibtex (conditional)
  # -------------------------------------------------------------------
  $needBibtex = $false
  if (-not $NoBibtex) {
    $hasBibCmd  = Select-String -Path $src -Pattern '\\bibliography\{' -Quiet
    # Skip bibtex if the source contains no \cite{} commands at all.
    # bibtex would emit "I found no \citation commands" + exit 1, which is
    # spurious noise for a paper that uses \bibliography{} only to render
    # an empty (or unused) reference list.
    $hasCites   = Select-String -Path $src -Pattern '\\cite[a-z]*\{' -Quiet
    if ($hasBibCmd -and $hasCites) {
      $bblPath = "$base.bbl"
      try {
        if (-not (Test-Path -LiteralPath $bblPath)) {
          $needBibtex = $true
        } else {
          $bblTime = (Get-Item -LiteralPath $bblPath -ErrorAction Stop).LastWriteTime
          $srcTime = (Get-Item -LiteralPath $src     -ErrorAction Stop).LastWriteTime
          $needBibtex = ($bblTime -lt $srcTime)
        }
      } catch {
        # If file-time inspection itself fails, default to running bibtex.
        $needBibtex = $true
      }
    } elseif ($hasBibCmd -and -not $hasCites) {
      Write-Phase "bibtex: SKIP (source has \bibliography{} but zero \cite{} — bibtex would error spuriously)" 'DarkGray'
    }
  }
  if ($needBibtex) {
    Write-Phase "bibtex $base"
    $rc = Invoke-LatexCommand 'bibtex' @($base)
    if ($rc -ne 0) {
      Write-Phase "WARN: bibtex returned $rc (continuing — may be missing optional bib entries)" 'Yellow'
      # bibtex returns non-zero on missing entries but we continue;
      # only treat as fatal if pdflatex pass 2 also fails.
    }
  } else {
    Write-Phase "bibtex: SKIP (no \bibliography{} OR .bbl up-to-date OR -NoBibtex)" 'DarkGray'
  }

  # -------------------------------------------------------------------
  # 3. pdflatex pass 2 + auto-extra-passes
  # -------------------------------------------------------------------
  Write-Phase "pass 2: pdflatex $base"
  $rc = Invoke-LatexCommand 'pdflatex' @('-interaction=nonstopmode','-halt-on-error',$src)
  if ($rc -ne 0) {
    Write-Phase "ERROR: pdflatex pass 2 failed (exit $rc); see $buildLog" 'Red'
    Pop-Location; exit 3
  }

  # Extra passes if undefined-ref count > 0 (e.g. cleveref + bibliography 3-pass)
  $extraPass = 0
  while ($extraPass -lt ($MaxRefPasses - 1)) {
    $undef = Get-UndefinedRefCount "$base.log"
    if ($undef -le 0) { break }
    $extraPass += 1
    Write-Phase ("pass " + ($extraPass + 2) + ": pdflatex $base (still " + $undef + " undefined refs)")
    $rc = Invoke-LatexCommand 'pdflatex' @('-interaction=nonstopmode','-halt-on-error',$src)
    if ($rc -ne 0) {
      Write-Phase "ERROR: pdflatex extra pass failed (exit $rc); see $buildLog" 'Red'
      Pop-Location; exit 4
    }
  }

  # -------------------------------------------------------------------
  # 4. PDF presence check
  # -------------------------------------------------------------------
  $pdf = "$base.pdf"
  if (-not (Test-Path -LiteralPath $pdf -PathType Leaf)) {
    Write-Phase "ERROR: no PDF produced for $base" 'Red'
    Pop-Location; exit 5
  }

  $pdfSize = (Get-Item -LiteralPath $pdf).Length
  $pdfPages = '?'  # extracting page count cleanly requires pdfinfo; report size only
  Write-Phase ("OK: $dir\$pdf  (size = " + [math]::Round($pdfSize/1024, 1) + " KB)") 'Green'

  # Final undef-ref report
  $remainingUndef = Get-UndefinedRefCount "$base.log"
  if ($remainingUndef -gt 0) {
    Write-Phase "WARN: $remainingUndef undefined-reference warnings remain after $($extraPass + 2) passes" 'Yellow'
  }

  Pop-Location
  exit 0

} catch {
  Write-Host "[TECT-build] EXCEPTION: $($_.Exception.Message)" -ForegroundColor Red
  Pop-Location
  exit 5
}
