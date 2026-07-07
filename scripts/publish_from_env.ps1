param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$Build,
    [switch]$DryRun,
    [string]$RepositoryUrl = ""
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf8"

function Read-DotEnvValue {
    param(
        [string]$Path,
        [string[]]$Keys
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw ".env file not found: $Path"
    }

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }

        $name, $value = $trimmed.Split("=", 2)
        $name = $name.Trim()
        $value = $value.Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        $values[$name] = $value
    }

    foreach ($key in $Keys) {
        if ($values.ContainsKey($key) -and $values[$key]) {
            return $values[$key]
        }
    }

    throw "No PyPI token found in .env. Expected one of: $($Keys -join ', ')"
}

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$envPath = Join-Path $root ".env"
$distPath = Join-Path $root "dist"
$token = Read-DotEnvValue -Path $envPath -Keys @("PYPI_API_TOKEN", "TWINE_PASSWORD", "password")

Push-Location $root
try {
    if ($Build) {
        python -m build
    }

    if (-not (Test-Path -LiteralPath $distPath)) {
        throw "dist directory not found: $distPath"
    }

    $artifacts = @(Get-ChildItem -LiteralPath $distPath -File | ForEach-Object { $_.FullName })
    if ($artifacts.Count -eq 0) {
        throw "No distribution artifacts found in: $distPath"
    }

    if ($DryRun) {
        Write-Host "Dry run OK: found token and $($artifacts.Count) artifact(s)."
        return
    }

    $args = @("-m", "twine", "upload", "--non-interactive", "--skip-existing", "-u", "__token__", "-p", $token)
    if ($RepositoryUrl) {
        $args += @("--repository-url", $RepositoryUrl)
    }
    $args += $artifacts

    & python @args
}
finally {
    Pop-Location
}
