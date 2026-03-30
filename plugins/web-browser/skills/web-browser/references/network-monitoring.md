# Network Monitoring

## View network traffic

See all requests the page makes (XHR, fetch, assets).

```bash
playwright-cli network
```

## View console output

```bash
playwright-cli console
playwright-cli console warning   # filter by level
```

## Intercept and mock requests

Useful for testing or bypassing API calls.

```bash
# Block images
playwright-cli route "**/*.jpg" --status=404

# Mock an API response
playwright-cli route "**/api/users" --body='[{"id":1,"name":"Alice"}]' --content-type=application/json

# List active routes
playwright-cli route-list

# Remove a route
playwright-cli unroute "**/*.jpg"

# Remove all routes
playwright-cli unroute
```

### URL patterns

```
**/api/users           - Exact path
**/api/*/details       - Wildcard in path
**/*.{png,jpg,jpeg}    - File extensions
**/search?q=*          - Query parameters
```

## Advanced: conditional mocking

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/data', async route => {
    const response = await route.fetch();
    const json = await response.json();
    json.modified = true;
    await route.fulfill({ response, json });
  });
}"
```

## Advanced: capture API responses

```bash
playwright-cli run-code "async page => {
  const responses = [];
  page.on('response', async response => {
    if (response.url().includes('/api/')) {
      responses.push({ url: response.url(), status: response.status() });
    }
  });
  await page.goto('https://example.com');
  await page.waitForLoadState('networkidle');
  return JSON.stringify(responses);
}"
```
