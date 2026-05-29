## 1 `participium.services.auth_service.AuthService.authenticate`

Suggested test file: `test_authenticate.py`

Prototype: `authenticate(identifier: str, password: str) -> User`

| TC-ID | identifier | password | Expected | Fixture |
| :---- | :--------- | :------- | :------- | :------ |
| TC-01 | "maria.rossi" | "CorrectPassword1!" | **User returned** | Active user (email verified) |
| TC-02 | "maria.rossi@example.com" | "CorrectPassword1!" | **User returned** | Active user (email verified) |
| TC-03 | "maria.rossi" | "WrongPassword" | **AuthenticationError** | Active user (email verified) |
| TC-04 | "nonexistent.user" | "CorrectPassword1!" | **AuthenticationError** | No user exists |
| TC-05 | "luca.bianchi" | "CorrectPassword1!" | **AuthenticationError** | Inactive user (email verified) |
| TC-06 | "giulia.verdi" | "CorrectPassword1!" | **AuthenticationError** | Active user (email not verified) |
| TC-07 | "" | "CorrectPassword1!" | **AuthenticationError** | No user exists |
| TC-08 | "maria.rossi" | "" | **AuthenticationError** | Active user (email verified) |
| TC-09 | None | "CorrectPassword1!" | **AttributeError** | Invalid input (None identifier) |
| TC-10 | "maria.rossi" | None | **AttributeError** | Invalid input (None password) |
| TC-11 | "   " | "CorrectPassword1!" | **AuthenticationError** | No user exists |
| TC-12 | "mario.neri" | "CorrectPassword1!" | **AuthenticationError** | Active user (wrong hash) |


## 2 `participium.core.utils.parse_date`

Suggested test file: `test_parse_date.py`

Prototype: `parse_date(value: str | None) -> datetime | None`

| TC-ID | value | Expected | Fixture |
| :---- | :---- | :------- | :------ |
| TC-01 | `None` | **`None` returned** | None required |
| TC-02 | `""` (empty string) | **`None` returned** | None required |
| TC-03 | `"2026-05-14"` (ISO date-only) | **`datetime(2026, 5, 14, 0, 0, 0)`** (naive) | None required |
| TC-04 | `"2026-05-14T10:30:45"` (ISO datetime, no tz) | **`datetime(2026, 5, 14, 10, 30, 45)`** (naive) | None required |
| TC-05 | `"2026-05-14T10:30:00+02:00"` (ISO datetime with tz) | **`datetime` with `utcoffset() == +02:00`** | None required |
| TC-06 | `"14/05/2026"` (non-ISO format) | **`ValueError`** | None required |
| TC-07 | `"2026-13-50"` (out-of-range month/day) | **`ValueError`** | None required |
| TC-08 | `" "` (whitespace-only, truthy) | **`ValueError`** | None required |
| TC-09 | `20260514` (non-string truthy input) | **`TypeError`** | None required |

## 3 `participium.core.status_flow.ensure_transition_allowed`

Suggested test file: `test_status_flow.py`

Prototype: `ensure_transition_allowed(current_status: ReportStatus, next_status: ReportStatus) -> bool`

Allowed transitions:
`Pending Approval -> Pending Approval | Assigned | Rejected`;
`Assigned -> Assigned | In Progress | Suspended | Resolved`;
`In Progress -> In Progress | Suspended | Resolved`;
`Suspended -> Suspended | In Progress | Resolved`;
`Rejected -> Rejected`;
`Resolved -> Resolved`.

| TC-ID | current_status | next_status | Expected | Fixture |
|:------| :------------- | :---------- | :------- | :------ |
| TC-01 | ANY valid `current_status` | Corresponding valid `next_status` (e.g., "Pending Approval" -> "Assigned") | `True` | None required |
| TC-02 | ANY valid `current_status` | Same as `current_status` (Self-transition) | `True` | None required |
| TC-03 | "Pending Approval" | "In Progress" / "Suspended" / "Resolved" (Skipping states) | `ValueError` | None required |
| TC-04 | "Assigned" / "In Progress" / "Suspended" | "Pending Approval" (Backward flow) or "Rejected" (Invalid flow) | `ValueError` | None required |
| TC-05 | "In Progress" / "Suspended" | "Assigned" (Backward flow) | `ValueError` | None required |
| TC-06 | "Resolved" / "Rejected" | ANY state different from `current_status` (Escaping terminal state) | `ValueError` | None required |

