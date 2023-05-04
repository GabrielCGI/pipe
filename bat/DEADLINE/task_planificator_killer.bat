

set TASK_NAME=SANDBOX_KILLER_DEADLINE
set SCRIPT_PATH="R:\pipeline\pipe\bat\DEADLINE\sandbox_killer3.bat"
set TASK_TRIGGER=/sc MINUTE /mo 2 /st 00:00
set TASK_ACTION=/tr %SCRIPT_PATH%

schtasks /Create /tn %TASK_NAME% %TASK_TRIGGER% %TASK_ACTION% /f /rl HIGHEST

