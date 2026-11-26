$ErrorActionPreference = "Continue"
Set-Location c:\Users\81808\.openclaw\gvqcc_v2832\v69_heads_for_3284
$env:K8_NPZ = "c:\Users\81808\.openclaw\gvqcc_v2832\v69_heads_for_3284\words_3284.npz"

$NREL = 12
$E = 29
$LIMIT = 450

foreach ($k in @(5, 7, 11, 1)) {
    $cover = "cover95_k${k}_s1.pkl"
    if (-not (Test-Path $cover)) {
        Write-Host "=== [$(Get-Date -Format HH:mm:ss)] Designing 95-product cover for k=$k (target 233 CCX) ==="
        cmd /c "python -X utf8 x43_perp.py $k > perp_k$k.txt"
        cmd /c ".\d20.exe 20 600 1 3 < perp_k$k.txt > d20_k$k.out 2> d20_k$k.err"
        if (-not (Select-String -Path "d20_k$k.out" -Pattern "FOUND" -Quiet)) {
            Write-Host "  NO 95-product design found for k=$k"
            continue
        }
        Write-Host "  [$(Get-Date -Format HH:mm:ss)] FOUND 95-product design for k=$k; extracting cover..."
        cmd /c "python -X utf8 x46_fix7.py $k $E"
    } else {
        Write-Host "=== [$(Get-Date -Format HH:mm:ss)] Reusing existing $cover for k=$k ==="
    }
    for ($seed = 3; $seed -le 25; $seed++) {
        $log = "make2_k${k}_n95_r${NREL}_s${seed}.log"
        Write-Host "  [$(Get-Date -Format HH:mm:ss)] k=$k NREL=$NREL seed=$seed (limit ${LIMIT}s)..."
        cmd /c "python -X utf8 -u make2.py $k $cover $NREL $E $seed $LIMIT > $log 2>&1"
        if ((Select-String -Path $log -Pattern "'status': 'PASS" -Quiet) -and (-not (Select-String -Path $log -Pattern "Traceback" -Quiet))) {
            Copy-Item "angle_k_${k}_n95_f${NREL}_s${seed}.kmb" "best_angle_k_${k}.kmb" -Force
            Write-Host "  >>> [$(Get-Date -Format HH:mm:ss)] PASS!! k=$k -> 233 CCX (seed=$seed) <<<"
            break
        }
        $err = (Select-String -Path $log -Pattern "Error|error|timeout|Timeout" | Select-Object -Last 1)
        Write-Host "  [$(Get-Date -Format HH:mm:ss)] k=$k seed=$seed did not pass ($err)"
    }
}
Write-Host "=== ALL HEADS FINISHED ==="
Get-ChildItem best_angle_k_*.kmb -ErrorAction SilentlyContinue | Select-Object Name, Length
