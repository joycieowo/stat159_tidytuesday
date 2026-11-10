# MyST website and GitHub Pages

This project includes a MyST website (`myst.yml`, `index.md`, `results.md`) and a GitHub Actions workflow (`.github/workflows/deploy.yml`). The workflow is the equivalent of setting up GitHub Pages with `myst init --gh-pages`; it is already present, so you do not need to rerun that initializer.

## Local preview

From the repository root:

```bash
pip install -U mystmd
myst build --html
```

MyST starts a local preview server, normally on port 3100. Press Ctrl+C to stop it.

## Publish

1. Copy these files to the root of `joycieowo/stat159_tidytuesday`.
2. In GitHub Settings > Pages, select **GitHub Actions** as the source.
3. Commit and push to `main`:

```bash
git add .
git commit -m "Add MyST website and GitHub Pages deployment"
git push origin main
```

4. Check https://github.com/joycieowo/stat159_tidytuesday/actions.
5. When deployment succeeds, open https://joycieowo.github.io/stat159_tidytuesday/.

The workflow uses `BASE_URL=/stat159_tidytuesday` for GitHub project Pages. If the repository is renamed, update that value. If GitHub Actions reports a missing artifact, inspect the HTML output location from the build log and update `path` in the upload step.
