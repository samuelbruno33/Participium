# 1) Stakeholders

| ID   | Stakeholder name   | Description                                 | Role                                         | Main concerns                                         |
|:-------|:---------------------|:----------------------------------------------------------------------------|:--------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------|
| STK-01 | Unregistered User  | Visitor accessing the platform without authentication.           | Consult public reports and explore issues on the map.                 | Ease of use, accessibility, clarity of information, no mandatory registration barriers.    |
| STK-02 | Registered Citizen  | Authenticated user who interacts actively with the platform.        | Submit reports, upload photos, track status, follow issues, communicate with offices. | Usability, responsiveness, transparency of report status, privacy of personal data.      |
| STK-03 | Admin        | Platform-level manager with extended privileges.              | Manage users, oversee system activity, access analytics, enforce policies.      | System security, data integrity, moderation workload, reliability of analytics.        |
| STK-04 | Municipal Office   | Public authority responsible for handling reported issues.         | Review reports, validate submissions, assign tasks, manage resolution workflows.   | Workload management, efficiency, accuracy of reports, accountability, clear communication.   |
| STK-05 | System Administrator | Technical operator responsible for infrastructure and system maintenance.  | Maintain infrastructure, ensure deployment, backups, security, and system performance.| System reliability, uptime, scalability, security threats, disaster recovery readiness.    |

---

# 2) Context Diagram

![Context Diagram](../../data/img/contextDiagram.png)

---

# 3) Interfaces

| ID  | Interface | Actor    | Physical interface | Logical interface |
|:------|:----------|:------------|:-------------------|:------------------|
| IF-01 | User Interface | Unregistered User          | Smartphone/PC with internet connection      | Web GUI     |
| IF-02 | User Interface | Registered Citizen          | Smartphone/PC with internet connection      | Web GUI     |
| IF-03 | User Interface | Admin                | Smartphone/PC with internet connection      | Web GUI     |
| IF-04 | User Interface | Municipal Office           | Workstation/PC with internet connection     | Web GUI     |
| IF-05 | User Interface | System Administrator         | Workstation with secure access (SSH/VPN)     | Web GUI     |
| IF-06 | External System Interface | Map Geo-Location Service       | Internet connection      | Map/Geo-Location APIs       |
| IF-07 | External System Interface | Authentication System   | Internet connection      | Authentication APIs        |
| IF-08 | External System Interface | Relational Database Service | Cloud Network connection   | SQL/Database APIs        |
| IF-09 | External System Interface | Cloud Hosting and Storage System  | Cloud Network connection    | Cloud Storage APIs        |
| IF-10 | External System Interface | Notification Service        | Internet connection | Notification APIs    |

---

# 4) Personas

