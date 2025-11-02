@echo off
title Windows Update Toggle - Menu
:: tenta elevar se não for admin
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Solicitando permissao de administrador...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '' -Verb RunAs"
  exit /b
)

:menu
cls
echo ================================
echo  Windows Update - Menu
echo ================================
echo 1) Desabilitar atualizacoes (parar e bloquear)
echo 2) Habilitar atualizacoes (restaurar)
echo 3) Sair
echo.
set /p choice="Escolha [1-3]: "

if "%choice%"=="1" goto disable
if "%choice%"=="2" goto enable
if "%choice%"=="3" goto end
echo Opcao invalida.
pause
goto menu

:disable
echo Parando servicos relacionados ao Windows Update...
sc stop wuauserv >nul 2>&1
sc stop bits >nul 2>&1
sc stop dosvc >nul 2>&1
sc stop WaaSMedicSvc >nul 2>&1

echo Definindo serviços como Disabled...
sc config wuauserv start= disabled >nul
sc config bits start= disabled >nul
sc config dosvc start= disabled >nul
sc config WaaSMedicSvc start= disabled >nul

echo Aplicando politicas de registro para bloquear atualizacoes automaticas...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v AUOptions /t REG_DWORD /d 1 /f >nul

echo Fallback: definindo Start=4 nas chaves de servico...
reg add "HKLM\SYSTEM\CurrentControlSet\Services\wuauserv" /v Start /t REG_DWORD /d 4 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\bits" /v Start /t REG_DWORD /d 4 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\dosvc" /v Start /t REG_DWORD /d 4 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc" /v Start /t REG_DWORD /d 4 /f >nul

echo Concluido. Reinicie o sistema para garantir aplicacao completa.
pause
goto menu

:enable
echo Restaurando configuracoes de servico e politicas...
sc config wuauserv start= auto >nul
sc config bits start= delayed-auto >nul
sc config dosvc start= auto >nul
sc config WaaSMedicSvc start= demand >nul

sc start wuauserv >nul 2>&1
sc start bits >nul 2>&1
sc start dosvc >nul 2>&1

reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v AUOptions /f >nul 2>&1

reg add "HKLM\SYSTEM\CurrentControlSet\Services\wuauserv" /v Start /t REG_DWORD /d 2 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\bits" /v Start /t REG_DWORD /d 3 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\dosvc" /v Start /t REG_DWORD /d 2 /f >nul

echo Atualizacoes habilitadas. Reinicie o computador para garantir.
pause
goto menu

:end
exit /b
