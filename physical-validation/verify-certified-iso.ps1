param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$IsoPath
)

$ErrorActionPreference = 'Stop'
$ExpectedSha256 = '7d1c212ad71778a84579e91c2e12ebafe3801a8bcd8a0a0856e506d47ebe20c7'
$ExpectedSize = 67401728

$resolved = (Resolve-Path -LiteralPath $IsoPath).Path
$item = Get-Item -LiteralPath $resolved
$hash = (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant()

$result = [ordered]@{
    profile = 'frames-v116-physical-hardware-full-gui-preboot-identity'
    iso_path = $resolved
    iso_name = $item.Name
    size_bytes = $item.Length
    expected_size_bytes = $ExpectedSize
    sha256 = $hash
    expected_sha256 = $ExpectedSha256
    size_match = ($item.Length -eq $ExpectedSize)
    sha256_match = ($hash -eq $ExpectedSha256)
    status = if (($item.Length -eq $ExpectedSize) -and ($hash -eq $ExpectedSha256)) { 'PASS' } else { 'FAIL' }
    checked_utc = (Get-Date).ToUniversalTime().ToString('o')
}

$json = $result | ConvertTo-Json -Depth 4
$json
$json | Set-Content -LiteralPath 'PHYSICAL-PREBOOT-ISO-IDENTITY.json' -Encoding UTF8

if ($result.status -ne 'PASS') {
    Write-Error 'ISO identity mismatch. Do not use this file for the certified physical validation.'
    exit 1
}

Write-Host 'Certified USB-compatible full-GUI ISO identity PASS. Physical boot validation may proceed within the documented safety boundary.'
