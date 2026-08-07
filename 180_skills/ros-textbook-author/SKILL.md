---
name: ros-textbook-author
description: Plan, draft, revise, and audit the university-level bilingual textbook series 机器人操作系统与智能机器人开发, covering ROS1, ROS2, intelligent robot perception-decision-action-feedback development, robot applications, production internships, comprehensive course design, project cases, assessments, and competition-derived cases. Use when working on the ROS教材 project, including series planning, chapter outlines, chapter writing, Chinese-English terminology, ROS1/ROS2 comparison, intelligent robot development, production internship tasks, course-design projects, experiments, exercises, project rubrics, competition case studies, or textbook quality review.
---

# ROS Textbook Author

## Core workflow

1. Read `references/project-decisions.md` before planning, drafting, revising,
   or auditing any part of this specific textbook series.
2. Read `references/outcomes-alignment.md` when defining learning objectives,
   assessments, course mappings, or claims about the training program.
3. Read `references/licensing-policy.md` before publishing, importing,
   adapting, or redistributing text, figures, code, data, models, or weights.
4. Read `references/volume-1-turtlesim-case.md` before planning, drafting, or
   revising Volume 1 chapters, exercises, code, or the final project.
5. Identify the target volume, chapter, audience, class hours, ROS version,
   expected prerequisites, and requested deliverable.
6. Read only the other references needed for the current task.
7. Inspect existing project material before drafting or revising.
8. Distinguish verified technical facts from proposed teaching design.
9. Draft with explicit learning progression:
   motivation, concept, observation, implementation, experiment, reflection.
10. Verify commands, package names, interfaces, versions, and code when practical.
11. Run the quality checklist before delivery.
12. Preserve the user's approved structure and terminology in later revisions.

## Companion skill routing

Use only the smallest set of companion skills required for the current task.
Naming a companion skill does not mean it has been loaded. Before taking
actions governed by another skill, confirm that it is available, read its
complete `SKILL.md`, announce why it is being used, and follow its workflow.
If a requested companion skill is unavailable, state that briefly and use the
closest in-scope workflow without claiming the missing skill was used.

- Use `doc-coauthoring` for volume planning, major chapter restructuring, or
  sustained section-by-section co-authoring when the user wants an iterative
  context-gathering, refinement, and reader-testing workflow. Do not invoke it
  for a small edit or a single factual answer.
- Use `scientific-schematics` for ROS computation graphs, node-interface
  diagrams, TF trees, navigation or MoveIt architectures, experimental setups,
  and other publication-quality technical schematics.
- Use `documents:documents` when creating, editing, redlining, formatting, or
  visually reviewing a DOCX manuscript or publisher-formatted chapter. Do not
  format a manuscript while its structure is still undecided unless the user
  explicitly requests a formatted draft.
- Use `literature-review` when a task requires systematic scholarly evidence,
  related-work coverage, research-backed technical context, or broad discovery
  of candidate competition cases.
- Use `citation-management` when collecting, deduplicating, normalizing,
  formatting, or auditing bibliographic records and in-text citations. Pair it
  with literature review when both evidence synthesis and reference integrity
  are required.
- Use `quiz-and-assessment-design` only for categorization-driven learner
  diagnostics, readiness assessments, or recommended learning paths. It is a
  segmentation-oriented assessment skill, not an educational exam-authoring
  skill. Do not use it for chapter exercises, examination papers, answer keys,
  or grading rubrics; use `references/exercise-rubric.md` for those tasks.
- Use `nature-polishing` only after technical structure, terminology, evidence,
  and verification status are stable, when the task requires substantial
  Chinese academic-language polishing. Never use polishing to hide unresolved
  technical uncertainty.

When several companion skills apply, use them in this order unless the task
requires otherwise: evidence discovery, citation management, content
co-authoring, technical schematics, language polishing, document production.

## Series boundaries

Use `references/series-plan.md` whenever planning chapters or deciding
which volume should contain a topic.

- Volume 1 establishes ROS system thinking and covers ROS1 and ROS2 foundations.
- Volume 2 covers TF, modeling, simulation, navigation, MoveIt, perception,
  control, and system integration.
- Volume 3 serves production internship and comprehensive course design. It
  covers project workflow, deployment, integration, testing, documentation,
  assessment, and engineering cases drawn from industry, teaching, research,
  and competitions.