| ID     | Name | Role | Background / Context | Goals | Constraints | Devices / Usage setting | Accessibility / Additional needs |
|:-------|:-----|:-----|:---------------------|:------|:------------|:------------------------|:---------------------------------|
| PER-01 | Marco Rossi | Registered Citizen | 45yo commuter who cycles to work daily. Frequently encounters road hazards. | Wants to report issues on the map, correctly categorize them, upload photos for evidence, and track their status | Has limited time, doesn't want to fill out long, complex forms while commuting. | Smartphone (outdoor usage, mobile network). | Needs a high-contrast map UI for outdoor visibility and large, easy-to-tap buttons. |
| PER-02 | Giulia Bianchi | Municipal Office | 38yo public worker in the infrastructure department. Deals with dozens of citizen reports daily. | Wants to review incoming reports, assign tasks to the right team, update statuses, and request clarifications from citizens if needed. | High daily workload, needs to avoid duplicate reports and confusing workflows. | Desktop PC (indoor office environment). | Relies on clear, structured table views and the ability to easily filter data. |
| PER-03 | Carlo Verdone | Unregistered User | 72yo retired local resident. Very attached to his neighborhood decorum but not tech-savvy. | Wants to explore reports to understand city issues, track their progress over time, and view public analytics to see trends. | Reluctant to share personal data, frustrated by mandatory login screens. | Tablet (used at home on Wi-Fi). | Requires extremely simple navigation, large font sizes, and clear status indicators. |
| PER-04 | Andrea Verdi | Admin | 30yo platform administrator at the municipality. | Wants to oversee general system activity, manage user roles, and extract advanced analytics for the city council. | Needs accurate data aggregation, deals with strict privacy compliance. | Laptop (office or remote working). | Needs a comprehensive dashboard with clear data visualization and charts. |
| PER-05 | Elena Neri | System Administrator | 40yo IT infrastructure specialist hired by the municipality. | Wants to ensure platform uptime, manage secure backups, and monitor database performance. | Strict security protocols and zero-downtime requirements. | Workstation with VPN access. | Requires secure authentication, terminal/CLI access, and clear system logs. |
| PER-06 | Serena Gialli | Registered Citizen | 22yo university student. Active in local environmental groups, often reporting illegal waste dumping. | Wants to mark her sensitive reports as anonymous and send direct messages to the Municipal Office to provide further clarifications. | Expects fast responses. Dislikes clunky, outdated web interfaces. | Smartphone (mostly used on the go) and Laptop. | Needs a highly responsive, modern UI with a clear messaging interface. |
| PER-07 | Roberto Conti | Municipal Office | 50yo field inspector for the city. Spends most of his day outside verifying the validity of citizen reports. | Wants to validate or reject reports directly from the field so that only relevant issues are processed. | Operates in areas with potentially poor internet connectivity. Needs quick actions. | Company tablet (outdoor usage, sometimes under direct sunlight). | Requires a streamlined interface with offline-tolerant features or low data usage. |
| PER-08 | Luigi Ferrara | Registered Citizen | 60yo owner of a small shop in the city center. Deeply cares about the decorum near his business. | Wants to receive optional email notifications on reports he follows, so he can stay informed without checking the app. | Very busy with his shop, has low tolerance for complex registration steps. | Desktop PC (behind the shop counter) and Smartphone. | Relies heavily on the email notification system. Prefers reading detailed updates in his inbox. |

---

# 5) User Stories

| ID  | Persona/Role | User story (As a… I want… so that…) |
|:------|:-------------|:------------------------------------|
| US-01 | Unregistered User/ Registered Citizen | As an Unregistered User/Registered Citizen, I want to explore reports so that I can understand issues in my city                   |
| US-02 | Unregistered User/ Registered Citizen  | As an Unregistered User/Registered Citizen, I want to see updates of reports over time so that I can track their progress               |
| US-03 | Unregistered User/ Registered Citizen  | As an Unregistered User/Registered Citizen I want to view public analytics filtered by category or by day/week/month so that I can analyze trends                 |
| US-04 | Registered Citizen   | As a Registered Citizen, I want to report issues on the map so that I can notify the Municipal Office about problems                |
| US-05 | Registered Citizen   | As a Registered Citizen, I want to track updates on my created reports so that I can know their status                   |
| US-06 | Registered Citizen   | As a Registered Citizen, I want to receive notifications on followed reports (optionally by email) so that I stay informed                  |
| US-07 | Registered Citizen   | As a Registered Citizen, I want to upload photos to a report so that I can provide visual evidence |
| US-08 | Registered Citizen       | As a Registered Citizen, I want to mark a report as anonymous so that my identity is not publicly visible.                   |
| US-09 | Registered Citizen       | As a Registered Citizen, I want to assign a category to a report so that it can be handled by the correct Municipal Office                   |
| US-10 | Registered Citizen       | As a Registered Citizen, I want to send messages to the Municipal Office so that I can provide or receive clarifications                   |
| US-11 | Municipal Office       | As a Municipal Office, I want to review incoming reports so that I can assess their validity     |
| US-12 | Municipal Office       | As a Municipal Office, I want to assign tasks so that reports are handled by the appropriate team     |
| US-13 | Municipal Office       | As a Municipal Office, I want to update the status of reports so that citizens are informed about the progress     |
| US-14 | Municipal Office       | As a Municipal Office, I want to validate or reject reports so that only relevant issues are processed     |
| US-15 | Municipal Office       | As a Municipal Office, I want to request clarification from citizens so that I can better understand reported issues     |


---

# 6) Functional Requirements (FR)

| ID  | Requirement statement (The system shall…) | Priority | User story ID | Notes |
|:------|:------------------------------------------|:---------|:--------------|:------|
| FR-XX |                      |     |        |    |


---

# 7) Non-Functional Requirements (NFR)

| ID   | Category | Requirement statement | Metric / Target | Verification              | Priority | Notes |
|:-------|:---------|:----------------------|:----------------|:---------------------------------------|:---------|:------|
| NFR-XX |     |            |         |                    |     |    |