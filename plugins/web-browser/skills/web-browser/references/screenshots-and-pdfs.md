# Screenshots and PDFs

## Screenshots

```bash
# Full page screenshot
playwright-cli screenshot --filename=page.png

# Screenshot of a specific element (by ref)
playwright-cli screenshot e5 --filename=element.png

# Auto-named (timestamped)
playwright-cli screenshot
```

## PDFs

```bash
playwright-cli pdf --filename=page.pdf
```

## Resize viewport before capturing

```bash
playwright-cli resize 1920 1080
playwright-cli screenshot --filename=desktop.png

playwright-cli resize 375 812
playwright-cli screenshot --filename=mobile.png
```
