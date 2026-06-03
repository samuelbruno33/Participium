# Participium - Bug Report Log

---

## Bug 1: Missing Email Format Validation on User Registration

| Field | Value |
|---|---|
| **Date** | 2026-06-03 |
| **Module** | Authentication |
| **Severity** | Medium |
| **Found during** | Task 8 (Postman API Acceptance Testing) |

---

### Description

During the implementation of API Acceptance Testing via Postman, a validation bypass was discovered in the registration flow. The backend successfully creates a new user account and returns a `201 Created` status even if the provided email string does not match a valid email format (e.g., passing `"invalid-email-format"` instead of `user@domain.com`).

---

### Root Cause

In `src/backend/participium/services/auth_service.py`, the `register_user` method verifies the presence of the `email` field and ensures it is unique:

```python
required = ["username", "first_name", "last_name", "email", "password"]
# ...
if self.user_repository.get_by_email(payload["email"]):
    raise ValidationError("Email already in use.")
```

However, it lacks a standard validation mechanism (e.g., regex pattern matching or a validation library) to ensure the string is a semantically correct email address before persisting the `User` entity to the database.

---

### Steps to Reproduce

1. Send a `POST` request to `/api/v1/auth/register`.
2. Provide the following JSON payload:

```json
{
  "username": "test_bug_user",
  "first_name": "Test",
  "last_name": "User",
  "email": "invalid-email-format",
  "password": "ValidPassword123!"
}
```

3. **Actual Result:** The server responds with `201 Created` and creates the user.
4. **Expected Result:** The server should return `400 Bad Request` with a `ValidationError` indicating that the email format is invalid.