

set TASK_NAME=SYNC_RANCH_CACHE
set SCRIPT_PATH="C:\Users\sysadmin\Desktop\ranch.ffs_batch"
set TASK_TRIGGER=/sc MINUTE /mo 5 /st 00:00
set TASK_ACTION=/tr %SCRIPT_PATH%

schtasks /Create /tn %TASK_NAME% %TASK_TRIGGER% %TASK_ACTION% /f /rl HIGHEST

