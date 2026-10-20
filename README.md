# AshisAura — daily YouTube Shorts automation

This starter project generates an original, anime-aura-inspired (but not based on copyrighted characters) vertical mindset Short, creates narration, builds SEO metadata, and uploads it as a private scheduled video.

## What runs daily
- GitHub Actions starts at 06:30 UTC (12:00 IST).
- Python creates a 1080x1920 MP4 with an original abstract silhouette and aura visuals.
- Microsoft Edge neural TTS via `edge-tts` creates an English voiceover.
- SEO title, description, hashtags, and tags are created from a local fallback or optional Gemini API output.
- YouTube Data API uploads it privately and schedules it for 19:00 IST.

This is a starter workflow, not a promise of viral reach. GitHub scheduled jobs can be delayed or disabled by platform rules; check Actions periodically.

## 1. Create Google Cloud OAuth credentials
1. Open https://console.cloud.google.com/ and create a project.
2. Enable **YouTube Data API v3**: https://console.cloud.google.com/apis/library/youtube.googleapis.com
3. Configure Google Auth Platform / OAuth consent screen. Add your own Google account as a test user if the app is in Testing.
4. Create an OAuth client ID of type **Desktop app** and download its JSON.
5. Rename the downloaded file to `client_secret.json` and place it in this project folder.
6. On your own Windows PC, install Python 3.11+ and FFmpeg, then run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   py auth_youtube.py
   ```
   A browser opens. Sign in to the Google account that owns the channel and approve upload access. This creates `token.json`.

**Important OAuth caveat:** if the OAuth consent app remains in Testing, refresh tokens for these scopes commonly expire after 7 days, so daily automation may stop. Publishing the consent app to Production may require Google verification for YouTube scopes. Do not assume it will run indefinitely until the token is tested and the app status is resolved.

## 2. Add the project to GitHub
1. Create a GitHub repository. A **public** repository's standard GitHub-hosted Actions usage is generally free, but anything committed to a public repository is visible to everyone.
2. Upload the project files, but **never commit `client_secret.json` or `token.json`**.
3. In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.
4. Add these secrets:
   - `YOUTUBE_CLIENT_SECRET_B64`: base64 of `client_secret.json`
   - `YOUTUBE_TOKEN_B64`: base64 of `token.json`
   - `GEMINI_API_KEY` (optional): a key from https://aistudio.google.com/apikey. Without it, a built-in topic/script rotation is used.

### Create Base64 secrets in Windows PowerShell
Run these commands in the project directory; copy each output into the matching GitHub secret:
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("client_secret.json")) | Set-Clipboard
```
Paste clipboard into `YOUTUBE_CLIENT_SECRET_B64`, then run:
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token.json")) | Set-Clipboard
```
Paste clipboard into `YOUTUBE_TOKEN_B64`. Never paste either token into chat or commit it to GitHub.

## 3. Turn on daily automation
- In GitHub, open **Actions**, enable workflows if prompted, select **Daily AshisAura Short**, then click **Run workflow** for a first test.
- The schedule is daily at 06:30 UTC (12:00 IST). The script schedules the Short for 19:00 IST. If the workflow starts too late, it schedules for the next day.
- Open the run logs to see upload status and video ID.
- Keep the repo active. GitHub may disable scheduled workflows in inactive public repositories after 60 days. Scheduled runs may be delayed.

## 4. Optional Gemini script/SEO generation
Add `GEMINI_API_KEY` as a GitHub Actions secret. The code uses Gemini API's `gemini-2.5-flash` endpoint when available; on errors or quota exhaustion, it falls back to built-in scripts. API model availability and free-tier limits can change. Do not enable billing unless you intentionally want paid usage.

## 5. Change upload time
In `.github/workflows/daily.yml`, the cron time controls when the workflow starts. It is currently `30 6 * * *` (12:00 IST). The upload script schedules publication for 19:00 IST using `PUBLISH_HOUR_IST` and `PUBLISH_MINUTE_IST` environment variables.

## 6. Test without uploading
Temporarily add `DRY_RUN: "true"` to the environment of the Generate step in the workflow, or run locally:
```powershell
$env:DRY_RUN="true"
py main.py
```
This renders the video without uploading it. Remove `DRY_RUN` for actual upload.

## Limitations and safety
- YouTube API projects that have not passed YouTube's required compliance audit can have uploads restricted to private visibility. Verify your project's current status before relying on public auto-publishing.
- The default YouTube Data API quota includes a separate `videos.insert` upload allowance (currently documented as 100 calls/day); check the Google Cloud quota page for your project.
- This workflow uses original abstract visuals and generic motivational scripts. Do not add copyrighted anime/Marvel footage, movie dialogue, or music without permission. Reused/low-effort content can also affect monetization eligibility.
- `edge-tts` is a community package using an online service; it is not a guaranteed SLA and may change.
- No AI-generated SEO system can guarantee views or rankings.
- The first version generates simple stylized visuals, not polished anime animation. Improve it with assets you own or are licensed to use.
