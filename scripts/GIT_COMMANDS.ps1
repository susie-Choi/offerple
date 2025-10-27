# PowerShell script for committing paper evaluation framework

Write-Host "=== Current Git Status ===" -ForegroundColor Cyan
git status

Write-Host "`n=== Adding new files ===" -ForegroundColor Cyan
git add src/zero_day_defense/evaluation/
git add scripts/collect_paper_dataset.py
git add scripts/run_historical_validation.py
git add scripts/run_historical_validation_mock.py
git add .kiro/specs/paper-evaluation-framework/
git add docs/PAPER_*.md
git add docs/QUICK_START_PAPER.md
git add docs/TODAY_ACHIEVEMENTS.md

Write-Host "`n=== Adding modified files ===" -ForegroundColor Cyan
git add src/zero_day_defense/data_sources/
git add src/zero_day_defense/prediction/engine/scorer.py
git add src/zero_day_defense/prediction/signal_collectors/storage.py
git add requirements.txt
git add .gitignore

Write-Host "`n=== Files to be committed ===" -ForegroundColor Cyan
git diff --cached --name-status

Write-Host "`n=== Committing ===" -ForegroundColor Cyan
git commit -F COMMIT_MESSAGE.md

Write-Host "`n=== Commit Details ===" -ForegroundColor Cyan
git log -1 --stat

Write-Host "`n=== Ready to push ===" -ForegroundColor Green
Write-Host "Run: git push origin main" -ForegroundColor Yellow