## 4 `participium.services.report_service.ReportService.create_report`

Suggested test file: `test_create_report.py`

Prototype: `create_report(reporter: User, category_id: int | str | None, title: str | None, description: str | None, latitude: float | str | None, longitude: float | str | None, photos: list[FileStorage], is_anonymous: bool = False) -> Report`

| TC-ID | reporter | category_id          | title       | description       | latitude             | longitude             | photos                | is_anonymous | Expected        | Fixture                                                                                |
| :---- | :------- | :------------------- | :---------- | :---------------- | :------------------- | :-------------------- | :-------------------- | :----------- | :-------------- | :------------------------------------------------------------------------------------- |
| TC-01 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | Report          | session, report_repository, storage_service, notification_service, category_repository |
| TC-02 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | 3 valid and 1 invalid | false        | Report          | session, report_repository, storage_service, notification_service, category_repository |
| TC-03 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | 1 valid and 1 invalid | true         | Report          | session, report_repository, storage_service, notification_service, category_repository |
| TC-04 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | 3 valid and 1 invalid | true         | Report          | session, report_repository, storage_service, notification_service, category_repository |
| TC-05 | User     | **non-existent int** | valid title | valid description | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-06 | User     | **inactive int**     | valid title | valid description | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-07 | User     | **None**             | valid title | valid description | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-08 | User     | valid int            | **None**    | valid description | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-09 | User     | valid int            | **""**      | valid description | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-10 | User     | valid int            | valid title | **None**          | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-11 | User     | valid int            | valid title | **""**            | valid latitude       | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-12 | User     | valid int            | valid title | valid description | **invalid latitude** | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-13 | User     | valid int            | valid title | valid description | **""**               | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-14 | User     | valid int            | valid title | valid description | **None**             | valid longitude       | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-15 | User     | valid int            | valid title | valid description | valid latitude       | **invalid longitude** | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-16 | User     | valid int            | valid title | valid description | valid latitude       | **""**                | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-17 | User     | valid int            | valid title | valid description | valid latitude       | **None**              | 1 valid and 1 invalid | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-18 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | **empty list**        | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-19 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | **1 invalid**         | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-20 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | **4 valid**           | false        | ValidationError | session, report_repository, storage_service, notification_service, category_repository |
| TC-21 | User     | valid int            | valid title | valid description | valid latitude       | valid longitude       | **None**              | false        | TypeError | session, report_repository, storage_service, notification_service, category_repository |




## 5 `participium.services.report_service.ReportService.update_status`

Suggested test file: `test_update_status.py`

Prototype: `update_status(report_id: int, operator: User, next_status_value: str, note: str | None = None) -> Report`

| TC-ID | report_id               | operator                                | next_status_value | note         | Expected           | Fixture                                                                                                    |
| :---- | :---------------------- | :-------------------------------------- | :---------------- | :----------- | :----------------- | :--------------------------------------------------------------------------------------------------------- |
| TC-01 | existing report         | ADMIN                                   | valid             | "valid note" | Report             | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-02 | existing report         | OPERATOR with correct category_id       | valid             | "valid note" | Report             | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-03 | existing report         | ADMIN                                   | valid             | None         | Report             | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-04 | existing report         | OPERATOR with correct category_id       | valid             | None         | Report             | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-05 | **non-existing report** | ADMIN                                   | valid             | "valid note" | NotFoundError      | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-06 | **None**                | ADMIN                                   | valid             | "valid note" | NotFoundError      | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-07 | existing report         | **OPERATOR with incorrect category_id** | valid             | "valid note" | AuthorizationError | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-08 | existing report         | **other role**                          | valid             | "valid note" | AuthorizationError | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-09 | existing report         | ADMIN                                   | **invalid**       | "valid note" | ValidationError    | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-10 | existing report         | ADMIN                                   | **non-existing**  | "valid note" | ValidationError    | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |
| TC-11 | existing report         | ADMIN                                   | **"Rejection"**   | **None**     | ValidationError    | mocked `session`, `report_repository`, `category_repository`, `storage_service` and `notification_service` |

## 6 `participium.services.report_service.ReportService.list_public_reports`

