# Frames Cross-Chat Continuity Protocol

This protocol exists to prevent scope drift when a long ChatGPT conversation ends or a new chat is opened.

## Source-of-truth order

Use this order whenever sources disagree:

1. Current repository contents and exact build/evidence artifacts.
2. `PROJECT_STATE.md`.
3. Current active branch/workflow/run state.
4. Explicit instructions from the user in the current conversation.
5. Older chat/project summaries and remembered context.

Never let an older summary override newer repository evidence.

## Required startup procedure

Before continuing Frames engineering in a new conversation:

1. Read repository-root `PROJECT_STATE.md`.
2. Read repository-root `CONTINUITY_PROTOCOL.md`.
3. Verify the active branch and latest relevant GitHub Actions run.
4. Inspect the latest evidence if a certification claim is involved.
5. Resume the exact `Active milestone` and `Current objective` from `PROJECT_STATE.md` unless the user explicitly changes direction.

Do not ask the user to reconstruct several hours of prior work when the repository can resolve the state.

## Scope-lock rule

Once an active milestone is defined, do not silently pivot to a different architecture train, roadmap phase, feature family, or release target.

A scope change is allowed only when:

- the current milestone is completed and the next milestone is explicitly defined;
- repository evidence proves the current approach must change;
- the user explicitly changes priorities.

When a scope change occurs, update `PROJECT_STATE.md` in the same work session.

## Claim discipline

Do not describe internal markers as equivalent to user-visible functionality.

Examples:

- A GUI phase marker does not prove a usable desktop.
- A green GitHub workflow does not prove certification if runtime evidence is absent.
- A generated/mockup image does not prove what Frames actually rendered.
- A build artifact is not the same as an artifact booted and visually verified.

For user-visible GUI claims, the exact candidate must be booted and its actual framebuffer evidence inspected.

## Artifact identity rule

When handing a physical-test ISO to the user:

- identify the exact workflow run and commit;
- provide the ISO SHA-256;
- ensure the screenshot/evidence came from that exact ISO hash;
- never reuse an older ISO while describing newer code changes;
- do not provide an ISO if the corresponding fail-closed visual/runtime gate failed.

## Automatic engineering progression

Frames work should continue automatically through the active objective:

- Failure -> inspect evidence -> make narrow repair -> rerun.
- Success -> independently validate evidence -> update `PROJECT_STATE.md` -> move to the next defined milestone.

Do not stop merely to report a routine failure or intermediate pass.

## Handoff update requirements

Update `PROJECT_STATE.md` whenever any of these changes:

- certified baseline;
- active branch;
- active milestone;
- exact next repair/action;
- decisive test result;
- approved artifact/hash;
- safety boundary;
- next milestone.

The handoff should state both what is proven and what is NOT proven.

## Full GUI-specific guardrail

For the current Full Interactive Desktop GUI milestone, no candidate may be called a full GUI or given to the user as such unless the exact booted candidate visibly proves multiple native application windows and passes the dedicated visual verifier. The old dashboard/home-shell ISO is explicitly excluded from this classification.
