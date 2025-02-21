## Backend

Update `.env` with the following:
```bash
GO_WEB_INTERNAL_URL=http://host.docker.internal:3001
# To enable playwright console/network logs
DEBUG_PLAYWRIGHT=True
```
> [!IMPORTANT]
> A second instance of the go-web-app will run at **port 3001** for Playwright.

Start or update containers with:
```bash
# In the background
docker compose up -d serve celery

# In the foreground - Use this to view Playwright logs
docker compose up serve celery
```

## Frontend

For setup instructions, refer to: https://github.com/IFRCGo/go-web-app/?tab=readme-ov-file#local-development

**We need two instances of the go-web-app:**
1. For the host system (browser) on port 3000.
2. For Celery workers (Playwright browser) on port 3001.

To start the regular go-web-app:
```bash
pnpm start:app
```

For the additional go-web-app instance for Playwright:
```bash
APP_API_ENDPOINT=http://host.docker.internal:8000/ pnpm start:app --host --port 3001
```
> [!IMPORTANT]
> The backend will be available at `host.docker.internal:8000` inside the Playwright container running within Celery.
