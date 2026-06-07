# sync-murfy

[![GitHub Release](https://img.shields.io/github/v/release/macfernandez/sync-murfy)](https://github.com/macfernandez/sync-murfy/releases)

> **Unofficial tool.** This project is community-built and is not affiliated with or endorsed by Murfy / Murple Corp. Usage is at the user's own risk.

GitHub Action to back up a [Murfy](https://murfy.ai) LaTeX project into a git repository.

## Important notices

### Credential security

This action requires your Murfy password to be stored as a **GitHub Secret**. GitHub Secrets are encrypted at rest and never exposed in workflow logs, but you should be aware of the following before proceeding:

- The secret value is a plaintext password. Anyone with admin access to the repository can use (but not read) it; anyone who can write workflow files can potentially expose it in a workflow run.
- Consider using a dedicated Murfy account — or at minimum a unique password — rather than your primary account credentials. As a safety measure, we recommend that account only has read access to the project being synced.
- If your credentials are ever compromised, revoke them from the Murfy dashboard immediately.

### Scheduling

If you automate this action on a schedule, **please avoid frequent runs.** Running this too often generates unnecessary load on Murfy's infrastructure and may result in access being revoked.

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
MURFY_PROJECT=your-project-name
```

`MURFY_PROJECT` must match the project name as it appears in the Murfy dashboard (the title shown in the project list).

### Run

```bash
uv run python sync.py
```

Chrome will open visibly so you can follow along. The downloaded ZIP ends up in `./downloads/{project-name}.zip`.

## Using this action

Pin to a **specific tagged release** rather than `@main`. Following `@main` means your workflow silently picks up every future change to this action, including potentially breaking ones.

```yaml
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: macfernandez/sync-murfy@v1.0.0   # pin to a specific release
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

The CSS/XPath selectors in `sync.py` were confirmed against murfy.ai's DOM at the time of writing. If the site changes and a step breaks, inspect the relevant element with Chrome DevTools (F12 → click the element → Copy selector) and update the corresponding selector in `sync.py`
