@echo off
rem Creates a "SnapSolve" shortcut on your Desktop (with your logo). Double-click the shortcut to run.
rem It starts the app through Python (signed by Python), so Smart App Control does not block it.
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"
if exist ".venv\Scripts\python.exe" (".venv\Scripts\python.exe" tools\make_icon.py) else (python tools\make_icon.py)
powershell -NoProfile -Command "$root=$env:ROOT.TrimEnd('\'); $py=Join-Path $root '.venv\Scripts\pythonw.exe'; if(-not(Test-Path $py)){$c=Get-Command pythonw.exe -EA 0; if($c){$py=$c.Source}else{Write-Host 'pythonw.exe not found - run the setup steps first.'; exit 1}}; $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'SnapSolve.lnk')); $s.TargetPath=$py; $s.Arguments='-m app.main'; $s.WorkingDirectory=$root; $i=Join-Path $root 'assets\icon.ico'; if(Test-Path $i){$s.IconLocation=$i}; $s.Description='SnapSolve'; $s.Save(); Write-Host 'Done: SnapSolve shortcut created on your Desktop.'"
pause
