# Participium

> A full-stack, role-based civic engagement platform developed as a software engineering project for Politecnico di Torino (PoliTO).

Participium is a comprehensive system designed to bridge the gap between citizens and municipal administrations. It empowers citizens to easily report urban issues (such as broken streetlights, potholes, or environmental hazards) via an interactive interface, and provides municipal operators with a dedicated dashboard to assign, track, communicate, and resolve these reports efficiently.

### Technologies & Implementation Details
Throughout the development of this platform, the following components and engineering practices were successfully implemented:
* **Frontend:** Built a responsive, dynamic single-page application using **React** (Vite).
* **Backend:** Developed a robust RESTful API architecture using **Python** and **Flask**.
* **Database:** Integrated a relational **MySQL** database using SQLAlchemy for secure data persistence.
* **Containerization:** Orchestrated the entire ecosystem (Frontend, Backend, Database) using **Docker** and **Docker Compose** for seamless, automated local deployment.
* **Quality Assurance & Testing:** Ensured system reliability through a multi-layered testing strategy:
  * White-box and Black-box backend testing (`pytest`).
  * Automated API Acceptance Testing (`Postman`).
  * End-to-End automated browser UI testing (`Selenium WebDriver`).

---

## Project Repository Details

**System description (entry point):**
- **[Participium.md](doc/Participium.md)** — definitive system description (EN)
- **[Participium_it.md](doc/Participium_it.md)** — Italian version (IT)

### Repository structure

- **`doc/`** Project documentation.
    - `Participium.md`: general system description (EN).
    - `Participium_it.md`: general system description (IT).
    - `OfficialDocumentation.md`: official requirement engineering documentation.
    - `Participium_Implementation_Spec.md`: implementation specification.
    - `deliverables/`: **stubs/templates** to be completed for each project task.

- **`data/`** Static/auxiliary data used by the project documentation and deliverables.
    - `img/`: images referenced by Markdown documents.

- **`src/`** Source code of the system implementation.

- **`task/`** Task specifications and assignment texts (what must be done for each project task).

### Changelog

| Date (YYYY-MM-DD) | Version | Description                                                                                                                                              |
|:------------------|:--------|:---------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2026-03-04        | 1.0.0   | Initial public release. Added system description in EN/IT and repository structure (`doc/`, `task/`, `data/`, deliverable templates, and static assets). |
| 2026-03-04        | 1.1.0   | Added `task/Task_01.md` and `doc/deliverable/01_ProjetcManagement.md`                                                                                    |
| 2026-04-15        | 1.2.0   | Added the official documentation and `src/` as the repository area for the system implementation.                                                        |
