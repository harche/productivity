---
name: web-browser
description: Browse the web — look up information, extract data, fill forms, take screenshots, interact with pages. Use when the user needs to visit a website, read page content, check something online, or extract information from the internet.
allowed-tools: Bash(playwright-cli:*)
---

# Web Browser

Browse the internet to look up information, extract data, fill forms, and interact with web pages.

## Modes

| Mode | Command | When to use |
|------|---------|-------------|
| Headless | `playwright-cli open URL` | Default — fast, no visible window |
| Headed | `playwright-cli open URL --headed` | See what's happening |
| Chrome extension | `playwright-cli open --extension` | Use your real Chrome with existing logins |

## How it works

1. Open a page — get a **snapshot** (accessibility tree with numbered refs like `e1`, `e5`)
2. Interact using refs: `click e3`, `fill e5 "text"`, `select e9 "value"`
3. Each action returns a new snapshot

## Core commands

```bash
playwright-cli open URL                        # open browser + navigate
playwright-cli goto URL                        # navigate current tab
playwright-cli snapshot                        # get current page state
playwright-cli click e3                        # click element by ref
playwright-cli fill e5 "text"                  # fill input field
playwright-cli type "text"                     # type into focused element
playwright-cli press Enter                     # press key
playwright-cli select e9 "option"              # select dropdown
playwright-cli eval "document.title"           # run JS
playwright-cli eval "el => el.textContent" e5  # extract from element
playwright-cli screenshot --filename=page.png  # capture page
playwright-cli pdf --filename=page.pdf         # save as PDF
playwright-cli close                           # close browser
```

## Use cases

### Look up information
```bash
playwright-cli open https://example.com
# read the snapshot that comes back
playwright-cli close
```

### Extract structured data from a page
[Detailed patterns](references/extracting-data.md)
```bash
playwright-cli eval "JSON.stringify([...document.querySelectorAll('.item')].map(el => ({
  title: el.querySelector('h2')?.textContent,
  price: el.querySelector('.price')?.textContent
})))"
```

### Fill forms and submit
[Detailed patterns](references/filling-forms.md)
```bash
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password"
playwright-cli click e3
```

### Browse authenticated sites
[Detailed patterns](references/authenticated-browsing.md)
```bash
playwright-cli open --extension
playwright-cli goto https://authenticated-site.com
```

### Save screenshots and PDFs
[Detailed patterns](references/screenshots-and-pdfs.md)

### Monitor network / API calls
[Detailed patterns](references/network-monitoring.md)

### Work across multiple tabs
[Detailed patterns](references/multi-tab-workflows.md)

## References

* [Extracting data](references/extracting-data.md)
* [Filling forms](references/filling-forms.md)
* [Authenticated browsing](references/authenticated-browsing.md)
* [Screenshots and PDFs](references/screenshots-and-pdfs.md)
* [Network monitoring](references/network-monitoring.md)
* [Multi-tab workflows](references/multi-tab-workflows.md)
* [Session management](references/session-management.md)
* [Storage state](references/storage-state.md)
* [Running custom code](references/running-code.md)