Suggested test file: `test_public_reports.py`

Prototype: `list_public_reports(category_id: int | None = None, status: ReportStatus | None = None, date_from: datetime | None = None, date_to: datetime | None = None, sort: str = "desc") -> list[Report]`

| TC-ID | category_id | status | date_from | date_to | sort | Expected | Fixture |
| :---- | :---------- | :----- | :-------- | :------ | :--- | :------- | :------ |
| TC-01 | `None` | `None` | `None` | `None` | `"desc"` (default) | Repository called with `public_only=True` and all filters `None`, `sort="desc"`; result list returned unchanged | mocked `report_repository` returning a non-empty list |
| TC-02 | `7` | `None` | `None` | `None` | `"desc"` | Repository called with `category_id=7`, other filters unchanged | mocked `report_repository` returning `[]` |
| TC-03 | `None` | `ReportStatus.RESOLVED` | `None` | `None` | `"desc"` | Repository called with `status=ReportStatus.RESOLVED` (forwarded as-is) | mocked `report_repository` returning `[]` |
| TC-04 | `None` | `None` | `datetime(2026, 1, 1)` | `None` | `"desc"` | Repository called with the given `date_from` | mocked `report_repository` returning `[]` |
| TC-05 | `None` | `None` | `None` | `datetime(2026, 12, 31, 23, 59, 59)` | `"desc"` | Repository called with the given `date_to` | mocked `report_repository` returning `[]` |
| TC-06 | `None` | `None` | `None` | `None` | `"asc"` | Repository called with `sort="asc"` | mocked `report_repository` returning `[]` |
| TC-07 | `3` | `ReportStatus.IN_PROGRESS` | `datetime(2026, 1, 1)` | `datetime(2026, 6, 30)` | `"asc"` | Repository called with **all** filters forwarded together | mocked `report_repository` returning `[]` |
| TC-08 | `99` | `None` | `None` | `None` | `"desc"` | Service returns `[]` unchanged | mocked `report_repository` returning `[]` |
| TC-09 | `None` | `None` | `None` | `None` | `"desc"` | Service returns the repository list verbatim (same object, same length) | mocked `report_repository` returning a 3-element list |
| TC-10 | `1` | `ReportStatus.ASSIGNED` | `None` | `None` | `"desc"` | Repository call kwargs include `public_only=True` regardless of other inputs | mocked `report_repository` returning `[]` |


## 7 `participium.services.messaging_service.MessagingService.send_message`

Suggested test file: `test_send_message.py`

Prototype: `send_message(report: Report, sender: User, body: str) -> Message`

| TC-ID | report | sender | body | Expected | Fixture |
| :---- | :----- | :----- | :--- | :------- | :------ |
| TC-01 | Report(id=10, reporter=User(id=2)) | User(id=1, role=ADMIN, first_name, last_name) | "Normal message" | Message created; sender_id=1; recipient_id=2; repo.add called; notify called; commit called | report exists; reporter user exists; admin sender exists; notification service exists; repository exists |
| TC-02 | Report(id=10) | None | "Hello?" | AuthorizationError | report exists; sender is None |
| TC-03 | Report(id=10, reporter_id=1, status_history=[]) | User(id=1, role=CITIZEN) | "Hello?" | ValidationError (no recipient available) | report exists; reporter exists; no messages in repository; empty status history |
| TC-04 | None | User(id=1, role=ADMIN) | "Valid content" | AttributeError | sender exists; report is None |
| TC-05 | Report(id=10) | User(id=1, role=ADMIN) | "   " | ValidationError (empty body) | report exists; sender exists; body is whitespace |
| TC-06 | Report(id=10, reporter_id=2) | User(id=5, role=CITIZEN, id≠reporter) | "Normal Message" | AuthorizationError | report exists; sender exists; sender is not reporter |
| TC-07 | Report(id=10, category_id=3, reporter=User(id=2)) | User(id=5, role=OPERATOR, category_id=3) | "Operator response" | Message created; recipient_id=2; commit called | report exists; reporter exists; operator exists; matching category; valid repository and session |
| TC-08 | Report(id=10, category_id=3) | User(id=5, role=OPERATOR, category_id=7) | "Trying to send this message." | AuthorizationError | report exists; reporter exists; operator exists; category mismatch |

## 8 `participium.core.security.verify_password`

