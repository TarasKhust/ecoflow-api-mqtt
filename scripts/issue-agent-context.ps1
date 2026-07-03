param(
    [Parameter(Mandatory = $true)]
    [int] $IssueNumber
)

$ErrorActionPreference = "Stop"

function Invoke-GhJson {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    $output = & gh @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gh $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }

    return $output
}

$repo = Invoke-GhJson -Arguments @("repo", "view", "--json", "nameWithOwner,defaultBranchRef")
$issue = Invoke-GhJson -Arguments @(
    "issue", "view", "$IssueNumber",
    "--json", "number,title,body,author,labels,comments,state,createdAt,updatedAt,url"
)
$openIssues = Invoke-GhJson -Arguments @(
    "issue", "list",
    "--state", "open",
    "--limit", "20",
    "--json", "number,title,labels,updatedAt,url"
)
$openPrs = Invoke-GhJson -Arguments @(
    "pr", "list",
    "--state", "open",
    "--limit", "20",
    "--json", "number,title,headRefName,baseRefName,mergeable,reviewDecision,updatedAt,url"
)
$releases = Invoke-GhJson -Arguments @("release", "list", "--limit", "10")
$tags = & git --no-pager tag --sort=-creatordate |
    Select-Object -First 20
$recentCommits = & git --no-pager log --oneline --decorate --max-count=12 origin/main

$context = [ordered]@{
    repo = $repo | ConvertFrom-Json
    issue = $issue | ConvertFrom-Json
    openIssues = $openIssues | ConvertFrom-Json
    openPullRequests = $openPrs | ConvertFrom-Json
    recentReleasesText = $releases -join "`n"
    recentTags = @($tags)
    recentMainCommits = @($recentCommits)
}

$context | ConvertTo-Json -Depth 20
