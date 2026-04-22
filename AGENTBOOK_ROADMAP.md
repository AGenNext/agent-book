# Autonomyx AgentBook Product Architecture Roadmap

## Positioning
**Autonomyx AgentBook** is an **Enterprise Knowledge Workspace** focused on grounded answers, reusable intelligence, and action-ready outputs.

## Current-to-Target Module Mapping

| Current module | Target AgentBook module | Status |
|---|---|---|
| Notebook CRUD | Workspace lifecycle | In progress (UI terminology rebranded to workspace) |
| Sources | Source ingestion & management | Reused |
| Notebook chat + source refs | Grounded chat with citations | Reused and promoted |
| Notes | Notes and evidence capture | Reused |
| Transformations | Artifact Studio | Repositioned |
| Session history + updates | Timeline / memory continuity | Partial scaffolding |
| Settings + auth | Governance foundations | Partial scaffolding |

## Domain model expansion plan

Existing data model already includes: `Notebook`, `Source`, `Note`, `ChatSession`, `ChatMessage`.

Planned extension entities for enterprise workflows:
- `WorkspaceMember`
- `Citation`
- `EvidenceCard`
- `SavedAnswer`
- `Artifact`
- `ArtifactVersion`
- `Task`
- `Comment`
- `TimelineEvent`
- `AuditEvent`

## API evolution plan

1. Add `/workspaces` alias routes on top of existing notebook API.
2. Add workspace-level tabs endpoints (`/timeline`, `/tasks`, `/members`, `/activity`, `/artifacts`).
3. Add explicit citation payload in all AI answer responses.
4. Add insufficient-evidence status in chat response contract.
5. Add role-guard middleware for owner/editor/viewer actions.

## Batch 1 (implemented in this change set)
- Rebrand primary UI to Autonomyx AgentBook.
- Introduce workspace route aliases (`/workspaces`, `/workspaces/[id]`).
- Add workspace detail tab architecture (Overview, Chat, Sources, Notes, Artifacts, Timeline, Tasks, Activity, Members, Settings).
- Add artifact, timeline, tasks, members, and governance view scaffolding.
- Add workspace duplication action.
- Update README positioning and messaging baseline.

## Batch 2 (next)
- Backend table + router additions for members, timeline, tasks, artifacts.
- Explicit citations persistence model.
- Save answer as note/evidence card relation model.
- Workspace activity stream and audit event log ingestion.

## Batch 3 (later)
- Connectors: Google Drive, SharePoint, Confluence, Slack, Jira, GitHub.
- Approval/publish workflows.
- Usage analytics and quality dashboards.
