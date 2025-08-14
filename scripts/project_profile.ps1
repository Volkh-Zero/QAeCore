# Project-local PowerShell profile for QAeCore
# Loaded only via VS Code terminal profile args (not global)

function Get-WorkspaceRoot {
    param([string]$Marker = '.git')
    $currentPath = $pwd.Path
    $rootPath = $currentPath
    while ($rootPath -and -not (Test-Path (Join-Path $rootPath $Marker))) {
        $parentPath = Split-Path $rootPath -Parent
        if ($parentPath -eq $rootPath) {
            # Reached the root of the drive without finding the marker
            return $null
        }
        $rootPath = $parentPath
    }
    return $rootPath
}

function Use-QAeCoreDev {
    if (Get-Command deactivate -ErrorAction SilentlyContinue) { deactivate }
    $root = Get-WorkspaceRoot
    if (-not $root) {
        Write-Host "Workspace root (.git) not found." -ForegroundColor Red
        return
    }
    $script = Join-Path $root 'QAeonCoreDevelopment/.venv/Scripts/Activate.ps1'
    if (Test-Path $script) { . $script; $env:QAEC_ACTIVE_ENV='QAeCoreDev'; Write-Host '[env] QAeCoreDev active' -ForegroundColor Green } else { Write-Host "Missing venv: $script" -Foreground Yellow }
}

function Use-DocsMCP {
    if (Get-Command deactivate -ErrorAction SilentlyContinue) { deactivate }
    $root = Get-WorkspaceRoot
    if (-not $root) {
        Write-Host "Workspace root (.git) not found." -ForegroundColor Red
        return
    }
    $script = Join-Path $root 'Global-docs-mcp-python/.venv/Scripts/Activate.ps1'
    if (Test-Path $script) { . $script; $env:QAEC_ACTIVE_ENV='DocsMCP'; Write-Host '[env] DocsMCP active' -ForegroundColor Green } else { Write-Host "Missing venv: $script" -Foreground Yellow }
}

Set-Alias qdev Use-QAeCoreDev
Set-Alias qdocs Use-DocsMCP

function Show-EnvStatus {
    Write-Host "VIRTUAL_ENV : $($env:VIRTUAL_ENV)" -ForegroundColor Cyan
    Write-Host "QAEC_ACTIVE_ENV : $($env:QAEC_ACTIVE_ENV)" -ForegroundColor Cyan
    $code = @'
import sys, sysconfig
print("Python:", sys.executable)
print("Base Prefix:", sys.base_prefix)
print("Prefix:", sys.prefix)
print("Is Virtual:", sys.prefix != sys.base_prefix)
print("Site-packages:", sysconfig.get_paths().get("purelib"))
'@
    python -c $code
}
Set-Alias envstat Show-EnvStatus

# Convenience: auto-load last used env marker if present (future enhancement)