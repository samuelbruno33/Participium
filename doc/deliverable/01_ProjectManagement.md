# Product Breakdown Structure (PBS)

| ID   | Deliverable                                 | Type           | Notes                                                                                                                  |
|:-----|:--------------------------------------------|:---------------|:-----------------------------------------------------------------------------------------------------------------------|
| S1   | Backend                                     | Software       | The main logic and background services of the application.                                                             |
| S1.1 | Account management service                  | Software       | Handles user registration, roles (citizens, operators, admins), and profile settings like email preferences.           |
| S1.2 | Report and Workflow management service      | Software       | The core module. It saves report text, handles photo uploads (up to 3), and tracks the report's status (Pending, etc.).|
| S1.3 | Map and Geo-Location service                | Software       | Dedicated to handling latitude/longitude coordinates and OpenStreetMap integration to show issues on the map.          |
| S1.4 | Communication and Notification service      | Software       | Generates in-platform alerts, handles the "follow" feature, sends emails, and manages direct messages.                 |
| S1.5 | Analytics service                           | Software       | Calculates time trends for public views and generates advanced data for admins (like the top 1% reporters).            |
| S2   | Frontend (Web Client Responsive)            | Software       | The web interface for all users. We only need a responsive web app, no native mobile apps are required.                |
| I1   | Web application deployment platform         | Infrastructure | The server environment used to host our website.                                                                       |
| I2   | Storage (report photos)                     | Infrastructure | Dedicated space to save the photos uploaded by users.                                                                  |
| I3   | Relational Database                         | Infrastructure | The database to store users, reports, categories, and messages.                                                        |
| I4   | Email service                               | Infrastructure | The service used to send automated email notifications.                                                                |
| I5   | Backup and disaster recovery                | Infrastructure | System to save data copies and restore them if something goes wrong.                                                   |
| D1   | Requirements document                       | Documentation  | A list of what the system needs to do (functional and non-functional requirements).                                    |
| D2   | Architecture and design document            | Documentation  | Diagrams and explanations of how the system is built.                                                                  |
| D3   | Test documentation (test plan, test report) | Documentation  | How we test the system and the results of those tests.                                                                 |
| D4   | User manual and documentation               | Documentation  | Simple instructions on how to use the platform.                                                                        |
| D5   | API documentation                           | Documentation  | Technical guide explaining how the front-end and back-end talk to each other.                                          |

![Product Breakdown Structure Diagram](SWE_Participium_PBS_Tree.png)

---

# Work Breakdown Structure (WBS)

### WBS with traceability to PBS
| ID  | Work package | Traced PBS outputs (IDs) |
|:----|:-------------|:--------------------------|
| #.# |              |                           |


---

# Gantt, dependencies, and critical path

## Activity table
| ID | Activity | Duration | Dependencies | Start | End | Critical | Milestone |
|:---|:---------|:---------|:-------------|:------|:----|:------|:---------|
| R# |          |          |              |       |     |       |          |


## Critical path
`X → X → X → ...`



---

# Risk Management

**Scales and thresholds**
- **Probability (P)**: 1 (rare) … 5 (almost certain)
- **Impact (I)**: 1 (minor) … 5 (critical)
- **Exposure**: `P × I` (range 1–25)

Risk level thresholds (by exposure):
- **Low**: 1–5
- **Medium**: 6–10
- **High**: 11–16
- **Very High**: >16



## Risks table
| ID | Risk | Category | P | I | P×I | Level | Mitigation / Response strategy |
|:---|:-----|:---------|--:|--:|----:|:------|:-------------------------------|
|  |      |          |   |   |     |       |                                |


