
taskkill /f /im mayabatch.exe
taskkill /f /im deadlinelauncher.exe
start /wait "" C:\Users\illogic\Desktop\DeadlineClient-10.1.21.4-windows-installer.exe --mode unattended --connectiontype Direct --repositorydir "R:\deadline" --dbsslcertificate "R:\deadline\Deadline10Client.pfx"
echo Installer has finished.
echo Starting Deadline Worker...
start "" "C:\Program Files\Thinkbox\Deadline10\bin\deadlinelauncher.exe"
start "" "C:\Program Files\Thinkbox\Deadline10\bin\deadlineworker.exe"