# GloryDay

## Releasing a new version

Build with PyInstaller first:
```
C:\Users\Thomas\AppData\Local\Programs\Python\Python312\Scripts\pyinstaller.exe main.spec
```

Copy assets into dist (PyInstaller does NOT do this automatically):
```powershell
Remove-Item -Path "dist\asset" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "dist\asset" | Out-Null
Get-ChildItem "asset" | Copy-Item -Destination "dist\asset" -Recurse -Force
```

Zip the dist folder:
```powershell
Compress-Archive -Path "dist\main.exe", "dist\asset" -DestinationPath "GloryDay_v1.2.zip" -Force
```

Create GitHub release:
```
gh release create v1.2 "GloryDay_v1.2.zip" --repo zzthomaszzz/Glory_days_beta --title "GloryDay Beta v1.2" --notes "..."
```

Releases: https://github.com/zzthomaszzz/Glory_days_beta/releases
