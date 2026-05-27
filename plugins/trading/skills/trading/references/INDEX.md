# Trading Skill Reference Index

Reference files contain tribal knowledge and non-obvious patterns for the `ib_async` library against Interactive Brokers. For discoverable details, read the ib_async docs or source.

All code runs via: `cd ${CLAUDE_PLUGIN_ROOT} && uv run python3 -c "..."`

Dependencies are in `${CLAUDE_PLUGIN_ROOT}/pyproject.toml` — `uv run` auto-installs them.

## Connection & Session

| connection.md

## Market Data & Pricing

| market-data.md

## Options: Contracts, Chains, Strikes

| options.md

## Orders: Placement, Combos, Brackets

| orders.md

## Strategies: Iron Butterfly, Iron Condor

| strategies.md

## Positions, Portfolio, Closing

| positions.md

## Box Spreads

| box-spreads.md

## Portfolio Greeks & Risk

| portfolio-greeks.md

## Economic Calendar & Pre-Trade Checks

| economic-calendar.md

## Position Management: Rolling, Adjustments, Exits

| position-management.md
