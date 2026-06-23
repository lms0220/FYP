@echo off
REM pm.cmd - forward package manager commands to the frontend package.json
SETLOCAL
SET PREFIX=frontend
npm --prefix %PREFIX% %*
ENDLOCAL
