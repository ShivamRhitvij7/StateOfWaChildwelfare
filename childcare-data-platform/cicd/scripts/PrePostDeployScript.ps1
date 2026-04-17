param(
    [parameter(Mandatory = $true)]  [String] $armTemplate,
    [parameter(Mandatory = $true)]  [String] $ResourceGroupName,
    [parameter(Mandatory = $true)]  [String] $DataFactoryName,
    [parameter(Mandatory = $true)]  [Bool]   $predeployment
)

$templateJson = Get-Content $armTemplate | ConvertFrom-Json
$triggers = $templateJson.resources | Where-Object { $_.type -eq "Microsoft.DataFactory/factories/triggers" }

if ($predeployment -eq $true) {
    # ── PRE-DEPLOYMENT: Stop all active triggers ──
    Write-Host "🛑 Stopping triggers before deployment..."

    $triggersToStop = Get-AzDataFactoryV2Trigger `
        -DataFactoryName $DataFactoryName `
        -ResourceGroupName $ResourceGroupName

    $triggersToStop | ForEach-Object {
        if ($_.RuntimeState -eq "Started") {
            Write-Host "  Stopping trigger: $($_.Name)"
            Stop-AzDataFactoryV2Trigger `
                -ResourceGroupName $ResourceGroupName `
                -DataFactoryName $DataFactoryName `
                -Name $_.Name `
                -Force
        }
    }

    Write-Host "✅ All triggers stopped."
}
else {
    # ── POST-DEPLOYMENT: Restart triggers that exist in the ARM template ──
    Write-Host "▶️ Restarting triggers after deployment..."

    $triggers | ForEach-Object {
        $triggerName = $_.name.Substring(37, $_.name.Length - 37)  # Strip factory prefix

        Write-Host "  Starting trigger: $triggerName"
        try {
            Start-AzDataFactoryV2Trigger `
                -ResourceGroupName $ResourceGroupName `
                -DataFactoryName $DataFactoryName `
                -Name $triggerName `
                -Force
        }
        catch {
            Write-Warning "  ⚠️ Could not start trigger '$triggerName': $_"
            # Don't fail the deployment — log and continue
            # The team can manually start it after investigation
        }
    }

    # ── CLEANUP: Remove triggers that are no longer in the template ──
    Write-Host "🧹 Checking for orphaned triggers..."

    $currentTriggers = Get-AzDataFactoryV2Trigger `
        -DataFactoryName $DataFactoryName `
        -ResourceGroupName $ResourceGroupName

    $templateTriggerNames = $triggers | ForEach-Object {
        $_.name.Substring(37, $_.name.Length - 37)
    }

    $currentTriggers | ForEach-Object {
        if ($templateTriggerNames -notcontains $_.Name) {
            Write-Host "  Removing orphaned trigger: $($_.Name)"
            if ($_.RuntimeState -eq "Started") {
                Stop-AzDataFactoryV2Trigger `
                    -ResourceGroupName $ResourceGroupName `
                    -DataFactoryName $DataFactoryName `
                    -Name $_.Name `
                    -Force
            }
            Remove-AzDataFactoryV2Trigger `
                -ResourceGroupName $ResourceGroupName `
                -DataFactoryName $DataFactoryName `
                -Name $_.Name `
                -Force
        }
    }

    Write-Host "✅ Post-deployment complete."
}