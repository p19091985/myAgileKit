@echo off
title 🧹 Limpeza Completa do Python no Windows
echo ============================================
echo 🧹 Iniciando limpeza completa do Python...
echo ============================================

REM --- Checa permissões de administrador ---
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo ❌ Este script precisa ser executado como Administrador.
    echo Clique com o botao direito e escolha "Executar como administrador".
    pause
    exit /b
)

REM --- Desinstala todas as versões Python registradas ---
echo.
echo 🔍 Procurando instalacoes do Python registradas no sistema...
for /f "tokens=*" %%a in ('wmic product where "Name like 'Python%%'" get IdentifyingNumber ^| find "{"') do (
    echo Desinstalando %%a ...
    msiexec /x %%a /qn
)

REM --- Remove pastas residuais ---
echo.
echo 🗑️ Removendo pastas residuais...

rmdir /s /q "C:\Users\user\AppData\Local\Programs\Python"
rmdir /s /q "C:\Users\user\AppData\Local\pip"
rmdir /s /q "C:\Users\user\AppData\Roaming\Python"
rmdir /s /q "C:\Users\user\AppData\Local\Temp"
for /d %%i in (C:\Python*) do (
    echo Removendo %%i
    rmdir /s /q "%%i"
)

REM --- Removendo ambientes virtuais (.venv, venv, env) ---
echo.
echo 🧰 Procurando e removendo ambientes virtuais (.venv, venv, env) em C:\Users\user ...
for /d /r "C:\Users\user" %%i in (.venv venv env) do (
    if exist "%%i" (
        echo Removendo ambiente virtual: %%i
        rmdir /s /q "%%i"
    )
)

REM --- Remove variáveis de ambiente ---
echo.
echo 🧭 Limpando variaveis de ambiente do Python...

for /f "tokens=1,* delims==" %%a in ('set') do (
    echo %%a | findstr /I "PYTHON" >nul
    if not errorlevel 1 (
        echo Removendo variavel de ambiente: %%a
        setx %%a ""
    )
)

REM --- Remove entradas no PATH contendo Python ---
for /f "tokens=2* delims==" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do (
    set "path_system=%%b"
)
setlocal enabledelayedexpansion
set "newpath=!path_system:Python=!"
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "!newpath!" /f >nul
endlocal

REM --- Limpa chaves de registro ---
echo.
echo 🧹 Limpando registro do Windows...
reg delete "HKCU\Software\Python" /f >nul 2>&1
reg delete "HKLM\Software\Python" /f >nul 2>&1
reg delete "HKLM\Software\Wow6432Node\Python" /f >nul 2>&1

echo.
echo ============================================
echo ✅ Limpeza total concluida com sucesso!
echo ============================================
pause
