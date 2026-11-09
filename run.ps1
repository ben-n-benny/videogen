<#
.SYNOPSIS
    VideoGen One-Click PowerShell Runner (9:16 1080p Short Video Builder)
.EXAMPLE
    .\run.ps1
    .\run.ps1 projects\project_azorian\project.json
    .\run.ps1 init projects\my_new_short --theme commentary
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPy = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$PyExe = if (Test-Path $VenvPy) { $VenvPy } else { "python" }

if (-not $ArgsList -or $ArgsList.Count -eq 0) {
    & $PyExe "$ScriptDir\videogen.py" build "$ScriptDir\projects\project_azorian\project.json"
} else {
    & $PyExe "$ScriptDir\videogen.py" @ArgsList
}
