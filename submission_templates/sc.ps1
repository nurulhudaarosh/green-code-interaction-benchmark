$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$MetadataFile = Join-Path $Root "metadata.json"
$DatasetRoot = Join-Path $Root "dataset"
$SubmissionDir = Join-Path $Root "submission"
$SubmissionsDir = Join-Path $Root "submissions"

$Models = @("gpt", "claude", "gemini", "deepseek")

function Fail($Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Ok($Message) {
    Write-Host "OK: $Message" -ForegroundColor Green
}

function Require-File($Path, $Message) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail $Message
    }
}

function Load-Metadata {
    Require-File $MetadataFile "metadata.json not found."

    try {
        $script:Meta = Get-Content -Raw -LiteralPath $MetadataFile | ConvertFrom-Json
    } catch {
        Fail "metadata.json is not valid JSON."
    }

    if ([string]::IsNullOrWhiteSpace([string]$Meta.category)) {
        Fail "metadata.json is missing category."
    }

    if ([string]::IsNullOrWhiteSpace([string]$Meta.task_id)) {
        Fail "metadata.json is missing task_id."
    }

    $script:Category = [string]$Meta.category
    $script:TaskId = [string]$Meta.task_id
    $script:Completed = [int]$Meta.completed
}

function Load-Task {
    $script:DatasetFile = Join-Path (Join-Path $DatasetRoot $Category) "dataset.json"

    Require-File $DatasetFile "Dataset not found: $DatasetFile"

    try {
        $data = Get-Content -Raw -LiteralPath $DatasetFile | ConvertFrom-Json
    } catch {
        Fail "dataset.json is not valid JSON."
    }

    if ($null -ne $data.tasks) {
        $tasks = @($data.tasks)
    } else {
        $tasks = @($data)
    }

    $task = $tasks | Where-Object { [string]$_.task_id -eq $TaskId } | Select-Object -First 1

    if ($null -eq $task) {
        Fail "Task '$TaskId' was not found in $DatasetFile."
    }

    $script:Task = $task
    $script:TaskTitle = [string]$task.title

    if ($null -eq $task.interaction_design) {
        Fail "Task '$TaskId' has no interaction_design."
    }

    $script:Interactions = @(
        $task.interaction_design.psobject.Properties.Name
    )

    if ($Interactions.Count -eq 0) {
        Fail "Task '$TaskId' has no interactions."
    }
}

function New-File($Path) {
    $parent = Split-Path -Parent $Path

    if (!(Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    if (!(Test-Path -LiteralPath $Path)) {
        New-Item -ItemType File -Path $Path -Force | Out-Null
    }
}

function New-Interaction($Model, $Interaction) {
    $base = Join-Path $SubmissionDir $Model

    switch ($Interaction) {
        "ONE_SHOT" {
            New-File (Join-Path $base "one_shot\code.py")
        }

        "BUG_FIX" {
            New-File (Join-Path $base "bug_fix\initial.py")
            New-File (Join-Path $base "bug_fix\final.py")
        }

        "FEATURE_ADDITION" {
            New-File (Join-Path $base "feature_addition\initial.py")
            New-File (Join-Path $base "feature_addition\final.py")
        }

        "EDGE_CASE" {
            New-File (Join-Path $base "edge_case\initial.py")
            New-File (Join-Path $base "edge_case\final.py")
        }

        "FULL_MULTI_TURN" {
            New-File (Join-Path $base "full_multi_turn\turn_01.py")
            New-File (Join-Path $base "full_multi_turn\turn_02.py")
            New-File (Join-Path $base "full_multi_turn\turn_03.py")
            New-File (Join-Path $base "full_multi_turn\turn_04.py")
            New-File (Join-Path $base "full_multi_turn\final.py")
        }

        default {
            Fail "Unknown interaction '$Interaction'."
        }
    }
}

function New-Template {
    if (Test-Path -LiteralPath $SubmissionDir) {
        Remove-Item -LiteralPath $SubmissionDir -Recurse -Force
    }

    New-Item -ItemType Directory -Path $SubmissionDir -Force | Out-Null

    @{
        category = $Category
        task_id = $TaskId
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $SubmissionDir "metadata.json") -Encoding UTF8

    foreach ($model in $Models) {
        foreach ($interaction in $Interactions) {
            New-Interaction $model $interaction
        }
    }

    @"
GREEN CODE INTERACTION BENCHMARK

Category : $Category
Task ID  : $TaskId
Title    : $TaskTitle

Use the exact prompts from the dataset.
Do not modify generated code.
For multi-turn interactions, continue the same conversation.
Do not rename files or folders.
Do not add extra files.

When finished, return to the workspace root and run:

    sc.bat submit
"@ | Set-Content -LiteralPath (Join-Path $SubmissionDir "README.txt") -Encoding UTF8

    Write-Host ""
    Ok "Submission template created."
    Write-Host "Category : $Category"
    Write-Host "Task ID  : $TaskId"
    Write-Host "Title    : $TaskTitle"
    Write-Host ""
    Write-Host "Interactions:"
    foreach ($i in $Interactions) {
        Write-Host "  - $i"
    }
}

function Validate-File($Path) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail "Missing file: $Path"
    }

    if ((Get-Item -LiteralPath $Path).Length -eq 0) {
        Fail "Empty file: $Path"
    }
}

