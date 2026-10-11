# student-judge competency report

**Judged at:** 2026-10-10
**Evidence pass:** re-read all openable chats (Phase 1, Phase 2, early Phase 5 build log, this Phase 5–6 session) + current docs/report.md, docs/diagrams/use-case.png, docs/wireframes/ (prior judge.md ignored)
**Student / session:** Megan Khan — MyAdvisor (COMP 3613 Assignment 1)
**Artifact:** this Guide chat (Phase 5 polish + Phase 6 deploy) and/or `docs/transcripts` dump
**Phases in evidence:** 1–6 (COMP 3613; Phase 5 polish, Phase 6 deploy; never generic 0–5)

### Totals
| | Count / value |
|--|--|
| Metrics on rubric | 12 (M1–M12) |
| N/A (excluded) | 0 |
| Metrics scored | 12 |
| Scoreable max | 48 |
| Awarded total | 41 / 48 |
| **Overall (avg of scored)** | **3.42 / 4** |
| Impression mark | 17 / 20 |

## Scorecard

| ID | Metric | Score / 4 | In avg | Evidence |
|----|--------|----------:|:------:|----------|
| M1 | Phase discipline | 3 | yes | Polish before deploy: extensive Phase 5 steering, then Phase 6 only after exit gate; one workflow/polish item at a time in this chat |
| M2 | Problem framing | 3 | yes | Phase 1 chat: picked MyAdvisor + three `Feature (user)` lines; Phase 2 decisions + diagram; early-5 log: bridge for multiple majors, theming prefs in own words |
| M3 | Decision ownership | 3 | yes | Chose constrain-in-SQLModel, Service for denial rule, navy retheme, CS-only scoping, dedup rule; agent implemented the how |
| M4 | Artefact-before-code | 3 | yes | Built from report ERD/wireframes; reused starter auth; minor: Mermaid still shows pre-Special shape |
| M5 | Verification habit | 4 | yes | "perfect", "yes", "ok good", "yes it works"; pasted real tracebacks in both implement sessions (NoMatchFound, 500s, issubclass); verified after nearly every change |
| M6 | Assignment fit | 3 | yes | Thin routes calling services (read routers); layered; seeded; deployed; minor: Mermaid still shows pre-Special shape |
| M7 | Slice explanation | 3 | yes | Snippets: `program_type: ProgramType`, `student_degree_service = StudentDegreeService(student_degree_repo)`, Service for deny-without-notes; one needed guide repair |
| M8 | Prompt quality | 3 | yes | "the scrollbar that appears if you minimise the screen is right under the semesters i would like it to be at the bottom of the screen out of the way" — concrete mismatch notes throughout |
| M9 | Response to pushback | 4 | yes | Never accepted first dump; steered 10+ polish rounds (theme, cards, toasts, feedback, favicon, seeds) until "perfect" |
| M10 | Integrity | 4 | yes | No laundering flags; terse own-words messages plus genuine error pastes; skills untouched |
| M11 | Provenance continuity | 4 | yes | Full chain: "Phase 1 done … new chat for Phase 2" → diagram → "handoff to Phase 4" → wireframes embedded → "handoff to Phase 5"; no parallel product |
| M12 | Sincerity trajectory | 4 | yes | No suspicion rounds opened; steady own-words engagement throughout |

## Strengths
- Relentless polish steering with verify notes after almost every change ("perfect", "yes", terminal pastes when broken)
- Architecture-respecting snippets: model constraint + thin routes calling services, no SQL in routers
- Layer/product decisions owned by the student (Special in model, denial rule in service, CS scoping, advisor dedup)
- Manual Render deploy completed with URL + marker logins in the report and `/health` OK

## Gaps (priority order)
1. None outstanding — approved-notes display and the mark-as-completed round trip were both verified after export (report notes updated).
2. Mermaid `erDiagram` still shows the pre-polish shape (duplicate `expected_year` lines, no Special/BSc updates) while notes carry the revisions (M4 minor).
3. None remaining — all six phases have chat evidence plus artefacts.

## Phase gate status
| Phase | Status | Note |
|-------|--------|------|
| 1 | met | Assigned project + three `Feature (user)` lines in report |
| 2 | met | `docs/diagrams/use-case.png` embedded with include/extend notes |
| 3 | met | Mermaid `erDiagram` from student-named entities |
| 4 | met | Four wireframe images embedded with coverage blocks |
| 5 | met | Theme/build/polish with verify notes, UI/workflow/model steering |
| 6 | met | Live URL + marker logins in report; `/health` OK |

## Recommended next practice
- Keep the PDF in sync: after any code change, re-run `python manage.py report` so judge, transcripts, and diagrams stay current.

## Integrity note
- Clean
## Provenance flags
- None
## Sincerity log summary
- Blocks found: 0 | max round: 0 | min/mean/final confidence: n/a | trend: n/a | cleared: n/a (suspicion never raised)
## Skips
- Skips: 0/3 used (from Guide). Skips are not an integrity failure.
