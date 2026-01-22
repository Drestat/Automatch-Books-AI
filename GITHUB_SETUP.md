# GitHub Integration Setup

I have initialized a root-level git repository for this project. To finish the integration with GitHub, follow these final steps:

## 1. Create a New Repository on GitHub
1. Go to [github.com/new](https://github.com/new).
2. Name it `Easy-Bank-Transactions`.
3. Do **NOT** initialize it with a README, license, or gitignore (I have already created these locally).

## 2. Link your Local Repo to GitHub
Run the following commands in your terminal:

```bash
git remote add origin https://github.com/YOUR_USERNAME/Easy-Bank-Transactions.git
git branch -M main
git push -u origin main
```

## 3. GitHub Actions
I have already set up a basic CI workflow in `.github/workflows/backend.yml`. Every time you push to `main`, GitHub will automatically:
- Set up a Python 3.9 environment.
- Install your backend dependencies.
- Perform a syntax check on your code.

## 4. Automatic Version Control
Going forward, I will automatically commit major logic changes. You can always see the history by running `git log`.
