<!-- student-build:skill-integrity
status: pass
root: e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb
expected_root: e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb
mismatches: none
-->

# COMP 3613 Assignment 1

Draft this file with the Guide. **Update it after every phase milestone** before you pause. The use-case diagram is a UML PNG at `docs/diagrams/use-case.png`, linked from this file as `diagrams/use-case.png` (path relative to `docs/report.md`). The model diagram is Mermaid. **Embed wireframe images** as `wireframes/<file>` (files live in `docs/wireframes/`).

Do not put your student ID in this file if you will commit it. The PDF cover adds your name and ID at export time.

## Assigned project

MyAdvisor — students track degree progress, plan semester course selections, and obtain approval from an administrator / advisor.

## Three workflows

### 1.

Select degree and track progress (Students)

### 2.

Add/remove courses for each semester (Students)

### 3.

Approve/deny courses for each semester (Admin/Advisor)

## Use case diagram

![Use case diagram](diagrams/use-case.png)

Phase 2 notes:

- **«include»:** Track progress always includes Select degree. Seek approval always includes Notify student (pending). Approve/deny courses always includes Notify student (approved or denied, including push).
- **«extend»:** Seek approval extends Add/remove courses for each semester — only when the student is sure about that semester’s list. Add/remove can repeat without seeking approval. Approval is still required for each semester.
- **Shared across actors:** none of the named Phase 1 use cases. Notify student is a nested step (no extra actor lines), included from Seek approval and from Approve/deny.
- **Added from the edge-case answer:** Seek approval (Students); Notify student for pending / approved / denied (toast plus push).
- **Deliberate gap:** starter login/session is supporting behaviour, not a named use case.

## Model diagram

First draft. Update this section in Phase 5 when polish revises the model, and note what changed.

```mermaid

erDiagram
    STUDENT ||--o{ COURSE_SELECTION : enrolls_in
    STUDENT ||--o{ STUDENT_DEGREE : pursues
    DEGREE ||--o{ STUDENT_DEGREE : selected_as
    DEGREE ||--o{ DEGREE_REQUIREMENT : requires
    COURSE ||--o{ DEGREE_REQUIREMENT : satisfies
    COURSE ||--o{ COURSE_SELECTION : selected_as
    SEMESTER ||--o{ COURSE_SELECTION : contains
    ADVISOR ||--o{ COURSE_SELECTION : reviews

    STUDENT {
      int student_id PK
      int user_id FK, UK
      string first_name
      string last_name
      string email
    }

    STUDENT_DEGREE {
      int student_id PK, FK
      int degree_id PK, FK
      string program_type
    }

    ADVISOR {
      int advisor_id PK
      string first_name
      string last_name
      string email
    }

    DEGREE {
      int degree_id PK
      string degree_name
      int total_credits_required
      string faculty_name
      int expected_years
      int expected_years
    }

    COURSE {
      string course_code PK
      string course_name
      string description
      int credits
    }

    SEMESTER {
      int semester_id PK
      string semester_name
      int semester_year
      date start_date
      date end_date
    }

    DEGREE_REQUIREMENT {
      int requirement_id PK
      int degree_id FK
      string course_code FK
      string requirement_type
      string minimum_grade
      int expected_year
      int expected_semester
      int expected_year
      int expected_semester
    }

    COURSE_SELECTION {
      int selection_id PK
      int student_id FK
      string course_code FK
      int semester_id FK
      string status
      int reviewed_by FK
      string notes
    }
```

Phase 3 notes:

- Students can pursue multiple degrees, including majors, minors, and specials; `STUDENT_DEGREE.program_type` classifies each student-degree association as Major, Minor, or Special.
- A course is selected by many students across many semesters through CourseSelection, which records the semester, enrollment status, and advisor review.
- DegreeRequirement ties a degree to a course and records the rule that must be satisfied, such as a minimum grade or requirement type.
- The relationship between Advisor and CourseSelection is review-based: an advisor may review many course selections, while each selection may be reviewed by one advisor.
- Phase 4 revision: `DEGREE.faculty_name` reflects the faculty grouping shown in the degree-selection screens; `COURSE_SELECTION.notes` stores notes attached to a student's selected course.
- Phase 5 model refinement: replaced `STUDENT.degree_id` with the `STUDENT_DEGREE` bridge so a student can pursue multiple majors and minors; `STUDENT.user_id` links each student profile to one registered account.

