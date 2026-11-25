# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0]

### Added
- GitHub Actions CI workflow (`.github/workflows/ci.yml`): runs on push and pull_request to `main` and manually (`workflow_dispatch`) with a module choice; the four modules run in parallel via a matrix; logs, CSV files and charts are uploaded as artifacts.
- Self-hosted runner workflow (`.github/workflows/ci-selfhosted.yml`): manual run of the full pipeline on a local Windows runner with a direct download from the open data portal.
- Fallback dataset (`data/fallback/dataset.csv`): `data_load` uses it when the portal is unreachable and `DATA_LOAD_FALLBACK=1` is set (CI only).
- `artifacts/` added to `.gitignore`.
- `REPORT.md`: Lab 2 section with a comparison of GitHub-hosted and self-hosted runners.

### Fixed
- CI failure caused by the open data portal returning `403 Forbidden` to GitHub-hosted runners.

## [0.1.0]

### Added
- Project structure (`data/`, `notebooks/`, `src/`, `reports/figures/`) and `.gitignore` for Python cache, Jupyter checkpoints, virtual environment, secrets and data folders.
- README: project goal, data source, field descriptions, hypotheses, development environment (Zed, venv) and run order.
- `data_load` module: downloads the dataset on shelters and internet access in educational institutions of Lviv oblast, detects encoding and delimiter, saves a UTF-8 CSV to `data/raw/`.
- `data_quality_analysis` module: data quality report (missing values, duplicates, inconsistent and invalid values) and cleaning; the clean dataset is saved to `data/processed/`.
- `data_research` module: tests three hypotheses and fits a logistic regression model that predicts internet availability in a shelter.
- `visualization` module: four charts saved to `reports/figures/`.
- `REPORT.md` with the analysis results and a description of the Git workflow.

### Fixed
- Merge conflict in `README.md` ("Модулі" section) between `feature/data_quality_analysis` and `feature/data_research`.
- Order of the modules in the README "Модулі" section after the conflict was resolved.
