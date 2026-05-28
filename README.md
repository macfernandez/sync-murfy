# sync-murfy

GitHub Action to back up a [Murfy](https://murfy.ai) LaTeX project into a git repository.

## Local setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Google Chrome

> **GitHub Actions:** the action requires `runs-on: ubuntu-latest` (Chrome is pre-installed on that runner).

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
MURFY_PROJECT=your-project-name
```

`MURFY_PROJECT` must match the project name as it appears in the Murfy dashboard (the title shown in the project list).

### Run

```bash
uv run python sync.py
```

Chrome will open visibly so you can follow along. The downloaded ZIP ends up in `./downloads/{project-name}.zip`.

## Using this action

```yaml
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: macfernandez/sync-murfy@main
        id: murfy
        with:
          email: ${{ secrets.MURFY_EMAIL }}
          password: ${{ secrets.MURFY_PASSWORD }}
          project: ${{ vars.MURFY_PROJECT }}

      # The ZIP is now at steps.murfy.outputs.zip-path
      - name: Unzip into folder
        run: unzip "${{ steps.murfy.outputs.zip-path }}" -d ./my-folder/
```

It is recommended to store `MURFY_EMAIL` and `MURFY_PASSWORD` as repository secrets and `MURFY_PROJECT` as a repository variable, but the action accepts any combination.

## Maintenance

The CSS/XPath selectors in `sync.py` were confirmed against murfy.ai's DOM at the time of writing. If the site changes and a step breaks, inspect the relevant element with Chrome DevTools (F12 → click the element → Copy selector) and update the corresponding selector in `sync.py`.