## Wireframes

### Student degree tracking and course planning — desktop

![Student degree tracking and course planning, desktop](wireframes/Desktop%20version%20wireframe.png)

<!-- student-build:wireframe-coverage
use_case: Track progress
image: docs/wireframes/Desktop version wireframe.png
covered: yes
-->
<!-- student-build:wireframe-coverage
use_case: Select degree
image: docs/wireframes/Desktop version wireframe.png
covered: yes
-->
<!-- student-build:wireframe-coverage
use_case: Add/remove courses for each semester
image: docs/wireframes/Desktop version wireframe.png
covered: yes
-->
<!-- student-build:wireframe-coverage
use_case: Seek approval
image: docs/wireframes/Desktop version wireframe.png
covered: yes
-->

### Advisor course review — desktop

![Advisor course review, desktop](wireframes/Desktop%20version%20wireframe%202.png)

<!-- student-build:wireframe-coverage
use_case: Approve/deny courses for each semester
image: docs/wireframes/Desktop version wireframe 2.png
covered: yes
-->

### Student degree tracking and course planning — mobile

![Student degree tracking and course planning, mobile](wireframes/Mobile%20version%20wireframe.png)

### Advisor course review — mobile

![Advisor course review, mobile](wireframes/Mobile%20version%20wireframe%202.png)

<!-- student-build:wireframe-coverage
use_case: Notify student
image: docs/wireframes/Desktop version wireframe 2.png
covered: yes
-->

### Coverage note

The student screens show pending submission and approved/denied semester statuses. These visible outcomes cover `Notify student`; toast/push delivery is not depicted in the wireframes.

`python manage.py report` also embeds any PNG/JPG still missing from `docs/wireframes/`.

### Desktop version wireframe 2

![Desktop version wireframe 2](wireframes/Desktop version wireframe 2.png)

### Desktop version wireframe

![Desktop version wireframe](wireframes/Desktop version wireframe.png)

### Mobile version wireframe 2

![Mobile version wireframe 2](wireframes/Mobile version wireframe 2.png)

### Mobile version wireframe

![Mobile version wireframe](wireframes/Mobile version wireframe.png)

## Theming

- **Colors:** deep navy background, tech blue, teal, and white accents.
- **Type:** sans serif (Manrope).
- **Tone:** modern and techy; not a university portal.
- **Logo / wordmark:** plain `MyAdvisor` text with a subtle tech glow.
- **Applied to:** public landing, login, registration, and authenticated shell.
- **Visual refinement:** deep navy background with blue/teal glows, dark surfaces for cards and forms, centered top-bar wordmark, warning alerts in pale blue to avoid orange UI accents.
- **Verification:** student requested modern techy deep-navy retheme; follow-up polish made the semester 3-dot menu visible and restyled all popups for the dark theme. Student verified: overall look great, dots visible, popups clean — perfect. Replaced the tab icon with a sleek black square `MyA` SVG favicon. Made the centered top-bar `MyAdvisor` wordmark clickable back to Home (admin/student aware). Student verified: click goes home — yes.

## Implementation notes

One named workflow at a time. Include verify notes and polish / model revisions (Phase 5). Do not treat the first build as final.

- **Role provisioning:** public registration creates Student accounts; Admin/Advisor access remains seeded for testing and is not selectable during public registration. Bob's seeded `current_year` is Year 3 (fresh profiles start there; existing default Year 1 profiles migrate up). All degrees now sit under Faculty of Science and Technology; any legacy Faculty of Science rows migrate on seed so that faculty disappears. Degrees were renamed to BSc Computer Science (Major) and BSc Mathematics (Minor), with duplicate-name merges keeping the assigned degree. The old BSc Computer Science catalog entry was retired — its courses (COMP1600, COMP1601, COMP2603, COMP2611, COMP3613) already live as requirements on BSc Computer Science — as was the colliding BSc Mathematics catalog entry, leaving one degree per name.

