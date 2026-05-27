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

```
MURFY_EMAIL=tu@email.com
MURFY_PASSWORD=tupassword
MURFY_PROJECT=nombre-del-proyecto   # leave empty to open the first project
```

### Run

```bash
uv run python sync.py
```

Chrome will open visibly so you can follow the flow. The project files end up in `./project/`.

## Adjusting selectors

The script uses best-guess CSS/XPath selectors for murfy.ai's DOM. If any step fails, look for the `# TODO` comments in `sync.py` and update the selectors using Chrome DevTools (F12 → click the element → Copy selector).

The steps that most likely need adjustment are:

| Step | Function | What to inspect |
|---|---|---|
| Login fields | `login()` | Email/password inputs and submit button |
| Post-login dashboard | `login()` | Any element present after a successful login |
| Project list item | `find_and_open_project()` | The link/element for a project in the list |
| Editor loaded | `download_project_zip()` | Any element present once the editor is ready |
| Menu + download button | `download_project_zip()` | The menu toggle and the download/export ZIP option |