function Validate-Submission {
    if (!(Test-Path -LiteralPath $SubmissionDir -PathType Container)) {
        Fail "submission folder not found. Run: sc.bat init"
    }

    $subMetaPath = Join-Path $SubmissionDir "metadata.json"
    Require-File $subMetaPath "submission/metadata.json is missing."

    try {
        $subMeta = Get-Content -Raw -LiteralPath $subMetaPath | ConvertFrom-Json
    } catch {
        Fail "submission/metadata.json is invalid JSON."
    }

    if ([string]$subMeta.category -ne $Category) {
        Fail "Submission category does not match metadata.json."
    }

    if ([string]$subMeta.task_id -ne $TaskId) {
        Fail "Submission task_id does not match metadata.json."
    }

    foreach ($model in $Models) {
        foreach ($interaction in $Interactions) {

            switch ($interaction) {
                "ONE_SHOT" {
                    Validate-File (Join-Path $SubmissionDir "$model\one_shot\code.py")
                }

                "BUG_FIX" {
                    Validate-File (Join-Path $SubmissionDir "$model\bug_fix\initial.py")
                    Validate-File (Join-Path $SubmissionDir "$model\bug_fix\final.py")
                }

                "FEATURE_ADDITION" {
                    Validate-File (Join-Path $SubmissionDir "$model\feature_addition\initial.py")
                    Validate-File (Join-Path $SubmissionDir "$model\feature_addition\final.py")
                }

                "EDGE_CASE" {
                    Validate-File (Join-Path $SubmissionDir "$model\edge_case\initial.py")
                    Validate-File (Join-Path $SubmissionDir "$model\edge_case\final.py")
                }

                "FULL_MULTI_TURN" {
                    Validate-File (Join-Path $SubmissionDir "$model\full_multi_turn\turn_01.py")
                    Validate-File (Join-Path $SubmissionDir "$model\full_multi_turn\turn_02.py")
                    Validate-File (Join-Path $SubmissionDir "$model\full_multi_turn\turn_03.py")
                    Validate-File (Join-Path $SubmissionDir "$model\full_multi_turn\turn_04.py")
                    Validate-File (Join-Path $SubmissionDir "$model\full_multi_turn\final.py")
                }
            }
        }
    }

    Ok "Submission validation passed."
}

function Save-Metadata($NewTaskId) {
    $Meta.completed = [int]$Meta.completed + 1
    $Meta.task_id = $NewTaskId

    $Meta | ConvertTo-Json | Set-Content -LiteralPath $MetadataFile -Encoding UTF8
}

function Get-NextTask {
    $data = Get-Content -Raw -LiteralPath $DatasetFile | ConvertFrom-Json

    if ($null -ne $data.tasks) {
        $tasks = @($data.tasks)
    } else {
        $tasks = @($data)
    }

    $ids = @($tasks | ForEach-Object { [string]$_.task_id })
    $index = [Array]::IndexOf($ids, $TaskId)

    if ($index -lt 0) {
        Fail "Current task is not present in dataset."
    }

    if ($index + 1 -ge $ids.Count) {
        return $null
    }

    return $ids[$index + 1]
}

function Do-Init {
    Load-Metadata
    Load-Task
    New-Template
}

function Do-Submit {
    Load-Metadata
    Load-Task

    Write-Host ""
    Write-Host "Submitting $TaskId..." -ForegroundColor Cyan

    Validate-Submission

    if (!(Test-Path -LiteralPath $SubmissionsDir)) {
        New-Item -ItemType Directory -Path $SubmissionsDir -Force | Out-Null
    }

    $zipPath = Join-Path $SubmissionsDir "$TaskId.zip"

    if (Test-Path -LiteralPath $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }

    Compress-Archive -Path (Join-Path $SubmissionDir "*") -DestinationPath $zipPath -Force

    Ok "ZIP created: $zipPath"

    Remove-Item -LiteralPath $SubmissionDir -Recurse -Force
    Ok "Old submission folder removed."

    $next = Get-NextTask

    if ($null -eq $next) {
        Save-Metadata $null
        Write-Host ""
        Write-Host "All tasks in this category are completed." -ForegroundColor Yellow
        return
    }

    Save-Metadata $next

    Load-Metadata
    Load-Task
    New-Template

    Write-Host ""
    Ok "Ready for next task: $TaskId"
}

function Do-Status {
    Load-Metadata
    Load-Task

    Write-Host ""
    Write-Host "===================================="
    Write-Host " Green Code Benchmark Status"
    Write-Host "===================================="
    Write-Host "Category  : $Category"
    Write-Host "Task ID   : $TaskId"
    Write-Host "Title     : $TaskTitle"
    Write-Host "Completed : $Completed"
    Write-Host ""
    Write-Host "Interactions:"
    foreach ($i in $Interactions) {
        Write-Host "  - $i"
    }
    Write-Host ""
}

function Do-Reset {
    if (Test-Path -LiteralPath $SubmissionDir) {
        Remove-Item -LiteralPath $SubmissionDir -Recurse -Force
        Ok "Current submission folder removed."
    } else {
        Write-Host "No submission folder exists."
    }
}

$Command = if ($args.Count -gt 0) { $args[0].ToLower() } else { "" }

switch ($Command) {
    "init"   { Do-Init }
    "submit" { Do-Submit }
    "status" { Do-Status }
    "reset"  { Do-Reset }
    default {
        Write-Host ""
        Write-Host "Green Code Interaction Benchmark"
        Write-Host ""
        Write-Host "Usage:"
        Write-Host "  sc.bat init"
        Write-Host "  sc.bat submit"
        Write-Host "  sc.bat status"
        Write-Host "  sc.bat reset"
        Write-Host ""
    }
}
