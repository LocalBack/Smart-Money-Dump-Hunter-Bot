1. Generate `.env.live` from `env/.env.live.example`.
2. Add your real API keys (withdraw disabled on the exchange).
3. Run `docker compose --env-file .env.live up -d`.
4. Verify you receive the Telegram message "LIVE MODE ENABLED".
5. Run the chaos/kill-switch test once to ensure shutdown works.
