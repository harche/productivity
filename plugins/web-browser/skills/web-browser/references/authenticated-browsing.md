# Authenticated Browsing

## Use Chrome extension (easiest)

Connect to your real Chrome browser — uses your existing logins, cookies, and sessions.

```bash
playwright-cli open --extension
playwright-cli goto https://authenticated-site.com
# already logged in via your Chrome session
```

## Use a persistent profile

Save browser state to disk so logins persist across sessions.

```bash
# First time: login and the profile is saved automatically
playwright-cli open https://app.example.com/login --persistent
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password"
playwright-cli click e3
playwright-cli close

# Next time: reuse the profile — still logged in
playwright-cli open https://app.example.com/dashboard --persistent
```

### Custom profile directory

```bash
playwright-cli open https://app.example.com --profile=/path/to/profile
```

## Save and restore auth state

Save cookies + localStorage to a file and reload later.

```bash
# Login and save state
playwright-cli open https://app.example.com/login
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password"
playwright-cli click e3
playwright-cli state-save auth.json

# Later: restore state — skip the login
playwright-cli state-load auth.json
playwright-cli goto https://app.example.com/dashboard
# already authenticated
```

## Set cookies manually

```bash
playwright-cli cookie-set session_id abc123 --domain=example.com --httpOnly --secure
playwright-cli goto https://example.com/dashboard
```

## Security notes

- Never commit auth state files to git — add `*.auth-state.json` to `.gitignore`
- Delete state files when done
- Use `--persistent` or `--extension` over manual cookie setting when possible
