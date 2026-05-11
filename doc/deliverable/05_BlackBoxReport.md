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
|  |  |  |  |

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

| TC-ID | reporter | category_id | title | description | latitude | longitude | photos | is_anonymous | Expected | Fixture |
| :---- | :------- | :---------- | :---- | :---------- | :------- | :-------- | :----- | :----------- | :------- | :------ |
|  |  |  |  |  |  |  |  |  |  |  |

## 5 `participium.services.report_service.ReportService.update_status`

Suggested test file: `test_update_status.py`

Prototype: `update_status(report_id: int, operator: User, next_status_value: str, note: str | None = None) -> Report`

| TC-ID | report_id | operator | next_status_value | note | Expected | Fixture |
| :---- | :-------- | :------- | :---------------- | :--- | :------- | :------ |
|  |  |  |  |  |  |  |

## 6 `participium.services.report_service.ReportService.list_public_reports`

Suggested test file: `test_public_reports.py`

Prototype: `list_public_reports(category_id: int | None = None, status: ReportStatus | None = None, date_from: datetime | None = None, date_to: datetime | None = None, sort: str = "desc") -> list[Report]`

| TC-ID | category_id | status | date_from | date_to | sort | Expected | Fixture |
| :---- | :---------- | :----- | :-------- | :------ | :--- | :------- | :------ |
|  |  |  |  |  |  |  |  |


## 7 `participium.services.messaging_service.MessagingService.send_message`

Suggested test file: `test_send_message.py`

Prototype: `send_message(report: Report, sender: User, body: str) -> Message`

| TC-ID | report | sender | body | Expected | Fixture |
| :---- | :----- | :----- | :--- | :------- | :------ |
|  |  |  |  |  |  |

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
|  |  |  |  |  |  |  |  |

## 10 `participium.services.user_service.UserService.update_profile`

Suggested test file: `test_update_profile.py`

Prototype: `update_profile(user: User, username: str | None = None, first_name: str | None = None, last_name: str | None = None, email_notifications_enabled: bool | None = None, profile_picture: FileStorage | None = None) -> User`

| TC-ID   | user | username        | first_name | last_name | email_notifications_enabled | profile_picture | Expected                                                      | Fixture |
|:--------| :--- |:----------------|:-----------|:----------| :-------------------------- | :-------------- |:--------------------------------------------------------------| :------ |
| TC-01   | `ValidUser` | new_user        | John       | Doe       | `True` | `None` | `User` object with all text fields updated                    | `ValidUser` exists in DB |
| TC-02   | `ValidUser` | `None`          | `None`     | `None`    | `False` | `None` | `User` object with only `email_notifications_enabled` updated | `ValidUser` exists in DB |
| TC-03   | `ValidUser` | `None`          | `None`     | `None`    | `None` | `ValidFileStorage` | `User` object with updated `profile_picture_url`              | `ValidUser` exists in DB, Storage System is accessible |
| TC-04   | `ValidUser` | "existing_user" | `None`     | `None`    | `None` | `None` | `ValidationError`                                             | `ValidUser` exists in DB, another User with "existing_user" username already exists |
| TC-05   | `ValidUser` | `""` (Empty)    | `""`       | `None`    | `None` | `None` | `ValidationError`                                             | `ValidUser` exists in DB |
| TC-06   | `None` | "valid_name"    | `None`     | `None`    | `None` | `None` | `ValidationError` / `TypeError`                               | None required |