### Workflow 1 — Select degree and track progress (Students)

- **Workflow 1 refinement:** assigned Major/Minor/Special degree cards appear on the student home page. Clicking a card opens a degree action page with `Track degree` and `Plan semester`. Tracking a degree opens `Completed courses` and `Remaining courses` actions. Students may record previously completed courses and add past semesters; a grade is not required. Completed courses shows code-only entries grouped by collapsible `Year 1`, `Year 2`, etc. sections and horizontal collapsible semester columns; clicking a code opens course details and a delete action that removes only the student's completion record. Every semester has an `Add course` dialog and a `Delete semester` action. Deleting a semester removes this student's completed entries and deletes the shared semester row only when no selections reference it. The `Add extra semester` dialog appears at the end of page content and asks for a `Year N` label and one of three semester radio choices; the label maps to a real calendar year for stored semester dates. Remaining courses shows the degree roadmap for `DEGREE.expected_years`, with three horizontal semester columns per year. Uncompleted `DEGREE_REQUIREMENT` rows appear in their expected term, separated into Core and specific Elective courses; Semester 3 is marked optional. Completed courses are removed from the roadmap. Course codes open an information dialog, and no add/delete controls appear on this page. Degree requirements without an expected term are outside the roadmap and should be assigned during curriculum setup. The authenticated sidebar stays viewport-height and sticky while long page content scrolls. Student verified this track-progress flow through polish rounds — perfect.
- **Completed-courses seed (bob):** Year 1 Sem 1: COMP1600, COMP1601, INFO1600, MATH1150, FOUN1101; Year 1 Sem 2: COMP1602, COMP1604, INFO1601, FOUN1301; Year 1 Sem 3: COMP1603; Year 2 Sem 1: COMP2601, COMP2602, COMP2605, COMP2611, MATH2250; Year 2 Sem 2: COMP2604, COMP2606, INFO2602, INFO2604, FOUN1105; Year 2 Sem 3: COMP2603. Seeded as `completed` selections across 2023–2024 semesters on every `seed`/`init --no-drop`.
- **CS-only scoping:** those 21 courses plus CSCI110 are seeded as Computer Science (Major) `DEGREE_REQUIREMENT` rows (Core), and the Completed view now filters by the viewed degree's requirements — so the history shows only under the Computer Science degree, not Mathematics. Adding a completed course under a degree also tags it as that degree's requirement. The extra-semester year mapping is scoped per degree too, and reusing a shared semester row with no selections of yours counts as added instead of a false duplicate. The history page lists completed semesters plus empty shells only — planner semesters (e.g. an approved planned course) live under Plan, not history. Adding a semester reports `already exists` when that degree lists it, `already in use — manage its courses under Plan` when your other selections occupy that slot, and `added` otherwise. Student verified: CS history only under CS, Math add works — good.
- **Year 3 roadmap seed (CS):** Year 1 Sem 1/2 and Year 2 Sem 1/2 have no remaining courses (all completed). Year 3 Sem 1 Core: COMP3602, COMP3603, COMP3991; Electives: COMP3605, COMP3606, COMP3607, COMP3612, COMP3613, INFO2605, INFO3600, INFO3605. Year 3 Sem 2 Core: COMP3601, INFO3604; Electives: COMP3608, COMP3609, COMP3610, COMP3611, COMP3612, INFO3606, INFO3607, INFO3608, INFO3611 (all 3 credits). COMP3612 appears in both semesters, so it holds two requirement rows; shared catalog titles were aligned to these names. Student verified: Year 3 lists match — good. BSc Mathematics gets a small seeded roadmap (Year 1: MATH3273 Core, MATH3277 Core; Year 2: MATH3278 Elective, MATH2210 Core; anything else pruned). Student verified: all four show — good.
- **Remaining courses roadmap:** added `DEGREE.expected_years` and `DEGREE_REQUIREMENT.expected_year` / `expected_semester`. The Remaining page groups unmet course requirements into Core and Elective sections for each planned term, excludes courses with completed student selections, and labels the third semester optional. Existing databases receive additive defaults; seed data is now the Year 3 BSc Computer Science roadmap plus the four-course BSc Mathematics roadmap. Student verified both roadmaps — good.

