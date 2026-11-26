$ErrorActionPreference = "Continue"
Set-Location c:\Users\81808\.openclaw\gvqcc_v2832\v71_heads_232_for_3275
$env:K8_NPZ = "c:\Users\81808\.openclaw\gvqcc_v2832\v71_heads_232_for_3275\words_3284.npz"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:P1THREADS = "2"
$env:HSOLVE_THREADS = "2"
$env:P1EXE = "p1multi.exe"
$env:P1W0 = "8"
$env:P1EMAX = "26"
$env:P1PAIRLIM = "120"
$env:EAGER = "1"

$NREL = 13
$E = 30
$LIMIT = 360

foreach ($k in @(5, 7, 11, 1)) {
    $cover = "cover95_k${k}_s1.pkl"
    Write-Host "=== [$(Get-Date -Format HH:mm:ss)] Searching 232-CCX (NREL=13) for k=$k using p1multi.exe ==="
    for ($seed = 1; $seed -le 30; $seed++) {
        $log = "make2_k${k}_n95_r${NREL}_s${seed}.log"
        Write-Host "  [$(Get-Date -Format HH:mm:ss)] k=$k NREL=13 seed=$seed (limit ${LIMIT}s)..."
        cmd /c "python -X utf8 -u make2.py $k $cover $NREL $E $seed $LIMIT > $log 2>&1"
        if ((Select-String -Path $log -Pattern "'status': 'PASS" -Quiet) -and (-not (Select-String -Path $log -Pattern "Traceback" -Quiet))) {
            Copy-Item "angle_k_${k}_n95_f${NREL}_s${seed}.kmb" "best232_angle_k_${k}.kmb" -Force
            Write-Host "  >>> [$(Get-Date -Format HH:mm:ss)] PASS!! k=$k -> 232 CCX (seed=$seed) <<<"
            break
        }
        $err = (Select-String -Path $log -Pattern "Error|error|timeout|Timeout" | Select-Object -Last 1)
        Write-Host "  [$(Get-Date -Format HH:mm:ss)] k=$k seed=$seed did not pass ($err)"
    }
}
Write-Host "=== ALL 232 HEADS FINISHED ==="
Get-ChildItem best232_angle_k_*.kmb -ErrorAction SilentlyContinue | Select-Object Name, Length
