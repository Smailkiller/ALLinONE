<# 
Search_and_pin.ps1
���� ����� �� WORD.txt �� ���� ��������� ������ �������:
- ����� �������� (������)
- ����� ����������
- �������� ����������
����� ���������� � index.txt ����� �� ��������.
���������� ��������� ��������� (������� + ������� ������������� ������).
#>

# --- ���������/���� ---
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$WordFile  = Join-Path $ScriptDir 'WORD.txt'
$OutFile   = Join-Path $ScriptDir 'index.txt'

# ���� ������ ������ % ��������� (��������� � �����������), ������� �� $true
$PreciseProgress = $false

# --- �������� ---
if (-not (Test-Path $WordFile)) {
    Write-Error ("WORD.txt �� ������: {0}. ��������� ������ ���� '������ �� ������: �����1, �����2,'." -f $WordFile)
    exit 1
}

# --- ������ �������� ����� ---
try {
    $raw = Get-Content -Path $WordFile -Raw -ErrorAction Stop
} catch {
    Write-Error ("�� ������� ��������� WORD.txt {0}: {1}" -f $WordFile, $_.Exception.Message)
    exit 1
}

# ���� �� ����� ���������, ����� �� �������, ������ �� ��������/�������
$afterColon = ($raw -split ":", 2)[-1]
$terms = $afterColon -split "," |
    ForEach-Object { $_.Trim(" `t`r`n`"'���") } |
    Where-Object { $_ -match '\S' } |
    Select-Object -Unique

if (-not $terms -or $terms.Count -eq 0) {
    Write-Error "� WORD.txt �� ������� �� ������ ��������� ����� ����� ���������."
    exit 1
}

# --- ��������� (��������� ����������) ---
$escaped = $terms | ForEach-Object { [Regex]::Escape($_) }
$pattern = "(?i)(" + ($escaped -join "|") + ")"
$rx      = [Regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

# --- ���������� ������ ---
# ���������� index.txt (���� ������ ���������� � ������������� ������ ����)
"" | Out-File -FilePath $OutFile -Encoding UTF8

# ����� �� ����������� ���������� ������
$set = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

function Add-Line {
    param([string]$Line)
    if ($Line -and $set.Add($Line)) {
        Add-Content -Path $OutFile -Value $Line
    }
}

# �������� �������� ������� � ������
function ValueToString {
    param($v)
    if ($null -eq $v) { return "" }
    if ($v -is [byte[]])      { return [BitConverter]::ToString($v) }
    elseif ($v -is [Array])   { return ($v -join "; ") }
    else                      { return [string]$v }
}

Add-Line ("=== �����: {0} ===" -f ($terms -join ', '))
Add-Line ("����: {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Add-Line ""

# --- ���������� ����� ������� � ������� ������ ---
$regDrives = Get-PSDrive -PSProvider Registry | Select-Object -ExpandProperty Name
$preferredOrder = @('HKLM','HKCU','HKCR','HKU','HKCC')
$ordered = @()
foreach ($p in $preferredOrder) { if ($regDrives -contains $p) { $ordered += $p } }
$ordered += ($regDrives | Where-Object { $preferredOrder -notcontains $_ })
$ordered = $ordered | Select-Object -Unique

# --- ����� �� ������ � ���������� ---
$spinner = @('-', '\', '|', '/')

foreach ($drive in $ordered) {
    $rootPath = "${drive}:\"
    $actTitle = ("Scanning {0}" -f $rootPath)
    Write-Host ("Scanning {0} ..." -f $rootPath)

    try {
        if ($PreciseProgress) {
            # ������ %: ������� �������� ������ ���� ������ (�������� �� ������� ������)
            $allKeys = @(Get-ChildItem -Path $rootPath -Recurse -ErrorAction SilentlyContinue)
            $total   = $allKeys.Count
            $i = 0

            foreach ($key in $allKeys) {
                $i++
                if (($i % 300) -eq 0) {
                    $pct = if ($total -gt 0) { [int](($i / $total) * 100) } else { 0 }
                    Write-Progress -Activity $actTitle -Status ("{0}/{1}" -f $i, $total) -PercentComplete $pct
                }

                $keyName     = $key.PSChildName
                $fullKeyPath = $key.PSPath -replace '^Microsoft\.PowerShell\.Core\\Registry::',''

                if ($rx.IsMatch($keyName) -or $rx.IsMatch($fullKeyPath)) {
                    Add-Line ("[KEY]  {0}" -f $fullKeyPath)
                }

                try {
                    $props = (Get-ItemProperty -Path $key.PSPath -ErrorAction Stop).PSObject.Properties |
                             Where-Object { $_.Name -notin @('PSPath','PSParentPath','PSChildName','PSDrive','PSProvider') }

                    foreach ($p in $props) {
                        $vn = $p.Name
                        if ($rx.IsMatch($vn)) {
                            Add-Line ("[NAME] {0} -> {1}" -f $fullKeyPath, $vn)
                        }
                        try {
                            $vv = Get-ItemPropertyValue -Path $key.PSPath -Name $vn -ErrorAction Stop
                            $vs = ValueToString $vv
                            if ($vs -and $rx.IsMatch($vs)) {
                                $snippet = if ($vs.Length -gt 160) { $vs.Substring(0,160) + '�' } else { $vs }
                                Add-Line ("[DATA] {0} -> {1} = {2}" -f $fullKeyPath, $vn, $snippet)
                            }
                        } catch { }
                    }
                } catch { }
            }

            Write-Progress -Activity $actTitle -Completed
            Write-Host ("Done {0} (keys scanned: {1})." -f $rootPath, $total)
        }
        else {
            # ˸���� ���������: ������� + ������� (��� ������� ��������)
            $processed = 0
            $spinIdx   = 0

            Get-ChildItem -Path $rootPath -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
                $key = $_
                $processed++
                if (($processed % 500) -eq 0) {
                    $spinIdx = ($spinIdx + 1) % $spinner.Count
                    Write-Progress -Activity $actTitle `
                                   -Status   ("Checked {0} keys  {1}" -f $processed, $spinner[$spinIdx]) `
                                   -PercentComplete 0
                }

                $keyName     = $key.PSChildName
                $fullKeyPath = $key.PSPath -replace '^Microsoft\.PowerShell\.Core\\Registry::',''

                if ($rx.IsMatch($keyName) -or $rx.IsMatch($fullKeyPath)) {
                    Add-Line ("[KEY]  {0}" -f $fullKeyPath)
                }

                try {
                    $props = (Get-ItemProperty -Path $key.PSPath -ErrorAction Stop).PSObject.Properties |
                             Where-Object { $_.Name -notin @('PSPath','PSParentPath','PSChildName','PSDrive','PSProvider') }

                    foreach ($p in $props) {
                        $vn = $p.Name
                        if ($rx.IsMatch($vn)) {
                            Add-Line ("[NAME] {0} -> {1}" -f $fullKeyPath, $vn)
                        }
                        try {
                            $vv = Get-ItemPropertyValue -Path $key.PSPath -Name $vn -ErrorAction Stop
                            $vs = ValueToString $vv
                            if ($vs -and $rx.IsMatch($vs)) {
                                $snippet = if ($vs.Length -gt 160) { $vs.Substring(0,160) + '�' } else { $vs }
                                Add-Line ("[DATA] {0} -> {1} = {2}" -f $fullKeyPath, $vn, $snippet)
                            }
                        } catch { }
                    }
                } catch { }
            }

            Write-Progress -Activity $actTitle -Completed
            Write-Host ("Done {0} (keys scanned: {1})." -f $rootPath, $processed)
        }
    } catch {
        Write-Progress -Activity $actTitle -Completed
        Write-Warning ("Failed to enumerate {0}: {1}" -f $rootPath, $_.Exception.Message)
    }
}

Add-Line ""
Add-Line "=== ����� ������ ==="

Write-Host ("������. ����������: {0}" -f $OutFile)