<!-- student-build:code-check
workflow: Select degree and track progress
form: choice
layer: model
architecture_ok: yes
implement_confidence: 0.85
passed: yes
note: Student chose to constrain Special in SQLModel so Major/Minor/Special stay consistent.
-->
<!-- student-build:code-check
workflow: Select degree and track progress
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.65
passed: partial
note: Student first set program_type to a Literal alias; Guide corrected to str with pattern because Literal breaks SQLModel table mapping.
-->
<!-- student-build:code-check
workflow: Select degree and track progress
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.70
passed: yes
note: Corrected STUDENT_DEGREE.program_type to str with Major/Minor/Special pattern so Special validates without issubclass error.
-->
<!-- student-build:code-check
workflow: Select degree and track progress
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.85
passed: yes
note: Student completed thin degree_actions_view by constructing StudentDegreeService from the repository.
-->
- **Workflow 1 polish:** moved `MyAdvisor` from the sidebar into the centered top bar; removed the inner horizontal scrollbar on Completed courses so semester columns wrap and only page scroll remains, with single-column stacking on small screens; made `Delete semester` discrete with muted small text; added `Special` as a `STUDENT_DEGREE.program_type` alongside Major and Minor and updated degree-card copy; made semester cards equal height so adding a course no longer leaves uneven cards, with collapsed semesters shrinking to header size. Student verified: centered wordmark, no inner scroll, discrete delete, Special type, even cards with shrinking collapsed state — perfect.

<!-- student-build:code-check
workflow: Select degree and track progress
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.70
passed: partial
note: Guide wired degree_id through the completed view and add action after the student hit the missing-arg error.
-->

### Workflow 2 — Add/remove courses for each semester (Students)

- **Plan semester decisions:** registration collects the student's current year of study. The picker shows only three plain options (Semester 1, 2, and 3) for that registered academic year; existing profiles default to Year 1. Selecting an option opens a separate semester detail page with courses, Add course fields, and Submit for approval. While a semester is pending advisor review, students cannot add, edit, or remove courses; editing reopens after approval or denial. Re-submitting a course already in the same semester shows a warning toast that it is a duplicate.
- **Plan semester implementation:** enabled the degree action link and split planning into a picker with exactly three semester buttons for the student's registered current year and a separate selected-semester detail page. Course rows have a larger three-dot menu with Edit and Remove actions. The Add course button opens a modal with course fields. Course additions create shared catalog entries and student selections; duplicate attempts and pending locks show warning toasts. Submitting selected courses changes them to pending, and pending semesters hide editing/submission controls. Editing course details updates the shared `COURSE` catalog record; Remove deletes only this student's selection. Registration collects first/last name and current year; an additive schema migration defaults existing profiles to Year 1. Student verified the picker-to-detail flow through use — good.

<!-- student-build:code-check
workflow: Plan semester
form: choice
layer: service
architecture_ok: yes
implement_confidence: 0.75
passed: yes
note: Student chose Service to coordinate the pending lock and duplicate-course outcome.
-->
<!-- student-build:code-check
workflow: Plan semester
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.70
passed: yes
note: Student added a composite uniqueness constraint for student, course, and semester.
-->
<!-- student-build:code-check
workflow: Plan semester
form: snippet
layer: repository
architecture_ok: yes
implement_confidence: 0.55
passed: partial
note: Student attempted repository reads/writes; Guide corrected the Semester/Degree imports and degree scoping before continuing.
-->
<!-- student-build:code-check
workflow: Plan semester
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.70
passed: yes
note: Student route loads planner data through SemesterPlanService using the signed-in user and degree ids.
-->
- **Plan semester polish:** Submit now stays visible for denied semesters and resubmits denied plus selected courses so students do not need delete-plus-add to bring it back; removed the per-course Pending badge so only the top `Pending advisor approval` shows. Student verified: submit reappears correctly, Pending only at top — perfect.
- **Mark as completed:** any planned or approved semester moves into completed history with one button — no requirement prerequisite, and each moved course is tagged as that degree's requirement so it stays under that degree. Completed courses leave Remaining automatically and become read-only under Plan (managed under Track degree). Student verified the full round trip — yes.

