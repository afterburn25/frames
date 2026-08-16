param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$IsoPath
)

$ErrorActionPreference = 'Stop'
$ExpectedSha256 = 'abeead78504b6562ee6ecef47027c95803594dd21527cfc3120205a5ef9b7068'
$ExpectedSize = 67160064

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

Write-Host 'Certified ISO identity PASS. Physical boot validation may proceed within the documented safety boundary.'