Suggested test file: `test_verify_password.py`

Prototype: `verify_password(password: str, password_hash: str) -> bool`

| TC-ID | password | password_hash | Expected | Fixture |
| :---- | :------- | :------------ | :------- | :------ |
| TC-01 | "CorrectPassword1!" | hash of "CorrectPassword1!" | **True** | correct_hash |
| TC-02 | "WrongPassword" | hash of "CorrectPassword1!" | **False** | correct_hash |
| TC-03 | "CorrectPassword1!" | "not_a_valid_hash" | **False** | None |
| TC-04 | "correctpassword1!" | hash of "CorrectPassword1!" | **False** | correct_hash |
| TC-05 | "" | hash of "CorrectPassword1!" | **False** | correct_hash |
| TC-06 | " CorrectPassword1!" | hash of "CorrectPassword1!" | **False** | correct_hash |
| TC-07 | "CorrectPassword1! " | hash of "CorrectPassword1!" | **False** | correct_hash |
| TC-08 | None | hash of "CorrectPassword1!" | **AttributeError** | correct_hash |
| TC-09 | "CorrectPassword1!" | "" | **False** | None |

## 9 `participium.services.notification_service.NotificationService.create_notification`

Suggested test file: `test_create_notification.py`

Prototype: `create_notification(user: User | None, notification_type: NotificationType, title: str, body: str, report: Report | None = None) -> Notification | None`

| TC-ID | user | notification_type | title | body | report | Expected | Fixture |
| :---- | :--- | :---------------- | :---- | :--- | :----- | :------- | :------ |
| TC-01 | User(id=1, email_notifications_enabled=False) | STATUS_CHANGE | "Update" | "Your report has been assigned to an operator." | None | Notification created; repo.add called; email NOT sent | user exists; notifications disabled; repo exists; email gateway exists |
| TC-02 | None | MESSAGE | "New Message" | "You have a new message." | None | None returned; no repo call; no email sent | user is None; repo exists; email gateway exists |
| TC-03 | User(id=1) | STATUS_CHANGE | "Report Update" | "Body of the notification" | Report(id=10) | Notification created with report_id=10; repo.add called | user exists; report exists; repo exists |
| TC-04 | User(id=2, email, email_notifications_enabled=True) | SYSTEM | "System Alert" | "System is sending a notification." | None | Notification created; repo.add called; email sent | user exists with email; email notifications enabled; repo exists; email gateway exists |
| TC-05 | User(id=3, email, email_notifications_enabled=True) | MESSAGE | "Hi" | "Hello" | None | Notification created; email failure; repo.add called | user exists with email; email enabled; email gateway exists but throws error; repo exists |

## 10 `participium.services.user_service.UserService.update_profile`

Suggested test file: `test_update_profile.py`

Prototype: `update_profile(user: User, username: str | None = None, first_name: str | None = None, last_name: str | None = None, email_notifications_enabled: bool | None = None, profile_picture: FileStorage | None = None) -> User`

| TC-ID   | user | username        | first_name | last_name | email_notifications_enabled | profile_picture | Expected                                                      | Fixture |
|:--------| :--- |:----------------|:-----------|:----------| :-------------------------- | :-------------- |:--------------------------------------------------------------| :------ |
| TC-01   | `ValidUser` | new_user        | John       | Doe       | `True` | `None` | `User` object with all text fields updated                    | `ValidUser` exists in DB |
| TC-02   | `ValidUser` | `None`          | `None`     | `None`    | `False` | `None` | `User` object with only `email_notifications_enabled` updated | `ValidUser` exists in DB |
| TC-03   | `ValidUser` | `None`          | `None`     | `None`    | `None` | `ValidFileStorage` | `User` object with updated `profile_picture_url`              | `ValidUser` exists in DB, Storage System is accessible |
| TC-04   | `ValidUser` | existing_user | `None`     | `None`    | `None` | `None` | `ValidationError`                                             | `ValidUser` exists in DB, another User with "existing_user" username already exists |
| TC-05   | `ValidUser` | `""` (Empty)    | `""`       | `None`    | `None` | `None` | `ValidationError`                                             | `ValidUser` exists in DB |
| TC-06   | `None` | valid_name    | `None`     | `None`    | `None` | `None` | `ValidationError` / `TypeError`                               | None required |