# eleva se necessario
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) {
  Write-Host "Solicitando permissao de administrador..."
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "powershell.exe"
  $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
  $psi.Verb = "runas"
  try { [System.Diagnostics.Process]::Start($psi) | Out-Null } catch { Write-Error "Elevacao cancelada."; exit }
  exit
}

function Disable-Updates {
  Write-Host "Parando servicos..."
  $services = "wuauserv","bits","dosvc","WaaSMedicSvc"
  foreach ($s in $services) { Try { Stop-Service -Name $s -Force -ErrorAction SilentlyContinue } Catch {} }

  Write-Host "Definindo StartupType Disabled..."
  foreach ($s in $services) { Try { Set-Service -Name $s -StartupType Disabled -ErrorAction SilentlyContinue } Catch {} }

  Write-Host "Aplicando politicas de registro..."
  New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" -Force | Out-Null
  New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" -Force | Out-Null
  New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" -Name "NoAutoUpdate" -Value 1 -PropertyType DWord -Force | Out-Null
  New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" -Name "AUOptions" -Value 1 -PropertyType DWord -Force | Out-Null

  Write-Host "Fallback: definindo Start=4 nas chaves de servico..."
  $svcKeys = @("HKLM:\SYSTEM\CurrentControlSet\Services\wuauserv",
               "HKLM:\SYSTEM\CurrentControlSet\Services\bits",
               "HKLM:\SYSTEM\CurrentControlSet\Services\dosvc",
               "HKLM:\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc")
  foreach ($k in $svcKeys) {
    Try { New-ItemProperty -Path $k -Name "Start" -Value 4 -PropertyType DWord -Force -ErrorAction SilentlyContinue } Catch {}
  }

  Write-Host "Concluido. Reinicie o sistema para garantir aplicacao completa."
}

function Enable-Updates {
  Write-Host "Restaurando servicos e politicas..."
  $map = @{
    "wuauserv" = "Automatic"
    "bits"     = "Automatic"
    "dosvc"    = "Automatic"
    "WaaSMedicSvc" = "Manual"
  }
  foreach ($k in $map.Keys) {
    Try { Set-Service -Name $k -StartupType $map[$k] -ErrorAction SilentlyContinue } Catch {}
    Try { Start-Service -Name $k -ErrorAction SilentlyContinue } Catch {}
  }

  Remove-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" -Name "NoAutoUpdate" -ErrorAction SilentlyContinue
  Remove-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" -Name "AUOptions" -ErrorAction SilentlyContinue

  Write-Host "Atualizacoes habilitadas. Reinicie o computador para garantir."
}

while ($true) {
  Clear-Host
  Write-Host "==============================="
  Write-Host " Windows Update - Menu"
  Write-Host "==============================="
  Write-Host "1) Desabilitar atualizacoes (parar e bloquear)"
  Write-Host "2) Habilitar atualizacoes (restaurar)"
  Write-Host "3) Sair"
  $choice = Read-Host "Escolha [1-3]"

  switch ($choice) {
    "1" { Disable-Updates; Read-Host "Pressione Enter para continuar..." }
    "2" { Enable-Updates; Read-Host "Pressione Enter para continuar..." }
    "3" { break }
    default { Write-Host "Opcao invalida."; Start-Sleep -Seconds 1 }
  }
}
