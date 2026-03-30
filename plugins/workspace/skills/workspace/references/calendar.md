# Calendar Reference

Full command reference for Google Calendar via `gog calendar`.

## List Events

```bash
# List upcoming events (default: primary calendar, max 10)
gog calendar list [--max=10]

# List from all calendars
gog calendar list --all

# Filter by time range
gog calendar list --today
gog calendar list --tomorrow
gog calendar list --week
gog calendar list --days=7
gog calendar list --from="2026-03-01" --to="2026-03-15"

# List from a specific calendar
gog calendar list <calendarId>

# Search events by text
gog calendar list --query="standup"
```

## Search Events

```bash
gog calendar search "<query>" [--max=25] [--today] [--week] [--from=STRING] [--to=STRING]
```

## List Calendars

```bash
gog calendar calendars
```

## Get Event Details

```bash
gog calendar event <calendarId> <eventId>
```

## Create Events

**Always confirm with the user before creating events.**

```bash
# Timed event
gog calendar create primary --summary "Team Meeting" \
  --from "2026-03-03T10:00:00" --to "2026-03-03T11:00:00"

# With attendees and location
gog calendar create primary --summary "Review" \
  --from "2026-03-03T14:00:00" --to "2026-03-03T15:00:00" \
  --attendees "alice@example.com,bob@example.com" \
  --location "Room 42" --send-updates all

# With Google Meet
gog calendar create primary --summary "Sync" \
  --from "2026-03-03T09:00:00" --to "2026-03-03T09:30:00" \
  --with-meet

# All-day event
gog calendar create primary --summary "Team Offsite" \
  --from "2026-03-10" --to "2026-03-12" --all-day

# Recurring event
gog calendar create primary --summary "Weekly Standup" \
  --from "2026-03-03T09:00:00" --to "2026-03-03T09:15:00" \
  --rrule "RRULE:FREQ=WEEKLY;BYDAY=MO"

# With reminders
gog calendar create primary --summary "Deadline" \
  --from "2026-03-15T17:00:00" --to "2026-03-15T17:30:00" \
  --reminder popup:30m --reminder email:1d
```

## Update Events

**Always confirm with the user before modifying events.**

```bash
# Reschedule
gog calendar update primary <eventId> \
  --from "2026-03-04T10:00:00" --to "2026-03-04T11:00:00"

# Change title/description
gog calendar update primary <eventId> --summary "New Title" --description "Updated notes"

# Add attendees (preserving existing)
gog calendar update primary <eventId> --add-attendee "charlie@example.com"

# Update recurring event (single instance, future, or all)
gog calendar update primary <eventId> --scope=single --original-start="2026-03-10T09:00:00"
```

## Delete Events

```bash
gog calendar delete primary <eventId>
```

## RSVP / Respond

```bash
gog calendar respond primary <eventId> --status=accepted
gog calendar respond primary <eventId> --status=declined --comment="Conflict"
gog calendar respond primary <eventId> --status=tentative
```

## Free/Busy and Conflicts

```bash
# Check free/busy for calendars
gog calendar freebusy primary,other@example.com --from="2026-03-03T08:00:00" --to="2026-03-03T18:00:00"

# Find scheduling conflicts
gog calendar conflicts --today
gog calendar conflicts --week
gog calendar conflicts --days=7
```

## Focus Time and Out of Office

```bash
# Focus time block
gog calendar focus-time --from="2026-03-03T14:00:00" --to="2026-03-03T16:00:00" \
  --summary="Deep Work" --auto-decline=all --chat-status=doNotDisturb

# Out of office
gog calendar out-of-office --from="2026-03-10" --to="2026-03-14" --all-day \
  --summary="Vacation" --decline-message="I'm on vacation, back March 14"
```

## Working Location

```bash
gog calendar working-location --from="2026-03-03" --to="2026-03-03" --type=home
gog calendar working-location --from="2026-03-04" --to="2026-03-04" --type=office --working-office-label="HQ"
```

## Workspace Users and Teams

```bash
# List workspace users (use their email as calendar ID)
gog calendar users

# Show events for all members of a Google Group
gog calendar team group@example.com --today
```
