# Setting Up Branch Protection with Unit Tests

## Making Unit Tests Required for PR Merging

To make the unit tests a required check before merging PRs, follow these steps:

### 1. Go to Repository Settings
- Navigate to your repository on GitHub
- Click on **Settings** tab
- Click on **Branches** in the left sidebar

### 2. Add Branch Protection Rule
- Click **Add rule** button
- In **Branch name pattern**, enter: `main` (or your default branch name)

### 3. Configure Protection Settings
Check the following boxes:
- ✅ **Require a pull request before merging**
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

### 4. Select Required Status Checks
In the status checks section, search for and select:
- ✅ **test (3.8)** - Unit tests on Python 3.8
- ✅ **test (3.11)** - Unit tests on Python 3.11

### 5. Additional Recommended Settings
- ✅ **Require conversation resolution before merging**
- ✅ **Include administrators** (optional but recommended)

### 6. Save the Rule
Click **Create** to save your branch protection rule.

## Result
After setting this up:
- ❌ PRs **cannot be merged** if unit tests fail
- ✅ PRs can **only be merged** when all tests pass
- 🔄 Tests **automatically run** on every PR update
- 📊 **Coverage reports** are generated and visible in workflow summaries

## Workflow Features
- **Runs on**: All branch pushes and PRs to main/master/dev/develop
- **Tests**: Python 3.8 and 3.11 compatibility
- **Coverage**: Automatic code coverage reporting
- **Artifacts**: Downloadable coverage reports
- **Status**: Clear success/failure indicators for branch protection
