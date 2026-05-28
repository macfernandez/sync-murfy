# sync-murfy

GitHub Action to back up a [Murfy](https://murfy.ai) LaTeX project into a git repository.

> **Current state:** the Python script (`sync.py`) is ready to run locally with a visible browser. The GitHub Action workflow will be added in a later step.

## Local setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Google Chrome

### Install dependencies

```bash
uv sync
```

### Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your Murfy credentials and project name:

```env
MURFY_EMAIL=your@email.com
MURFY_PASSWORD=yourpassword
MURFY_PROJECT=your-project-name   # leave empty to use the first project in the list
```

`MURFY_PROJECT` must match the project name as it appears in the Murfy dashboard (the title shown in the project list). When running as a GitHub Action, this value is set as a repository variable (`vars.MURFY_PROJECT` in the workflow YAML), not as a secret.

### Run

```bash
uv run python sync.py
```

Chrome will open visibly so you can follow along. The downloaded ZIP ends up in `./downloads/{project-name}.zip`.

## Adjusting selectors

The script uses confirmed CSS/XPath selectors for murfy.ai's DOM. If the site changes and a step breaks, look for the `# TODO` comment in `sync.py` (submit button selector) and use Chrome DevTools (F12 → click the element → Copy selector) to update it.