### Workflow 3 — Approve/deny courses for each semester (Admin/Advisor)

- **Advisor workflow decision:** the existing seeded `admin` login also acts as Advisor and links to one Advisor profile. Review actions apply to the semester's submitted courses as a group, following the advisor wireframe. A denial requires an explanation; the Advisor's notes are saved with the selections and shown to the student on the semester page.

<!-- student-build:code-check
workflow: Approve/deny courses for each semester
form: mcq
layer: service
architecture_ok: yes
implement_confidence: 0.80
passed: yes
note: Student chose Service for the deny-without-notes rejection.
-->
<!-- student-build:code-check
workflow: Approve/deny courses for each semester
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.75
passed: yes
note: Student kept COURSE_SELECTION.notes as the denial-explanation field.
-->
<!-- student-build:code-check
workflow: Approve/deny courses for each semester
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.80
passed: yes
note: Student kept advisor_decide_semester_action thin by constructing repository plus service and calling decide_semester.
-->
- **Advisor review verified:** `/admin/advising` groups pending semesters with submitted courses; denial requires notes and surfaces them to the student semester page. Student verified: approve works, deny without notes shows the error, deny with notes updates the student page — yes it works.
- **Advisor dedup:** students with two degrees now appear for approval under one degree only (their Major, else first assigned), since plan semesters are shared across degrees; the decision still shows on the student's side under each degree. Student verified: single listing, visible under both degrees — good.

### Cross-cutting polish

- **Toast polish verified:** advisor `Semester approved / denied` alerts and all success toasts auto-dismiss after about four seconds; removed the student `Needs attention` warning popup so warnings no longer show as a toast box; removed per-course Approved/Denied/Pending badges so only the top semester status shows with one persistent advisor-feedback line above the course list (shown for approved semesters too, not just denied). Student verified: toasts vanish, warning box gone, feedback stays above the list — yes; approved-notes display verified too — yes.

## Deployed app

Phase 6. Public Render URL (not localhost). Markers open this to mark the three workflows.

https://myadvisor-choc.onrender.com

## Logins

Every account a marker needs, including extra users you added. Starter accounts:

- bob / bobpass — student
- admin / adminpass — advisor (admin)

## YouTube URL

https://youtu.be/JIegQTHd_bo

## GitHub

https://github.com/megankhan1/comp3613a1

## Agents used

- Cursor — Phases 1–2
- GitHub Copilot Agent — Phases 3–5
- OpenCode — Phase 5 polish, Phase 6 deploy, report build

## Session transcripts

Filled when the Guide builds the report: the agent writes chat markdown into `docs/transcripts/`; `python manage.py report` packages them.

Guide packaged **6** chat(s) in `docs/transcripts/` (and `docs/transcripts.zip`).

Index: [docs/transcripts/INDEX.md](transcripts/INDEX.md)

- [`Phase 1`](transcripts/Phase 1.md)
- [`Phase 2`](transcripts/Phase 2.md)
- [`phase 3`](transcripts/phase 3.md)
- [`phase 4`](transcripts/phase 4.md)
- [`phase 5`](transcripts/phase 5.md)
- [`phase-5-polish-and-phase-6`](transcripts/phase-5-polish-and-phase-6.md)

## Competency (student-judge)

Filled by Guide from the student-judge run when this report was built.

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

## Skill integrity

Course skills are hashed at export and compared to `.agents/skills.lock.json`. Do not edit `.agents/skills/`, `.cursor/skills/`, or `AGENTS.md`.

- Status: **pass**
- Root: `e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb`
- none
