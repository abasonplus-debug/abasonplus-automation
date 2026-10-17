# AbasonPlus automation audit — 2026-10-17

Audit scope: repository code, editorial/design rules, GitHub workflows, active Make routing, connected publishing accounts, scheduled ChatGPT research/audit tasks and Free-plan controls.

## Implemented and saved

- Unified operational dates and daily publishing keys to Europe/Berlin, including daylight-saving changes.
- Added per-platform daily duplicate guards for WordPress, YouTube and Facebook; retained Instagram's existing daily guard. The already-published 17 October has an explicit migration hold so the new keys do not permit another post that day.
- Isolated publishing failures in Make so one platform's uploader failure does not halt other branches. Inspect module errors/warnings as well as the overall execution status. Reservations remain in place after ambiguous failures; investigate before retrying.
- WordPress now requires a fresh current-day editorial item by default. Missing/already-published material produces a clean hold, never an automatic fallback to old catalogue content. Stale preview output is removed.
- WordPress publication verification now checks exact slug and normalized title, published status, expected HTTPS host and a fresh publication timestamp.
- Added shared official-source URL, safe article HTML and social-copy length validation. Reject credential-bearing/spoofed source URLs, executable HTML and embedded Post-by-Email control directives.
- Fixed the YouTube description hashtag check; validate final Instagram caption and YouTube metadata after credits and hashtags are added.
- Preserved the approved design: at least 120 px bold Bengali text directly on relevant photographs; no text box, border, outline, shadow or overlay; small bottom-right logo when available. Quality gates hold unsuitable output.
- Removed automatic creative generation from code-change checks. Full media previews remain explicit manual actions. Retired completed one-time TikTok/Instagram publishing workflows to prevent reuse of old approval.
- Updated the current specification, editorial rules and setup documentation to remove contradictory old timing, styling and account-status instructions.
- Updated the scheduled research and audit instructions. Audit runs at 11:00 Europe/Berlin and checks warning/error cycles, freshness, duplicate guards and Free-plan limits.

Implementation commits:
- ee3e50109aa33984d5ec22e9b63a7451ba45cb76
- 9a401edc53528225319e2e75f2fafec33d36534e
- 19defe8d09313b47d630e12447758ef98e636947

## Verification

- Ten regression tests passed, including Berlin date boundaries, source spoofing, unsafe HTML, copy limits, WordPress identity/freshness and workflow publishing contracts.
- Latest GitHub Safe Code Validation passed: https://github.com/abasonplus-debug/abasonplus-automation/actions/runs/39071285433
- Latest WordPress Email Preview Only passed: https://github.com/abasonplus-debug/abasonplus-automation/actions/runs/39071285477
- Live Make approval-gate regression passed for all four routes: video, WordPress email, reviewed TikTok and Instagram. All four unapproved payloads stopped at the webhook; no publisher or reservation module executed.
- Gate workflow: https://github.com/abasonplus-debug/abasonplus-automation/actions/runs/39071260217
- Main Make scenario 7968544 was read back active with no configuration issues and healthy connections after editing.
- Both TikTok and Instagram @abasonplus accounts were active with no reconnection requirement at inspection.
- Research and audit tasks were read back enabled with Europe/Berlin schedules.
- No new image/video was generated and no public post was sent during this audit. Existing earlier publications were inspected instead.

## Current schedule and cost controls

All times Europe/Berlin:
- 05:00 — research task
- 07:35 — source monitoring
- 08:20 — WordPress publishing
- 08:45 — Facebook, YouTube and Instagram publishing
- 11:00 — daily audit

Make was confirmed Free, automatic credit purchasing disabled, 160 of 1,000 monthly credits used and 840 remaining at the final check. Next reset: 2026-11-12 22:55 UTC. No paid service was enabled.

TikTok remains a separate reviewed, per-video manual-dispatch publishing route with no daily cron. Each exact completed video needs the applicable creator review and posting choices; old approval is not reused.

## Operational limits

Code checks and rejection gates passed; this is not a guarantee that every future external service request will succeed. The next scheduled production run has not yet occurred. GitHub scheduling can be delayed; missing fresh content, failed quality checks, expired connections or exhausted free quotas must hold publication and be surfaced in the audit. Visual automation checks cannot guarantee aesthetic quality or perfect subject matching.

Do not expose webhook URLs, tokens or the private WordPress Post-by-Email recipient in reports or repository files.
