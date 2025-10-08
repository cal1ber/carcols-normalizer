# Restore all carcols.meta.bak files beside the originals
Get-ChildItem -Recurse -Filter 'carcols.meta.bak' |
  ForEach-Object {
    Copy-Item $_.FullName ($_.FullName -replace '\.bak$','') -Force
    Write-Host "Restored $($_.DirectoryName)"
  }
