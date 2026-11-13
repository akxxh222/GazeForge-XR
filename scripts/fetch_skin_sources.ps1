$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$downloadRoot = Join-Path $taskRoot 'work\downloads'
New-Item -ItemType Directory -Path $downloadRoot -Force | Out-Null
$url = 'https://files.makehumancommunity.org/asset_packs/skins02/skins02_cc0.zip'
$destination = Join-Path $downloadRoot 'skins02_cc0.zip'
$recordedHash = '1613f1ef3afca53094511d26620ed7cf1d2dedc29ed3d384d60bdebe250698ae'
if (-not (Test-Path -LiteralPath $destination) -or (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ine $recordedHash) {
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $destination -TimeoutSec 300
}
if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ine $recordedHash) { throw 'Skin pack differs from the recorded source version; inspect the upstream revision before using it.' }
$catalog = 'https://static.makehumancommunity.org/assets/assetpacks/skins02.html'
Invoke-WebRequest -UseBasicParsing -Uri $catalog -OutFile (Join-Path $downloadRoot 'skins02_catalog.html') -TimeoutSec 60
$record = [ordered]@{
    source=$url; catalog=$catalog; license='CC0-1.0'; acquired_on='2026-11-14'
    sha256=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    bytes=(Get-Item -LiteralPath $destination).Length
    hash_note='Locally recorded download hash; no upstream checksum was advertised on the catalog page.'
    role='Source maps for later baking. These MakeHuman UV maps are not GNM-ready deliverables.'
}
$record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $downloadRoot 'skins02_download.json') -Encoding UTF8
python (Join-Path $PSScriptRoot 'prepare_skin_sources.py')
if ($LASTEXITCODE -ne 0) { throw 'Skin source inspection failed' }
