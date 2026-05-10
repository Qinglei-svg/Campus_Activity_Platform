$ErrorActionPreference = "Stop"

$Workspace = (Resolve-Path ".").Path

function Remove-WorkspaceItem($RelativePath) {
    $Target = Join-Path $Workspace $RelativePath
    $ResolvedParent = (Resolve-Path (Split-Path $Target -Parent)).Path
    if (-not $Target.StartsWith($Workspace)) {
        throw "Refusing to remove path outside workspace: $Target"
    }
    if ($ResolvedParent -ne $Workspace) {
        throw "Refusing to remove nested or unexpected path: $Target"
    }
    Remove-Item -LiteralPath $Target -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Cleaning previous build output..."
Remove-WorkspaceItem "build"
Remove-WorkspaceItem "dist"

Write-Host "Building desktop executable with PyInstaller..."
python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "CampusActivityPlatform" `
    --add-data "ui/styles/style.qss;ui/styles" `
    "main.py"

Write-Host "Build completed."
Write-Host "Executable path: dist/CampusActivityPlatform/CampusActivityPlatform.exe"
