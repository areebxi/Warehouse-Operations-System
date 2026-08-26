param(

  [string]$CsvPath = "",

  [string]$OutputDir = "",

  [string]$ColourImageColumn = "colour image 01",

  [string]$BrandColumn = "Brand",

  [string]$DescriptionColumn = "Description",

  [string]$ColourNameColumn = "Colour Name",

  [int]$MaxFileNameLength = 190,

  [int]$MaxRows = 0

)



$scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }

if ([string]::IsNullOrWhiteSpace($CsvPath)) {

  $CsvPath = Join-Path $scriptRoot "ProductExport.csv"

} elseif (-not [IO.Path]::IsPathRooted($CsvPath)) {

  $CsvPath = Join-Path $scriptRoot $CsvPath

}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {

  $OutputDir = Join-Path $scriptRoot "Apparel Images"

} elseif (-not [IO.Path]::IsPathRooted($OutputDir)) {

  $OutputDir = Join-Path $scriptRoot $OutputDir

}



$ErrorActionPreference = "Stop"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12



function Sanitize-FileName([string]$name) {

  if ($null -eq $name) { $name = "" }

  $name = $name.Trim()

  if ([string]::IsNullOrWhiteSpace($name)) { return "blank" }



  # Drop parenthetical / bracketed segments, e.g. "Sport Grey (RS)" -> "Sport Grey"

  do {

    $prev = $name

    $name = $name -replace '\([^()]*\)', ''

    $name = $name -replace '\[[^\]]*\]', ''

    $name = $name -replace '\{[^\}]*\}', ''

  } while ($name -ne $prev)



  $name = $name.Trim()

  # Keep only a-z, A-Z, 0-9 and spaces

  $name = $name -replace '[^A-Za-z0-9 ]', ''

  $name = ($name -replace '\s+', ' ').Trim()

  if ([string]::IsNullOrWhiteSpace($name)) { return "blank" }



  $name = $name -replace '\s+', '-'

  $name = $name -replace '-{2,}', '-'

  $name = $name.Trim('-')



  if ($name.Length -gt $MaxFileNameLength) {

    $name = $name.Substring(0, $MaxFileNameLength)

    $name = $name.TrimEnd('-')

  }

  return $name

}



function Get-UrlExtension([string]$url) {

  if ([string]::IsNullOrWhiteSpace($url)) { return ".jpg" }

  try {

    $u = [Uri]$url

    $ext = [IO.Path]::GetExtension($u.AbsolutePath)

    if (-not [string]::IsNullOrWhiteSpace($ext)) { return $ext }

  } catch { }

  return ".jpg"

}



function Get-UrlDedupeKey([string]$url) {

  if ([string]::IsNullOrWhiteSpace($url)) { return "" }

  $t = $url.Trim()

  try {

    $u = [Uri]$t

    $abs = $u.AbsoluteUri.TrimEnd('/')

    return $abs.ToLowerInvariant()

  } catch {

    return $t.ToLowerInvariant()

  }

}



if (-not (Test-Path -Path $CsvPath)) {

  throw "CSV not found: $CsvPath"

}



if (-not (Test-Path -Path $OutputDir)) {

  New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

}



$resolvedCsv = (Resolve-Path -Path $CsvPath).Path

$rows = Import-Csv -Path $resolvedCsv

$total = if ($rows) { $rows.Count } else { 0 }



$seenUrls = @{}

$failed = New-Object System.Collections.Generic.List[string]



$i = 0

foreach ($row in $rows) {

  $i++

  if ($MaxRows -gt 0 -and $i -gt $MaxRows) { break }



  $url = $row.$ColourImageColumn

  if ([string]::IsNullOrWhiteSpace($url)) { continue }

  $url = $url.Trim()



  $urlKey = Get-UrlDedupeKey $url

  # Same link again (exact or after normalize: trim, trailing slash, casing) — skip; keep first row only

  if ($seenUrls.ContainsKey($urlKey)) { continue }

  $seenUrls[$urlKey] = $true



  $brand = $row.$BrandColumn

  $desc = $row.$DescriptionColumn

  $colourName = $row.$ColourNameColumn



  $safeBrand = Sanitize-FileName $brand

  $safeDesc = Sanitize-FileName $desc

  $safeColour = Sanitize-FileName $colourName



  $baseName = "$safeBrand-$safeDesc-$safeColour"

  $ext = Get-UrlExtension $url



  $outPath = Join-Path $OutputDir "$baseName$ext"



  try {

    Write-Host "[$i/$total] Downloading $baseName$ext"

    # If multiple rows generate the same filename, replace it.

    if (Test-Path -Path $outPath) {

      Remove-Item -Path $outPath -Force

    }

    Invoke-WebRequest -Uri $url -OutFile $outPath -TimeoutSec 120

  } catch {

    $msg = "[$i/$total] FAIL $url :: $($_.Exception.Message)"

    $failed.Add($msg)

    Write-Warning $msg

  }

}



if ($failed.Count -gt 0) {

  $failPath = Join-Path $OutputDir "download-failures-colour-image-01.txt"

  $failed | Set-Content -Path $failPath -Encoding UTF8

  Write-Host "Done with failures. See: $failPath"

} else {

  Write-Host "Done. Images saved to: $OutputDir"

}