Across all three volumes, make intelligent robot development visible through
the progression `perception -> decision -> action -> feedback`: Volume 1 builds
the software-system loop, Volume 2 implements intelligent functions, and
Volume 3 integrates and delivers complete task-oriented systems. Do not use
“intelligent” as a synonym for deep learning or as an unsupported title claim.

Do not duplicate a complete topic across volumes. Introduce prerequisites
briefly and point to the volume where the topic is developed fully.

Volume 1 uses the single-turtle `TurtleMission` autonomous task system as its
approved through-line. Develop it cumulatively through `TurtleGoal`,
`TurtleGuard`, `TurtlePainter`, and the integrated `TurtleMission`; do not turn
these into four unrelated sample projects.
Keep Chapters 1-5 as the shared foundation. Present one complete stage case at
the end of each of Chapters 6-9: `TurtleGoal`, `TurtleGuard`, `TurtlePainter`,
and `TurtleMission`, respectively. Chapter 10 consolidates migration, testing,
and review; it must not introduce a fifth case.

## Chapter writing

Read `references/chapter-template.md` before creating or substantially
restructuring a chapter.

Start from a robot problem or observable phenomenon. Introduce a ROS concept
when it becomes necessary to solve that problem. Avoid command-list teaching.
When applicable, identify how the chapter contributes to perception, decision,
action, feedback, or their system integration.

For every command or code example:

- state whether it is ROS1, ROS2, or shared;
- state the applicable software environment;
- explain the expected observable result;
- include at least one likely failure and diagnostic method;
- never present unverified code as tested.

## ROS1 and ROS2

Read `references/ros-version-policy.md` for comparison or implementation work.

Teach shared concepts once. Present ROS1 and ROS2 implementations as
corresponding realizations of the same system idea. Avoid writing two
independent books inside one volume.

Label content consistently:

- Shared concept
- ROS1 implementation
- ROS2 implementation
- Migration note
- Version-specific warning

## Bilingual writing

Read `references/terminology.md` for terminology or bilingual work.

Use Chinese as the main explanatory language unless the user requests
otherwise. On first occurrence, write:

`中文名称（English term，abbreviation）`

After the first occurrence, use the approved Chinese term or abbreviation
consistently. Keep command names, package names, API names, message fields,
file names, and code identifiers in their original form.

Do not translate technical identifiers literally.

## Experiments and assessments

Read `references/exercise-rubric.md` when designing exercises, tests,
experiments, answer keys, or grading criteria.

Separate:

- concept checks;
- command and observation tasks;
- programming exercises;
- diagnostic exercises;
- design questions;
- comprehensive projects.

Every experiment must specify prerequisites, environment, objective, steps,
expected evidence, failure diagnosis, submission artifacts, and rubric.

## Production internship and comprehensive course design

Read `references/practice-course-policy.md` whenever planning Volume 3,
selecting project cases, designing course delivery, or defining assessment.

- Treat production internship and comprehensive course design as two teaching
  routes that may share the same project case but must not share identical
  instructions or assessment.
- For production internship, emphasize safety, equipment operation,
  environment deployment, prescribed workflow, troubleshooting, records, and
  handover.
- For comprehensive course design, emphasize requirements, alternatives,
  architecture, team roles, staged reviews, integration, verification,
  technical reporting, and defense.
- Provide both routes for a reusable case whenever practical: a guided
  deployment-and-debugging route and an open design-and-integration route.
- Keep module-level teaching in Volume 2. Move multi-module delivery,
  acceptance, and project evaluation to Volume 3.

## Project and competition-derived cases

Read `references/competition-case-template.md` before drafting an engineering,
teaching, research, or competition-derived project case.

Do not write a promotional summary. Convert the source into a reproducible
engineering study covering course applicability, requirements, architecture,
ROS graph, TF tree, hardware, software versions, implementation, debugging,
metrics, limitations, assessment, and extension tasks.

Clearly label:

- publicly verified facts;
- information provided by the case owner;
- author reconstruction;
- proposed teaching adaptation.

Do not reuse protected text, figures, code, or photographs without permission.

## Quality control

Read `references/quality-checklist.md` before finalizing a chapter.

Check:

- volume boundary;
- prerequisite consistency;
- terminology consistency;
- ROS1/ROS2 labels;
- version reproducibility;
- command and code status;
- figure and source attribution;
- experiment observability;
- assessment-answer alignment;
- unresolved placeholders.

Report what is complete, what is proposed, and what remains unverified.
