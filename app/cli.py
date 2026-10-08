#!/usr/bin/env python3
"""FastStarter project CLI — stdlib argparse (no extra CLI library).

From the project root (venv active, deps installed; ``.env`` optional — falls back to ``.env.example``):

    python manage.py init
    python manage.py run
    python manage.py users
    python manage.py report --name "Student Name" --id "816000000"
    python manage.py usecase
    python manage.py skills-verify
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path


def _ensure_models_loaded() -> None:
    import app.models  # noqa: F401


def cmd_init(args: argparse.Namespace) -> None:
    """Create database tables (drops existing by default) and seed demo users."""
    from app.config import get_settings
    from app.database import drop_all, ensure_db_and_tables

    _ensure_models_loaded()
    if args.drop:
        print("Dropping all tables…")
        # Drop can fail on a brand-new empty DB; create path still retries.
        try:
            drop_all()
        except Exception as exc:  # noqa: BLE001
            from app.database import is_db_not_ready_error

            if not is_db_not_ready_error(exc):
                raise
            print(f"Database not ready yet while dropping ({exc}); continuing…")
    print("Creating tables…")
    ensure_db_and_tables()
    print(f"Database ready ({get_settings().database_uri}).")
    if getattr(args, "seed", True):
        cmd_seed(args)


def cmd_seed(args: argparse.Namespace) -> None:
    """Insert demo users and a sample student degree profile.

    bob / bobpass       (regular_user)
    admin / adminpass   (admin)
    """
    from app.database import ensure_db_and_tables, get_cli_session
    from app.models.course import Advisor, Course, DegreeRequirement, Semester
    from app.models.course_selection import CourseSelection
    from app.models.degree import Degree, StudentDegree
    from app.models.student import Student
    from sqlmodel import select
    from app.repositories.user import UserRepository
    from app.schemas.user import AdminCreate, RegularUserCreate
    from app.utilities.security import encrypt_password

    _ensure_models_loaded()
    ensure_db_and_tables()

    demo_users = [
        ("bob", "bob@example.com", "bobpass", "regular_user"),
        ("admin", "admin@example.com", "adminpass", "admin"),
    ]

    created = 0
    skipped = 0
    with get_cli_session() as session:
        repo = UserRepository(session)
        for username, email, password, role in demo_users:
            if repo.get_by_username(username):
                print(f"  skip  {username} (already exists)")
                skipped += 1
                continue
            payload_cls = AdminCreate if role == "admin" else RegularUserCreate
            repo.create(
                payload_cls(
                    username=username,
                    email=email,
                    password=encrypt_password(password),
                    role=role,
                )
            )
            print(f"  create {username} ({role})")
            created += 1

        admin_user = repo.get_by_username("admin")
        if admin_user:
            advisor = session.exec(
                select(Advisor).where(Advisor.user_id == admin_user.id)
            ).one_or_none()
            if advisor is None:
                session.add(
                    Advisor(
                        user_id=admin_user.id,
                        first_name="Admin",
                        last_name="Advisor",
                        email=admin_user.email,
                    )
                )
                session.commit()
                print("  create Advisor profile for admin")

        demo_student_user = repo.get_by_username("bob")
        if demo_student_user:
            student = session.exec(
                select(Student).where(Student.user_id == demo_student_user.id)
            ).one_or_none()
            if student is None:
                student = Student(
                    user_id=demo_student_user.id,
                    first_name="Bob",
                    last_name="Student",
                    email=demo_student_user.email,
                    current_year=3,
                )
                session.add(student)
                session.commit()
                session.refresh(student)
                print("  create Student profile for bob")
            elif student.current_year == 1:
                student.current_year = 3
                session.add(student)
                session.commit()
                print("  move bob to Year 3")

            for old_name, new_name in (
                ("Computer Science", "BSc Computer Science"),
                ("Mathematics", "BSc Mathematics"),
            ):
                old_degree = session.exec(
                    select(Degree).where(Degree.degree_name == old_name)
                ).one_or_none()
                new_degree = session.exec(
                    select(Degree).where(Degree.degree_name == new_name)
                ).one_or_none()
                if old_degree is None:
                    continue
                if new_degree is None or old_degree.degree_id == new_degree.degree_id:
                    old_degree.degree_name = new_name
                    session.add(old_degree)
                    print(f"  rename {old_name} to {new_name}")
                    continue
                old_assignments = session.exec(
                    select(StudentDegree).where(StudentDegree.degree_id == old_degree.degree_id)
                ).all()
                new_assignments = session.exec(
                    select(StudentDegree).where(StudentDegree.degree_id == new_degree.degree_id)
                ).all()
                keep, drop = (
                    (old_degree, new_degree)
                    if len(old_assignments) >= len(new_assignments)
                    else (new_degree, old_degree)
                )
                for requirement in session.exec(
                    select(DegreeRequirement).where(DegreeRequirement.degree_id == drop.degree_id)
                ).all():
                    session.delete(requirement)
                for assignment in session.exec(
                    select(StudentDegree).where(StudentDegree.degree_id == drop.degree_id)
                ).all():
                    session.delete(assignment)
                session.delete(drop)
                keep.degree_name = new_name
                session.add(keep)
                print(f"  merge duplicate into {new_name}")
            session.commit()

            assignments = session.exec(
                select(StudentDegree).where(StudentDegree.student_id == student.student_id)
            ).all()
            if not assignments:
                demo_degrees = [
                    ("BSc Computer Science", "Faculty of Science and Technology", 93, 3, "Major"),
                    ("BSc Mathematics", "Faculty of Science and Technology", 15, 2, "Minor"),
                ]
                for degree_name, faculty_name, credits, expected_years, program_type in demo_degrees:
                    degree = session.exec(
                        select(Degree).where(Degree.degree_name == degree_name)
                    ).one_or_none()
                    if degree is None:
                        degree = Degree(
                            degree_name=degree_name,
                            faculty_name=faculty_name,
                            total_credits_required=credits,
                            expected_years=expected_years,
                        )
                        session.add(degree)
                        session.commit()
                        session.refresh(degree)

                    session.add(
                        StudentDegree(
                            student_id=student.student_id,
                            degree_id=degree.degree_id,
                            program_type=program_type,
                        )
                    )
                    degree.expected_years = expected_years
                    session.add(degree)
                session.commit()
                print("  create demo Major and Minor degree assignments for bob")

            major = session.exec(
                select(Degree).where(Degree.degree_name == "BSc Computer Science")
            ).one()
            minor = session.exec(
                select(Degree).where(Degree.degree_name == "BSc Mathematics")
            ).one()
            major.expected_years = 3
            minor.expected_years = 2
            session.add(major)
            session.add(minor)
            demo_courses = [
                ("COMP3602", "Theory of Computing", "Explores formal languages, automata, computability, and the theoretical foundations of computation.", 3, major, "Core", "C", 1, 1),
                ("COMP3603", "Human Computer Interaction", "Explores how people interact with technology and how to design user-friendly, accessible interfaces.", 3, major, "Core", "C", 1, 2),
                ("COMP3991", "Applied Mathematics for Scientific Computing", "Applies mathematical methods and computational techniques to solve scientific and real-world problems.", 3, major, "Core", "C", 2, 1),
                ("COMP3605", "Introduction to Data Analytics", "Introduces data analysis techniques for discovering patterns, insights, and trends from data.", 3, major, "Elective", "C", 2, 2),
                ("COMP3613", "Software Engineering II", "Covers software development practices, system design, testing, teamwork, and project management.", 3, major, "Elective", "C", 3, 1),
                ("COMP3606", "Wireless and Mobile Computing", "Explores wireless and mobile technologies, including networking, communication, and device design.", 3, major, "Elective", "C", 3, 2),
                ("MATH3273", "Linear Algebra II", "Covers vectors, matrices, linear transformations, eigenvalues, and advanced linear algebra concepts.", 3, minor, "Core", "C", 1, 1),
                ("MATH3277", "Introduction to Real Analysis II", "An introduction to the theory of real numbers and functions of a real variable.", 3, minor, "Core", "C", 1, 2),
                ("MATH3278", "Probability Theory II ", "Covers advanced probability concepts, distributions, random variables, and statistical methods.", 3, minor, "Elective", "C", 2, 1),
            ]
            for code, name, description, credits, degree, requirement_type, minimum_grade, expected_year, expected_semester in demo_courses:
                course = session.get(Course, code)
                if course is None:
                    course = Course(
                        course_code=code,
                        course_name=name,
                        description=description,
                        credits=credits,
                    )
                    session.add(course)
                    session.flush()

                requirement = session.exec(
                    select(DegreeRequirement).where(
                        DegreeRequirement.degree_id == degree.degree_id,
                        DegreeRequirement.course_code == code,
                    )
                ).first()
                if requirement is None:
                    session.add(
                        DegreeRequirement(
                            degree_id=degree.degree_id,
                            course_code=code,
                            requirement_type=requirement_type,
                            minimum_grade=minimum_grade,
                            expected_year=expected_year,
                            expected_semester=expected_semester,
                        )
                    )
                else:
                    requirement.requirement_type = requirement_type
                    requirement.expected_year = expected_year
                    requirement.expected_semester = expected_semester
                    session.add(requirement)

            uwi_catalog = [
                (
                    "BSc Information Technology",
                    "Faculty of Science and Technology",
                    90,
                    3,
                    [
                        ("INFO1600", "Information Technology Fundamentals", "Information systems and digital technologies", 3, "Core", 1, 1),
                        ("INFO1601", "Web Development", "Client-side and server-side web development", 3, "Core", 1, 2),
                        ("INFO2602", "Web Programming and Technologies I", "Introduces web development, including HTML, CSS, JavaScript, and server-side technologies.", 3, "Core", 2, 1),
                        ("INFO2605", "Network Administration", "Network services, administration, and security", 3, "Core", 2, 2),
                    ],
                ),
                (
                    "BSc Economics",
                    "Faculty of Social Sciences",
                    90,
                    3,
                    [
                        ("ECON1001", "Principles of Economics I", "Foundations of microeconomic analysis", 3, "Core", 1, 1),
                        ("ECON1002", "Principles of Economics II", "Foundations of macroeconomic analysis", 3, "Core", 1, 2),
                        ("ECON2001", "Intermediate Microeconomics", "Consumer, producer, and market theory", 3, "Core", 2, 1),
                        ("ECON2002", "Intermediate Macroeconomics", "National income, growth, and policy", 3, "Core", 2, 2),
                    ],
                ),
                (
                    "BSc Management Studies",
                    "Faculty of Social Sciences",
                    90,
                    3,
                    [
                        ("MGMT1000", "Introduction to Management", "Principles of management and organizations", 3, "Core", 1, 1),
                        ("MGMT1001", "Business Communication", "Professional communication in business", 3, "Core", 1, 2),
                        ("MGMT2004", "Organizational Behaviour", "People, teams, and organizations", 3, "Core", 2, 1),
                        ("MGMT2010", "Operations Management", "Processes, capacity, and quality management", 3, "Core", 2, 2),
                    ],
                ),
                (
                    "BA Psychology",
                    "Faculty of Social Sciences",
                    90,
                    3,
                    [
                        ("PSYC1000", "Introduction to Psychology", "Foundations of psychological science", 3, "Core", 1, 1),
                        ("PSYC1001", "Research Methods in Psychology", "Research design and psychological measurement", 3, "Core", 1, 2),
                        ("PSYC2000", "Developmental Psychology", "Human development across the lifespan", 3, "Core", 2, 1),
                        ("PSYC2001", "Social Psychology", "Social influence, groups, and relationships", 3, "Core", 2, 2),
                    ],
                ),
                (
                    "BSc Civil Engineering",
                    "Faculty of Engineering",
                    90,
                    3,
                    [
                        ("ENGR1000", "Engineering Mathematics I", "Mathematical methods for engineering", 3, "Core", 1, 1),
                        ("ENGR1001", "Engineering Drawing", "Technical drawing and computer-aided design", 3, "Core", 1, 2),
                        ("CIVL2000", "Structural Mechanics", "Statics, strength, and structural analysis", 3, "Core", 2, 1),
                        ("CIVL2001", "Construction Materials", "Properties and applications of construction materials", 3, "Core", 2, 2),
                    ],
                ),
                (
                    "BSc Nursing",
                    "Faculty of Medical Sciences",
                    90,
                    3,
                    [
                        ("NURS1000", "Foundations of Nursing", "Professional nursing practice and patient care", 3, "Core", 1, 1),
                        ("NURS1001", "Human Anatomy and Physiology", "Structure and function of the human body", 3, "Core", 1, 2),
                        ("NURS2000", "Adult Health Nursing", "Nursing care for adult health conditions", 3, "Core", 2, 1),
                        ("NURS2001", "Community Health Nursing", "Population health and community nursing", 3, "Core", 2, 2),
                    ],
                ),
            ]
            for degree_name, faculty_name, credits, expected_years, catalog_courses in uwi_catalog:
                degree = session.exec(
                    select(Degree).where(Degree.degree_name == degree_name)
                ).one_or_none()
                if degree is None:
                    degree = Degree(
                        degree_name=degree_name,
                        faculty_name=faculty_name,
                        total_credits_required=credits,
                        expected_years=expected_years,
                    )
                    session.add(degree)
                    session.flush()
                else:
                    degree.faculty_name = faculty_name
                    degree.total_credits_required = credits
                    degree.expected_years = expected_years
                    session.add(degree)

                for code, name, description, course_credits, requirement_type, expected_year, expected_semester in catalog_courses:
                    course = session.get(Course, code)
                    if course is None:
                        course = Course(
                            course_code=code,
                            course_name=name,
                            description=description,
                            credits=course_credits,
                        )
                        session.add(course)
                        session.flush()

                    requirement = session.exec(
                        select(DegreeRequirement).where(
                            DegreeRequirement.degree_id == degree.degree_id,
                            DegreeRequirement.course_code == code,
                        )
                    ).first()
                    if requirement is None:
                        session.add(
                            DegreeRequirement(
                                degree_id=degree.degree_id,
                                course_code=code,
                                requirement_type=requirement_type,
                                minimum_grade="C",
                                expected_year=expected_year,
                                expected_semester=expected_semester,
                            )
                        )
                    else:
                        requirement.expected_year = expected_year
                        requirement.expected_semester = expected_semester
                        session.add(requirement)
            session.commit()

            completed_history = [
                (1, 1, ["COMP1600", "COMP1601", "INFO1600", "MATH1150", "FOUN1101"]),
                (1, 2, ["COMP1602", "COMP1604", "INFO1601", "FOUN1301"]),
                (1, 3, ["COMP1603"]),
                (2, 1, ["COMP2601", "COMP2602", "COMP2605", "COMP2611", "MATH2250"]),
                (2, 2, ["COMP2604", "COMP2606", "INFO2602", "INFO2604", "FOUN1105"]),
                (2, 3, ["COMP2603"]),
            ]
            for expected_year, semester_number, codes in completed_history:
                calendar_year = 2022 + expected_year
                start_month = (semester_number - 1) * 4 + 1
                end_month = start_month + 3
                semester = session.exec(
                    select(Semester).where(
                        Semester.semester_year == calendar_year,
                        Semester.start_date == date(calendar_year, start_month, 1),
                    )
                ).first()
                if semester is None:
                    semester = Semester(
                        semester_name=f"Semester {semester_number}",
                        semester_year=calendar_year,
                        start_date=date(calendar_year, start_month, 1),
                        end_date=date(calendar_year, end_month, 28),
                    )
                    session.add(semester)
                    session.flush()
                for code in codes:
                    if session.get(Course, code) is None:
                        session.add(
                            Course(
                                course_code=code,
                                course_name=code,
                                description="",
                                credits=3,
                            )
                        )
                        session.flush()
                    existing = session.exec(
                        select(CourseSelection).where(
                            CourseSelection.student_id == student.student_id,
                            CourseSelection.course_code == code,
                            CourseSelection.semester_id == semester.semester_id,
                            CourseSelection.status == "completed",
                        )
                    ).first()
                    if existing is None:
                        session.add(
                            CourseSelection(
                                student_id=student.student_id,
                                course_code=code,
                                semester_id=semester.semester_id,
                                status="completed",
                            )
                        )
                    requirement = session.exec(
                        select(DegreeRequirement).where(
                            DegreeRequirement.degree_id == major.degree_id,
                            DegreeRequirement.course_code == code,
                        )
                    ).first()
                    if requirement is None:
                        session.add(
                            DegreeRequirement(
                                degree_id=major.degree_id,
                                course_code=code,
                                requirement_type="Core",
                                minimum_grade="C",
                                expected_year=expected_year,
                                expected_semester=semester_number,
                            )
                        )
            if session.get(Course, "CSCI110") is None:
                session.add(
                    Course(
                        course_code="CSCI110",
                        course_name="Introduction to Computing",
                        description="",
                        credits=3,
                    )
                )
                session.flush()
            csci_requirement = session.exec(
                select(DegreeRequirement).where(
                    DegreeRequirement.degree_id == major.degree_id,
                    DegreeRequirement.course_code == "CSCI110",
                )
            ).first()
            if csci_requirement is None:
                session.add(
                    DegreeRequirement(
                        degree_id=major.degree_id,
                        course_code="CSCI110",
                        requirement_type="Core",
                        minimum_grade="C",
                        expected_year=3,
                        expected_semester=3,
                    )
                )
            cs_year3 = [
                ("COMP3602", "Theory of Computing", "Explores formal languages, automata, computability, and the theoretical foundations of computation.", "Core", 3, 1),
                ("COMP3603", "Human-Computer Interaction", "Explores how people interact with technology and how to design user-friendly, accessible interfaces.", "Core", 3, 1),
                ("COMP3991", "Applied Mathematics for Scientific Computing", "Applies mathematical methods and computational techniques to solve scientific and real-world problems.", "Core", 3, 1),
                ("COMP3605", "Introduction to Data Analytics", "Introduces data analysis techniques for discovering patterns, insights, and trends from data.", "Elective", 3, 1),
                ("COMP3606", "Wireless and Mobile Computing", "Explores wireless and mobile technologies, including networking, communication, and device design.", "Elective", 3, 1),
                ("COMP3607", "Object-Oriented Programming II", "", "Elective", 3, 1),
                ("COMP3613", "Software Engineering II", "Covers software development practices, system design, testing, teamwork, and project management.", "Elective", 3, 1),
                ("INFO2605", "Professional Ethics and Law", "", "Elective", 3, 1),
                ("INFO3600", "Business Information Systems", "", "Elective", 3, 1),
                ("INFO3605", "Fundamentals of LAN Technologies", "", "Elective", 3, 1),
                ("COMP3601", "Design and Analysis of Algorithms", "", "Core", 3, 2),
                ("INFO3604", "Project", "", "Core", 3, 2),
                ("COMP3608", "Intelligent Systems", "", "Elective", 3, 2),
                ("COMP3609", "Game Programming", "", "Elective", 3, 2),
                ("COMP3610", "Big Data Analytics", "", "Elective", 3, 2),
                ("COMP3611", "Modelling and Simulation", "Not offered in 2024/2025.", "Elective", 3, 2),
                ("INFO3606", "Cloud Computing", "", "Elective", 3, 2),
                ("INFO3607", "Fundamentals of WAN Technologies", "", "Elective", 3, 2),
                ("INFO3608", "E-Commerce", "", "Elective", 3, 2),
                ("INFO3611", "Database Administration", "", "Elective", 3, 2),
            ]
            for code, name, description, requirement_type, expected_year, expected_semester in cs_year3:
                course = session.get(Course, code)
                if course is None:
                    course = Course(
                        course_code=code,
                        course_name=name,
                        description=description,
                        credits=3,
                    )
                    session.add(course)
                    session.flush()
                else:
                    course.course_name = name
                    course.description = description
                    course.credits = 3
                    session.add(course)
                requirement = session.exec(
                    select(DegreeRequirement).where(
                        DegreeRequirement.degree_id == major.degree_id,
                        DegreeRequirement.course_code == code,
                    )
                ).first()
                if requirement is None:
                    session.add(
                        DegreeRequirement(
                            degree_id=major.degree_id,
                            course_code=code,
                            requirement_type=requirement_type,
                            minimum_grade="C",
                            expected_year=expected_year,
                            expected_semester=expected_semester,
                        )
                    )
                else:
                    requirement.requirement_type = requirement_type
                    requirement.expected_year = expected_year
                    requirement.expected_semester = expected_semester
                    session.add(requirement)
            special_course = session.get(Course, "COMP3612")
            if special_course is None:
                session.add(
                    Course(
                        course_code="COMP3612",
                        course_name="Special Topics in Computer Science",
                        description="Not offered in 2024/2025.",
                        credits=3,
                    )
                )
                session.flush()
            else:
                special_course.course_name = "Special Topics in Computer Science"
                special_course.description = "Not offered in 2024/2025."
                special_course.credits = 3
                session.add(special_course)
            existing_special = session.exec(
                select(DegreeRequirement).where(
                    DegreeRequirement.degree_id == major.degree_id,
                    DegreeRequirement.course_code == "COMP3612",
                )
            ).all()
            for index, (expected_year, expected_semester) in enumerate([(3, 1), (3, 2)]):
                if index < len(existing_special):
                    row = existing_special[index]
                    row.requirement_type = "Elective"
                    row.expected_year = expected_year
                    row.expected_semester = expected_semester
                    session.add(row)
                else:
                    session.add(
                        DegreeRequirement(
                            degree_id=major.degree_id,
                            course_code="COMP3612",
                            requirement_type="Elective",
                            minimum_grade="C",
                            expected_year=expected_year,
                            expected_semester=expected_semester,
                        )
                    )
            relocated = session.exec(
                select(Degree).where(Degree.faculty_name == "Faculty of Science")
            ).all()
            for degree in relocated:
                degree.faculty_name = "Faculty of Science and Technology"
                session.add(degree)
            session.commit()
            if relocated:
                print(f"  move {len(relocated)} degree(s) to Faculty of Science and Technology")
            print("  ensure sample degree requirements, completed history, and one pending review for bob")

    print(f"Seed done — created {created}, skipped {skipped}.")
    print("Login with bob/bobpass or admin/adminpass")


def cmd_run(args: argparse.Namespace) -> None:
    """Start the FastAPI app with Uvicorn."""
    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    bind_host = args.host or settings.app_host
    bind_port = args.port or settings.app_port
    if args.reload is None:
        use_reload = settings.env.lower() != "production"
    else:
        use_reload = args.reload
    print(f"Starting FastStarter on http://{bind_host}:{bind_port} (reload={use_reload})")
    uvicorn.run(
        "app.main:app",
        host=bind_host,
        port=bind_port,
        reload=use_reload,
    )


def cmd_report(args: argparse.Namespace) -> None:
    """Build the submission package: merge judge, package transcripts, write PDF.

    Guide must (1) write ``docs/judge.md`` and (2) pull every Guide chat into
    ``docs/transcripts/*.md`` before this command. Report only packages those files.
    """
    from app.report_pdf import export_report
    from app.skill_integrity import format_report, verify

    result = export_report(
        name=args.name,
        student_id=args.student_id,
        source=None if args.src is None else Path(args.src),
        output=None if args.output is None else Path(args.output),
    )
    print()
    print("Report package:")
    print(
        f"  Judge:       {'merged docs/judge.md' if result.judge_merged else 'MISSING - Guide must run student-judge first'}"
    )
    print(
        f"  Transcripts: {result.transcript_count} chat(s) in docs/transcripts/"
        + (
            ""
            if result.transcript_count
            else " (EMPTY - Guide must pull Copilot/Cursor/OpenCode chats first)"
        )
    )
    if result.transcript_zip:
        print(f"  Zip:         {result.transcript_zip.as_posix()}")
    print(f"  PDF:         {result.pdf_path.as_posix()}")
    print(format_report(verify()))


def cmd_transcripts(args: argparse.Namespace) -> None:
    """Package agent-written markdown under docs/transcripts/ (+ zip)."""
    from app.transcript_export import package_transcripts

    result = package_transcripts(make_zip=not args.no_zip)
    if result.found == 0:
        print(
            "Warning: no chat markdown in docs/transcripts/. "
            "The Guide agent must pull every Guide chat for this project "
            "(Copilot Agent, Cursor, or OpenCode) into docs/transcripts/<slug>.md first."
        )
        raise SystemExit(2)
    print(f"Submission package ready: {result.out_dir}")
    if result.zip_path:
        print(f"Zip for submission: {result.zip_path}")


def cmd_skills_verify(args: argparse.Namespace) -> None:
    """Check course skill files against .agents/skills.lock.json."""
    from app.skill_integrity import format_report, verify

    result = verify()
    print(format_report(result))
    if not result.ok:
        raise SystemExit(1)


def cmd_usecase(args: argparse.Namespace) -> None:
    """Render docs/diagrams/use-case.json to a UML use-case PNG."""
    from app.usecase_diagram import render_usecase_png

    dest = render_usecase_png(
        spec_path=None if args.spec is None else Path(args.spec),
        output=None if args.output is None else Path(args.output),
    )
    print(f"Wrote {dest}")


def cmd_skills_lock(args: argparse.Namespace) -> None:
    """Rewrite the skill lockfile (course authors only)."""
    from app.skill_integrity import write_lock

    dest = write_lock()
    print(f"Wrote {dest}")


def cmd_users(args: argparse.Namespace) -> None:
    """List users currently in the database."""
    from sqlmodel import select

    from app.database import get_cli_session
    from app.models.user import User

    _ensure_models_loaded()
    with get_cli_session() as session:
        users = session.exec(select(User)).all()
        if not users:
            print("No users found. Run: python manage.py init")
            return
        for user in users:
            print(
                f"  id={user.id}  username={user.username}  "
                f"role={user.role}  email={user.email}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python manage.py",
        description="FastStarter Python CLI — init database, seed demo data, run the app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create DB tables and seed demo users (drops existing tables by default)",
    )
    p_init.add_argument(
        "--no-drop",
        dest="drop",
        action="store_false",
        help="Create tables without dropping existing ones",
    )
    p_init.add_argument(
        "--no-seed",
        dest="seed",
        action="store_false",
        help="Skip demo user seed after creating tables",
    )
    p_init.set_defaults(drop=True, seed=True, func=cmd_init)

    p_seed = sub.add_parser(
        "seed",
        help="Insert demo users only (idempotent; also runs as part of init)",
    )
    p_seed.set_defaults(func=cmd_seed)

    p_run = sub.add_parser("run", help="Start the web app (uvicorn)")
    p_run.add_argument("--host", default=None, help="Bind host")
    p_run.add_argument("--port", type=int, default=None, help="Bind port")
    reload_group = p_run.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload", dest="reload", action="store_true", default=None, help="Enable auto-reload"
    )
    reload_group.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Disable auto-reload"
    )
    p_run.set_defaults(func=cmd_run, reload=None)

    p_users = sub.add_parser("users", help="List users in the database")
    p_users.set_defaults(func=cmd_users)

    p_report = sub.add_parser(
        "report",
        help=(
            "Build submission package: merge docs/judge.md, package docs/transcripts/, "
            "write docs/report.pdf (Guide pulls chats + runs student-judge first)"
        ),
    )
    p_report.add_argument("--name", required=True, help="Student name (printed on the PDF cover)")
    p_report.add_argument("--id", dest="student_id", required=True, help="Student ID (PDF only)")
    p_report.add_argument("--src", default=None, help="Markdown path (default: docs/report.md)")
    p_report.add_argument("--output", default=None, help="PDF path (default: docs/report.pdf)")
    p_report.set_defaults(func=cmd_report)

    p_transcripts = sub.add_parser(
        "transcripts",
        help="Package agent-written docs/transcripts/*.md into INDEX + zip (no IDE scrape)",
    )
    p_transcripts.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip writing docs/transcripts.zip",
    )
    p_transcripts.set_defaults(func=cmd_transcripts)

    p_usecase = sub.add_parser(
        "usecase",
        help="Render docs/diagrams/use-case.json to a UML use-case PNG",
    )
    p_usecase.add_argument("--spec", default=None, help="JSON spec (default: docs/diagrams/use-case.json)")
    p_usecase.add_argument("--output", default=None, help="PNG path (default: docs/diagrams/use-case.png)")
    p_usecase.set_defaults(func=cmd_usecase)

    p_skills_verify = sub.add_parser(
        "skills-verify",
        help="Check course skills against .agents/skills.lock.json",
    )
    p_skills_verify.set_defaults(func=cmd_skills_verify)

    p_skills_lock = sub.add_parser(
        "skills-lock",
        help="Rewrite .agents/skills.lock.json (course authors; needs FASTSTARTER_SKILLS_LOCK=1)",
    )
    p_skills_lock.set_defaults(func=cmd_skills_lock)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
