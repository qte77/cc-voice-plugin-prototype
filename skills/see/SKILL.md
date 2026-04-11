---
name: see
description: Capture and analyze screen content using vision models. Use for pair programming, UI review, or sharing visual context with Claude.
compatibility: Designed for Claude Code
metadata:
  allowed-tools: Bash, Read, Write
  argument-hint: [region|full] [--local] [--describe]
  context: inline
  stability: research
---

# /see

Capture and analyze screen content using vision models.

## Usage

- `/see` — capture full screen, send to Claude Vision API
- `/see active` — capture active window only
- `/see --local` — use local VLM (Moondream2) instead of API
- `/see --describe` — return text description only (no image)

## Implementation

```bash
python -m cc_vlm $ARGUMENTS
```

## Configuration

Edit `.cc-voice.toml` in project root:

```toml
[vlm]
engine = "auto"          # "claude" | "moondream" | "auto"
max_dimension = 1568     # longest edge in pixels
jpeg_quality = 85
region = "full"          # "full" | "active" | custom rect
```

Environment overrides: `CC_VLM_ENGINE`, `CC_VLM_MAX_DIMENSION`, `CC_VLM_REGION`.

## Status

Research — architecture defined in ADR-0001. No implementation yet.
