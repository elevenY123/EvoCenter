$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$repoPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$jobs = Get-Content -LiteralPath (Join-Path $repoPath 'site/preview-jobs.json') -Raw | ConvertFrom-Json
$jpegCodec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -EQ 'image/jpeg'
$jpegOptions = [System.Drawing.Imaging.EncoderParameters]::new(1)
$jpegOptions.Param[0] = [System.Drawing.Imaging.EncoderParameter]::new([System.Drawing.Imaging.Encoder]::Quality, [long]88)
$totalBytes = 0L
foreach ($job in $jobs) {
    $sourcePath = [IO.Path]::GetFullPath((Join-Path $repoPath $job.source))
    $outputPath = [IO.Path]::GetFullPath((Join-Path $repoPath $job.output))
    if (-not $sourcePath.StartsWith($repoPath + [IO.Path]::DirectorySeparatorChar) -or -not $outputPath.StartsWith($repoPath + [IO.Path]::DirectorySeparatorChar)) { throw 'Preview path must stay inside the repository' }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($outputPath)) | Out-Null
    $inputImage = [System.Drawing.Image]::FromFile($sourcePath)
    try {
        $targetWidth = [Math]::Min([int]$job.width, $inputImage.Width)
        $targetHeight = [int][Math]::Round($inputImage.Height * $targetWidth / $inputImage.Width)
        $pixelFormat = if ($job.format -eq 'png') { [System.Drawing.Imaging.PixelFormat]::Format32bppArgb } else { [System.Drawing.Imaging.PixelFormat]::Format24bppRgb }
        $bitmap = [System.Drawing.Bitmap]::new($targetWidth, $targetHeight, $pixelFormat)
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            try {
                $graphics.Clear($(if ($job.format -eq 'png') { [System.Drawing.Color]::Transparent } else { [System.Drawing.Color]::Black }))
                $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $graphics.DrawImage($inputImage, [System.Drawing.Rectangle]::new(0, 0, $targetWidth, $targetHeight))
            } finally { $graphics.Dispose() }
            if ($job.format -eq 'png') { $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png) }
            else { $bitmap.Save($outputPath, $jpegCodec, $jpegOptions) }
            $totalBytes += (Get-Item -LiteralPath $outputPath).Length
        } finally { $bitmap.Dispose() }
    } finally { $inputImage.Dispose() }
}
$jpegOptions.Dispose()
Write-Output "Exported $($jobs.Count) preview assets, $totalBytes bytes. Original screenshots are unchanged."
