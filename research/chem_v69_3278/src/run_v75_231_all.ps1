$ErrorActionPreference = "Continue"
Set-Location c:\Users\81808\.openclaw\gvqcc_v2832\v71_heads_232_for_3275
$env:K8_NPZ = "c:\Users\81808\.openclaw\gvqcc_v2832\v71_heads_232_for_3275\words_3284.npz"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:P1THREADS = "2"
$env:HSOLVE_THREADS = "2"
$env:P1EXE = "p1multi.exe"
$env:P1W0 = "8"
$env:P1EMAX = "26"
$env:P1PAIRLIM = "180"

foreach ($k in @(7, 11, 1)) {
    $cov5 = "cover95_k${k}_5col.pkl"
    if (-not (Test-Path $cov5)) {
        Write-Host "=== [$(Get-Date -Format HH:mm:ss)] Running fivecol.py for k=$k ==="
        cmd /c "python -X utf8 -u fivecol.py $k cover95_k${k}_s1.pkl $cov5 1 3000000"
    }
    if (-not (Test-Path $cov5)) {
        Write-Host "  fivecol.py did not find a 5-col cover for k=$k"
        continue
    }
    Write-Host "=== [$(Get-Date -Format HH:mm:ss)] Building 231-CCX via V75 min-dim(R) (e=30) for k=$k ==="
    for ($seed = 1; $seed -le 6; $seed++) {
        $log = "v75_231_k${k}_s${seed}.log"
        Write-Host "  [$(Get-Date -Format HH:mm:ss)] k=$k seed=$seed..."
        cmd /c "python -X utf8 -u c:\Users\81808\.openclaw\gvqcc_v2832\v75_make2_minR.py $k $cov5 13 30 $seed 600 > $log 2>&1"
        if (Select-String -Path $log -Pattern "'status': 'PASS" -Quiet) {
            Copy-Item "best231_v75_angle_k_${k}_s${seed}.kmb" "best231_v75_angle_k_${k}.kmb" -Force
            Write-Host "  >>> [$(Get-Date -Format HH:mm:ss)] WORLD FIRST PASS!! k=$k -> 231 CCX (seed=$seed) <<<"
            break
        }
        $tail = (Get-Content $log -Tail 1)
        Write-Host "  [$(Get-Date -Format HH:mm:ss)] k=$k seed=$seed did not pass ($tail)"
    }
}
Write-Host "=== ALL V75 231 HEADS FINISHED ==="
Get-ChildItem best231_v75_angle_k_*.kmb -ErrorAction SilentlyContinue | Select-Object Name, Length
