param()
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$assetRoot = Join-Path $taskRoot 'assets\gnm'
$sourceRevision = 'f84cdbdc86a34f55627526f137495f864e687679'
$modelRevision = 'c01e90d298d82301f9fd18f54806be751775cb7c'
$modelHash = '61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb'
New-Item -ItemType Directory -Path $assetRoot -Force | Out-Null
$downloads = @()
function Save-Asset([string]$url, [string]$relative, [string]$expectedHash = '') {
    $destination = [IO.Path]::GetFullPath((Join-Path $assetRoot $relative))
    if (-not $destination.StartsWith($assetRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Destination must stay inside assets/gnm'
    }
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
    $cached = (Test-Path -LiteralPath $destination) -and $expectedHash -and ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ieq $expectedHash)
    if (-not $cached) {
        Write-Output ('Downloading ' + $relative)
        Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $destination -TimeoutSec 300
    }
    $hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($expectedHash -and $hash -ne $expectedHash) { throw ('Checksum mismatch: ' + $relative) }
    $script:downloads += [ordered]@{file=('assets/gnm/' + $relative.Replace('\','/')); source=$url; sha256=$hash; bytes=(Get-Item -LiteralPath $destination).Length}
}
$sourceBase = 'https://raw.githubusercontent.com/google/GNM/' + $sourceRevision + '/'
Save-Asset ($sourceBase + 'LICENSE') 'LICENSE.Apache-2.0.txt'
Save-Asset ($sourceBase + 'README.md') 'reference/UPSTREAM_README.md'
foreach ($file in @('gnm_xnp.py','gnm_common.py','gnm_base.py','gnm_data_schema.py','semantic_sampler.py')) {
    Save-Asset ($sourceBase + 'gnm/shape/' + $file) ('reference/' + $file)
}
Save-Asset ($sourceBase + 'gnm/shape/README.md') 'reference/SHAPE_README.md'
Save-Asset ($sourceBase + 'gnm/shape/data/textures/edgeflow_bw_4k.png') 'edgeflow_bw_4k.png'
foreach ($file in @('expression_decoder_model.h5','identity_decoder_model.h5')) {
    Save-Asset ($sourceBase + 'gnm/shape/data/semantic_sampler/' + $file) ('semantic/' + $file)
}
$modelBase = 'https://huggingface.co/google/gnm-v3/resolve/' + $modelRevision + '/'
Save-Asset ($modelBase + 'README.md') 'reference/MODEL_CARD.md'
Save-Asset ($modelBase + 'v3_0/checksums.sha256') 'reference/checksums.sha256'
Save-Asset ($modelBase + 'v3_0/gnm_head.npz') 'gnm_head.npz' $modelHash
$manifest = [ordered]@{
    model='Google GNM Head'; version='3.0'; license='Apache-2.0'; copyright='2026 Google LLC'
    acquired_on='2026-11-14'; source_revision=$sourceRevision; model_revision=$modelRevision
    official_repository='https://github.com/google/GNM'; official_model='https://huggingface.co/google/gnm-v3'
    downloads=$downloads
    modifications='Downloaded files are unmodified. Project exports and scene adaptations are documented separately.'
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $assetRoot 'download_manifest.json') -Encoding UTF8
Write-Output ('Verified GNM asset: ' + $modelHash)
