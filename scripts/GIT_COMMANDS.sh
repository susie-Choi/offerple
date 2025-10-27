#!/bin/bash
# Git commands for committing paper evaluation framework

# 1. Check current status
echo "=== Current Git Status ==="
git status

# 2. Add all new files
echo ""
echo "=== Adding new files ==="
git add src/zero_day_defense/evaluation/
git add scripts/collect_paper_dataset.py
git add scripts/run_historical_validation.py
git add scripts/run_historical_validation_mock.py
git add .kiro/specs/paper-evaluation-framework/
git add docs/PAPER_*.md
git add docs/QUICK_START_PAPER.md
git add docs/TODAY_ACHIEVEMENTS.md

# 3. Add modified files
echo ""
echo "=== Adding modified files ==="
git add src/zero_day_defense/data_sources/*.py
git add src/zero_day_defense/prediction/engine/scorer.py
git add src/zero_day_defense/prediction/signal_collectors/storage.py
git add requirements.txt
git add .gitignore

# 4. Check what will be committed
echo ""
echo "=== Files to be committed ==="
git diff --cached --name-status

# 5. Commit
echo ""
echo "=== Committing ==="
git commit -F COMMIT_MESSAGE.md

# 6. Show commit
echo ""
echo "=== Commit Details ==="
git log -1 --stat

# 7. Ready to push
echo ""
echo "=== Ready to push ==="
echo "Run: git push origin main"
