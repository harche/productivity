# Filling Forms

## Basic flow

```bash
playwright-cli open https://example.com/form
playwright-cli snapshot
# identify form fields from snapshot refs

playwright-cli fill e1 "user@example.com"     # email
playwright-cli fill e2 "password123"           # password
playwright-cli click e3                        # submit button
```

## Form element types

```bash
# Text input
playwright-cli fill e1 "some text"

# Select dropdown
playwright-cli select e5 "option-value"

# Checkbox
playwright-cli check e7
playwright-cli uncheck e7

# File upload
playwright-cli upload ./document.pdf

# Textarea (same as fill)
playwright-cli fill e10 "multi-line\ntext content"
```

## Search forms

```bash
playwright-cli open https://example.com
playwright-cli type "search query"
playwright-cli press Enter
```

## Multi-step forms

```bash
# Step 1
playwright-cli fill e1 "John"
playwright-cli fill e2 "Doe"
playwright-cli click e3   # Next

# Step 2 — new snapshot, new refs
playwright-cli fill e1 "123 Main St"
playwright-cli fill e2 "City"
playwright-cli select e3 "CA"
playwright-cli click e4   # Next

# Step 3 — review and submit
playwright-cli click e1   # Submit
```

## Handling dialogs

Some forms trigger confirmation dialogs.

```bash
playwright-cli click e5              # triggers dialog
playwright-cli dialog-accept         # click OK
playwright-cli dialog-dismiss        # click Cancel
playwright-cli dialog-accept "yes"   # type and confirm
```

## Drag and drop

```bash
playwright-cli drag e2 e8   # drag element e2 onto e8
```
