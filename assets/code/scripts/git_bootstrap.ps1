# ==============================================================================
# TECT Local Git Bootstrap — Windows/PowerShell
# ==============================================================================
# Trigger : User request 2026-04-21 to track code retirement + changes locally.
#           Sandbox agent cannot initialize git on the Windows OneDrive mount
#           due to ACL lock on .git/config.lock.
# Evidence: Sandbox error "fatal: bad config line 1; unable to unlink
#           .git/config.lock: Operation not permitted".
# Decision: Run git init + initial commit locally where ACLs cooperate.
#           This script is one-shot; after it completes the repo is ready
#           for the ongoing commit workflow (scripts/commit_v25_*.ps1).
# Policy reference: /Contents/docs/policy/UPDATE_POLICY.md §14 (git discipline)
# ==============================================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot\..

Write-Host "============================================================"
Write-Host " TECT Repository Git Bootstrap"
Write-Host "============================================================"

# --- Stage 0 :: Clean broken .git if present -----------------------------------
if (Test-Path .git) {
    $configPath = ".git\config"
    $looksBroken = $false
    if (Test-Path .git\config.lock) { $looksBroken = $true }
    if ((Test-Path $configPath) -and ((Get-Item $configPath).Length -lt 10)) { $looksBroken = $true }

    if ($looksBroken) {
        Write-Warning "Detected broken .git state — removing and re-initialising."
        Remove-Item -Recurse -Force .git
    } else {
        Write-Host "Existing .git looks valid. Skipping init."
    }
}

# --- Stage 1 :: git init --------------------------------------------------------
if (-not (Test-Path .git)) {
    Write-Host "`n[1/5] git init -b main"
    git init -b main | Out-Null
    git config user.name "저스틴 (TECT)"
    git config user.email "jtkor@outlook.com"
    git config core.autocrlf true
    git config core.longpaths true
}

# --- Stage 2 :: .gitignore ------------------------------------------------------
Write-Host "`n[2/5] Writing .gitignore (if not already versioned)..."
$gitignore = @"
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
venv/
env/
.ipynb_checkpoints/

# Large numerical artifacts (kept out of git — tracked via runs/*/MANIFEST.md)
*.npy
*.npz
*.pt
*.pth
*.h5
*.hdf5
runs/*/*.log
runs/*/*.dat
!runs/*/MANIFEST.md
!runs/*/README.md
!runs/*/*.json

# Editor / OS
.vscode/
.idea/
*.swp
*~
.DS_Store
Thumbs.db

# Session/sandbox artifacts (should never reach the Windows-side repo)
/sessions/

# Build/cache directories
build/
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/

# Website build outputs
website/dist/

# Preserve PDE/deprecated/ content
!PDE/deprecated/
!PDE/deprecated/**
"@
Set-Content -Path .gitignore -Value $gitignore -Encoding UTF8

# --- Stage 3 :: Initial commit of current state --------------------------------
Write-Host "`n[3/5] Staging all repository content..."
git add -A

$staged = git diff --cached --name-only | Measure-Object -Line
Write-Host "    Staged: $($staged.Lines) files"

Write-Host "`n[4/5] Creating initial commit..."
git commit -m @"
Initial commit: TECT archive baseline (2026-04-22)

Trigger : Local git tracking requested by the user — previously no VCS was
          in place for the TECT archive; code retirement and theory revisions
          could not be audited without bidirectional git history.
Evidence: User instruction 2026-04-21 (feedback_tect_git_retirement.md).
Decision: Initialise a local-only repo on the user's Windows machine. Sandbox
          agent cannot write to .git due to OneDrive ACLs; bootstrap delegated
          to this script.
Retires : none (baseline)
Math note: N/A (meta / infrastructure)

Contents baseline includes:
- Theory: docs/math/TECT-Math01..63 + 4 supplementary notes
- Code:   PDE/*.py, tools/*.py (v2.4 + v2.5 spec)
- Docs:   docs/manual, docs/papers, docs/policy, docs/status, docs/supplementary
- Runs:   runs/R-2026-04-21-002 (v2.4 failure), R-2026-04-22-001 (pending)
- Website: website/data/*.js + website/math/*.html (rev 2 publish-ready)
"@

# --- Stage 5 :: Annotated tags for key milestones ------------------------------
Write-Host "`n[5/5] Creating annotated milestone tags..."
git tag -a v0.0-baseline -m "TECT archive baseline snapshot — 2026-04-22 (pre-v2.5 diagnostic)"
git tag -a math63-spec-sealed -m "Math63 v2.5 solver redesign specification sealed"
git tag -a math61-s2e-sealed -m "Math61 S_2-E falsifiability pre-registration sealed"
git tag -a website-rev2 -m "Website nav rev 2 (Code<->Results swap + Math notes->Notes)"

Write-Host "`n============================================================"
Write-Host " Git bootstrap COMPLETE."
Write-Host "============================================================"
git log --oneline --decorate | Select-Object -First 5
Write-Host "`nNext: run .\scripts\run_v25_diagnostic.ps1 to execute the v2.5 sweep."
Write-Host "      After success: .\scripts\commit_v25_diagnostic.ps1 will stamp the result."
