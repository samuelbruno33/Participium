# 1) Stakeholders

| ID     | Stakeholder name     | Description                                                                 | Role                                                                                  | Main concerns                                                                                  |
|:-------|:---------------------|:----------------------------------------------------------------------------|:--------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------|
| STK-01 | Unregistered User    | Visitor accessing the platform without authentication.                      | Consult public reports and explore issues on the map.                                 | Ease of use, accessibility, clarity of information, no mandatory registration barriers.        |
| STK-02 | Registered Citizen   | Authenticated user who interacts actively with the platform.                | Submit reports, upload photos, track status, follow issues, communicate with offices. | Usability, responsiveness, transparency of report status, privacy of personal data.            |
| STK-03 | Admin                | Platform-level manager with extended privileges.                            | Manage users, oversee system activity, access analytics, enforce policies.            | System security, data integrity, moderation workload, reliability of analytics.                |
| STK-04 | Municipal Office     | Public authority responsible for handling reported issues.                  | Review reports, validate submissions, assign tasks, manage resolution workflows.      | Workload management, efficiency, accuracy of reports, accountability, clear communication.     |
| STK-05 | System Administrator | Technical operator responsible for infrastructure and system maintenance.   | Maintain infrastructure, ensure deployment, backups, security, and system performance.| System reliability, uptime, scalability, security threats, disaster recovery readiness.        |

---

# 2) Context Diagram

![Context Diagram](../../data/img/contextDiagram.png)

---

# 3) Interfaces

| ID    | Interface | Actor       | Physical interface | Logical interface |
|:------|:----------|:------------|:-------------------|:------------------|
| IF-01 | User Interface | Unregistered User                    | Smartphone/PC with internet connection           | Web GUI         |
| IF-02 | User Interface | Registered Citizen                   | Smartphone/PC with internet connection           | Web GUI         |
| IF-03 | User Interface | Admin                                | Smartphone/PC with internet connection           | Web GUI         |
| IF-04 | User Interface | Municipal Office                     | Workstation/PC with internet connection          | Web GUI         |
| IF-05 | User Interface | System Administrator                 | Workstation with secure access (SSH/VPN)         | Web GUI         |
| IF-06 | User Interface | Map Geo-Location Service             | Internet connection            | Map/Geo-Location APIs             |
| IF-07 | External System Interface | Authentication System     | Internet connection            | Authentication APIs               |
| IF-08 | External System Interface | Relational Database Service |  Cloud Network connection      | SQL/Database APIs               |
| IF-09 | External System Interface | Cloud Hosting and Storage System    | Cloud Network connection       | Cloud Storage APIs                |
| IF-10 | External System Interface | Notification Service               | Internet connection  | Notification APIs       |


---

# 4) Personas

| ID     | Name | Role | Background / Context | Goals | Constraints | Devices / Usage setting | Accessibility / Additional needs |
|:-------|:-----|:-----|:---------------------|:------|:------------|:------------------------|:---------------------------------|
| PER-01 |      |      |                      |       |             |                         |                                  |
| PER-02 |      |      |                      |       |             |                         |                                  |
| PER-03 |      |      |                      |       |             |                         |                                  |
| PER-04 |      |      |                      |       |             |                         |                                  |
| PER-05 |      |      |                      |       |             |                         |                                  |
| PER-06 |      |      |                      |       |             |                         |                                  |
| PER-07 |      |      |                      |       |             |                         |                                  |
| PER-08 |      |      |                      |       |             |                         |                                  |



---

# 5) User Stories

| ID    | Persona/Role | User story (As a… I want… so that…) |
|:------|:-------------|:------------------------------------|
| US-01 | Unregistered User/ Registered Citizen  | As an Unregistered User/Registered Citizen, I want to explore reports so that I can understand issues in my city                                     |
| US-02 | Unregistered User/ Registered Citizen    | As an Unregistered User/Registered Citizen, I want to see updates of reports over time so that I can track their progress                             |
| US-03 | Unregistered User/ Registered Citizen    | As an Unregistered User/Registered Citizen I want to view public analytics filtered by category or by day/week/month so that I can analyze trends                                  |
| US-04 | Registered Citizen      | As a Registered Citizen, I want to report issues on the map so that I can notify the Municipal Office about problems                               |
| US-05 | Registered Citizen      | As a Registered Citizen, I want to track updates on my created reports so that I can know their status                                     |
| US-06 | Registered Citizen      | As a Registered Citizen, I want to receive notifications on followed reports (optionally by email) so that I stay informed                                   |
| US-07 | Registered Citizen      | As a Registered Citizen, I want to upload photos to a report so that I can provide visual evidence |
| US-08 | Registered Citizen             | As a Registered Citizen, I want to mark a report as anonymous so that my identity is not publicly visible.                                      |
| US-09 | Registered Citizen             | As a Registered Citizen, I want to assign a category to a report so that it can be handled by the correct Municipal Office                                      |
| US-10 | Registered Citizen             | As a Registered Citizen, I want to send messages to the Municipal Office so that I can provide or receive clarifications                                      |
| US-11 | Municipal Office             | As a Municipal Office, I want to review incoming reports so that I can assess their validity         |
| US-12 | Municipal Office             | As a Municipal Office, I want to assign tasks so that reports are handled by the appropriate team         |
| US-13 | Municipal Office             | As a Municipal Office, I want to update the status of reports so that citizens are informed about the progress         |
| US-14 | Municipal Office             | As a Municipal Office, I want to validate or reject reports so that only relevant issues are processed          |
| US-15 | Municipal Office             | As a Municipal Office, I want to request clarification from citizens so that I can better understand reported issues          |


---

# 6) Functional Requirements (FR)

| ID    | Requirement statement (The system shall…) | Priority | User story ID | Notes |
|:------|:------------------------------------------|:---------|:--------------|:------|
| FR-XX |                                           |          |               |       |


---

# 7) Non-Functional Requirements (NFR)

| ID     | Category | Requirement statement | Metric / Target | Verification                           | Priority | Notes |
|:-------|:---------|:----------------------|:----------------|:---------------------------------------|:---------|:------|
| NFR-XX |          |                       |                 |                                        |          |       |