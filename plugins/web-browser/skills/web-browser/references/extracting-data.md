# Extracting Data from Web Pages

## Read the snapshot

The simplest approach — every navigation returns a snapshot with page content. Just read it.

```bash
playwright-cli open https://example.com
# snapshot is returned automatically — contains the full page content as an accessibility tree
```

## Extract with eval

Run JavaScript to pull exactly what you need.

```bash
# Page title
playwright-cli eval "document.title"

# Text from a specific element (using ref from snapshot)
playwright-cli eval "el => el.textContent" e5

# All links on the page
playwright-cli eval "JSON.stringify([...document.querySelectorAll('a')].map(a => ({text: a.textContent.trim(), href: a.href})))"

# Table data
playwright-cli eval "JSON.stringify([...document.querySelectorAll('table tr')].map(row => [...row.cells].map(c => c.textContent.trim())))"

# Product listings
playwright-cli eval "JSON.stringify([...document.querySelectorAll('.product')].map(el => ({
  name: el.querySelector('.title')?.textContent?.trim(),
  price: el.querySelector('.price')?.textContent?.trim(),
  rating: el.querySelector('.rating')?.textContent?.trim()
})))"

# Meta tags (description, og:image, etc.)
playwright-cli eval "JSON.stringify({
  description: document.querySelector('meta[name=description]')?.content,
  ogImage: document.querySelector('meta[property=\"og:image\"]')?.content,
  canonical: document.querySelector('link[rel=canonical]')?.href
})"
```

## Extract across multiple pages

```bash
# Paginated content
playwright-cli run-code "async page => {
  const results = [];
  for (let i = 1; i <= 5; i++) {
    await page.goto(\`https://example.com/results?page=\${i}\`);
    const items = await page.locator('.result-item').allTextContents();
    results.push(...items);
  }
  return JSON.stringify(results);
}"
```

## Wait for dynamic content

Some pages load content via JavaScript after the initial page load.

```bash
# Wait for content to appear
playwright-cli run-code "async page => {
  await page.waitForSelector('.results-loaded');
  return await page.locator('.result').allTextContents();
}"

# Wait for network to settle
playwright-cli run-code "async page => {
  await page.waitForLoadState('networkidle');
}"
```

## Save snapshot to file

```bash
playwright-cli snapshot --filename=page-data.yaml
```
