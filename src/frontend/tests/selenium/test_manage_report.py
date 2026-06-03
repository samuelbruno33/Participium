# ---------------------------------------------------------------------------
# NOTE - Flask session and page reload
#
# In some tests the login is repeated after a page reload.
# Following certain updates,
# the backend enters a state that prevents the recognition of the
# user session, causing a redirect to login as if
# the session had expired or it fails to display the operator page.
# ---------------------------------------------------------------------------

from __future__ import annotations

import time
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

BASE_URL = "http://localhost:5173"

OPERATOR_EMAIL = "operator@example.com"
OPERATOR_PASSWORD = "Operator123!"

CITIZEN_EMAIL = "citizen@example.com"
CITIZEN_PASSWORD = "Citizen123!"

TIMEOUT = 20


@pytest.fixture
def operator_driver(driver):
    _login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
    return driver


def wait(driver, seconds: int = TIMEOUT) -> WebDriverWait:
    return WebDriverWait(
        driver,
        seconds,
        ignored_exceptions=[StaleElementReferenceException],
    )


def _force_clear(field) -> None:
    field.click()
    field.send_keys(Keys.CONTROL + "a")
    field.send_keys(Keys.DELETE)
    field.send_keys(Keys.BACKSPACE)
    time.sleep(0.25)

    if (field.get_attribute("value") or "").strip():
        field.click()
        field.send_keys(Keys.CONTROL + "a")
        field.send_keys(Keys.DELETE)
        field.send_keys(Keys.BACKSPACE)
        time.sleep(0.25)

    if (field.get_attribute("value") or "").strip():
        field.parent.execute_script(
            """
            arguments[0].value = '';
            arguments[0].dispatchEvent(new Event('input',  { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """,
            field,
        )
        time.sleep(0.2)


def _fill_field(field, value: str) -> None:
    _force_clear(field)
    field.click()
    field.send_keys(value)
    time.sleep(0.2)

    if field.get_attribute("value") != value:
        _force_clear(field)
        field.click()
        field.send_keys(value)
        time.sleep(0.2)


def _login(driver, email: str, password: str) -> None:
    driver.get(f"{BASE_URL}/login")
    wait(driver).until(EC.presence_of_element_located((By.ID, "login-identifier")))
    time.sleep(1.0)

    email_field = wait(driver).until(EC.element_to_be_clickable((By.ID, "login-identifier")))
    password_field = wait(driver).until(EC.element_to_be_clickable((By.ID, "login-password")))

    _fill_field(email_field, email)
    _fill_field(password_field, password)

    assert email_field.get_attribute("value") == email
    assert password_field.get_attribute("value") == password

    wait(driver).until(EC.element_to_be_clickable((By.ID, "login-submit"))).click()
    wait(driver).until(EC.url_changes(f"{BASE_URL}/login"))


def _logout(driver) -> None:
    try:
        driver.find_element(By.ID, "logout-button").click()
        wait(driver).until(EC.url_contains("/login"))
    except Exception:
        driver.get(f"{BASE_URL}/login")
        time.sleep(0.8)


def _ensure_logged_in_as_operator(driver) -> None:
    if "/login" in driver.current_url:
        _login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)


def _go_to_operator(driver) -> None:
    driver.get(f"{BASE_URL}/operator")
    time.sleep(0.8)
    _ensure_logged_in_as_operator(driver)

    if "/operator" not in driver.current_url:
        driver.get(f"{BASE_URL}/operator")

    wait(driver).until(EC.presence_of_element_located((By.ID, "operator-page")))
    wait(driver).until(EC.presence_of_element_located((By.ID, "assigned-reports-table-body")))


def _go_to_dashboard(driver) -> None:
    driver.get(f"{BASE_URL}/dashboard")
    time.sleep(0.8)

    if "/login" in driver.current_url:
        _login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
        driver.get(f"{BASE_URL}/dashboard")

    wait(driver).until(EC.presence_of_element_located((By.ID, "dashboard-page")))
    wait(driver).until(EC.presence_of_element_located((By.ID, "notifications-list")))


def _first_assigned_report_id(driver) -> int | None:
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        rows = driver.find_elements(By.CSS_SELECTOR, 'tr[id^="assigned-report-row-"]')
        if rows:
            return int(rows[0].get_attribute("id").split("-")[-1])
        time.sleep(0.5)
    return None


def _set_status(driver, report_id: int, status_value: str) -> None:
    select_el = wait(driver).until(
        EC.presence_of_element_located((By.ID, f"assigned-report-status-{report_id}"))
    )
    Select(select_el).select_by_value(status_value)


def _set_note(driver, report_id: int, note: str) -> None:
    note_input = wait(driver).until(
        EC.element_to_be_clickable((By.ID, f"assigned-report-note-{report_id}"))
    )
    _fill_field(note_input, note)


def _clear_note(driver, report_id: int) -> None:
    note_input = wait(driver).until(
        EC.element_to_be_clickable((By.ID, f"assigned-report-note-{report_id}"))
    )
    _force_clear(note_input)


def _click_update(driver, report_id: int) -> None:
    wait(driver).until(
        EC.element_to_be_clickable((By.ID, f"assigned-report-update-{report_id}"))
    ).click()


def _wait_for_status_updated(
        driver,
        report_id: int,
        expected_value: str,
        timeout: int = TIMEOUT,
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            select_el = driver.find_element(By.ID, f"assigned-report-status-{report_id}")
            current = Select(select_el).first_selected_option.get_attribute("value")
            if current == expected_value:
                return True
        except StaleElementReferenceException:
            pass
        time.sleep(0.5)
    return False


def _reload_and_get_status(driver, report_id: int) -> str | None:
    _go_to_operator(driver)
    try:
        select_el = wait(driver, 10).until(
            EC.presence_of_element_located((By.ID, f"assigned-report-status-{report_id}"))
        )
        return Select(select_el).first_selected_option.get_attribute("value")
    except TimeoutException:
        return None


def _wait_for_error_containing(driver, keyword: str, timeout: int = 8) -> bool:
    known_ids = [
        "operator-error",
        "update-report-error",
        "assigned-report-error",
        "status-update-error",
    ]
    deadline = time.time() + timeout
    while time.time() < deadline:
        for cid in known_ids:
            els = driver.find_elements(By.ID, cid)
            if els and els[0].is_displayed() and keyword.lower() in els[0].text.lower():
                return True

        for el in driver.find_elements(By.CLASS_NAME, "error-text"):
            try:
                if el.is_displayed() and keyword.lower() in el.text.lower():
                    return True
            except StaleElementReferenceException:
                pass

        try:
            if keyword.lower() in driver.find_element(By.TAG_NAME, "body").text.lower():
                return True
        except Exception:
            pass

        time.sleep(0.4)
    return False


def _get_notification_texts(driver) -> list[str]:
    items = driver.find_elements(By.CSS_SELECTOR, "#notifications-list li")
    return [el.text.strip() for el in items if el.text.strip()]


def _wait_for_notification_containing(
        driver,
        keyword: str,
        timeout: int = TIMEOUT,
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        texts = _get_notification_texts(driver)
        if any(keyword.lower() in t.lower() for t in texts):
            return True
        time.sleep(0.8)
    return False


@pytest.mark.implementation_bug("Flask session expired")
class TestOperatorMainScenario:

    def test_operator_can_login_and_see_operator_page(self, driver):
        _login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
        _go_to_operator(driver)
        assert driver.find_element(By.ID, "operator-title").is_displayed()

    def test_assigned_reports_table_is_visible(self, operator_driver):
        _go_to_operator(operator_driver)
        rows = operator_driver.find_elements(
            By.CSS_SELECTOR, 'tr[id^="assigned-report-row-"]'
        )
        assert len(rows) > 0

    def test_assigned_report_shows_status_select(self, operator_driver):
        _go_to_operator(operator_driver)
        report_id = _first_assigned_report_id(operator_driver)
        assert report_id is not None
        select_el = operator_driver.find_element(
            By.ID, f"assigned-report-status-{report_id}"
        )
        assert select_el.is_displayed()

    def test_update_status_to_in_progress(self, operator_driver):
        _go_to_operator(operator_driver)
        report_id = _first_assigned_report_id(operator_driver)
        assert report_id is not None
        _set_status(operator_driver, report_id, "In Progress")
        _set_note(operator_driver, report_id, "Taken in charge.")
        _click_update(operator_driver, report_id)
        assert _wait_for_status_updated(operator_driver, report_id, "In Progress")

    def test_update_status_to_suspended(self, operator_driver):
        _go_to_operator(operator_driver)
        report_id = _first_assigned_report_id(operator_driver)
        assert report_id is not None
        _set_status(operator_driver, report_id, "Suspended")
        _set_note(operator_driver, report_id, "Waiting for information.")
        _click_update(operator_driver, report_id)
        assert _wait_for_status_updated(operator_driver, report_id, "Suspended")

    # MOVED BEFORE "RESOLVED" TO AVOID TERMINAL STATE LEAKAGE
    def test_status_persists_after_page_reload(self, operator_driver):
        _go_to_operator(operator_driver)
        report_id = _first_assigned_report_id(operator_driver)
        assert report_id is not None
        _set_status(operator_driver, report_id, "In Progress")
        _set_note(operator_driver, report_id, "Persistence test.")
        _click_update(operator_driver, report_id)
        assert _wait_for_status_updated(operator_driver, report_id, "In Progress")
        persisted = _reload_and_get_status(operator_driver, report_id)
        assert persisted == "In Progress", (
            f"After reload, status is '{persisted}', expected 'In Progress'. "
            "The backend might not have saved the update."
        )

    def test_update_status_to_resolved_with_note(self, operator_driver):
        _go_to_operator(operator_driver)
        rows = operator_driver.find_elements(
            By.CSS_SELECTOR, 'tr[id^="assigned-report-row-"]'
        )
        assert rows
        report_id = int(rows[-1].get_attribute("id").split("-")[-1])
        _set_status(operator_driver, report_id, "Resolved")
        _set_note(operator_driver, report_id, "Problem resolved.")
        _click_update(operator_driver, report_id)
        assert _wait_for_status_updated(operator_driver, report_id, "Resolved")


@pytest.mark.implementation_bug("Flask session expired")
class TestOperatorRejectedExtension:

    def test_reject_without_note_shows_error(self, operator_driver):
        _go_to_operator(operator_driver)
        report_id = _first_assigned_report_id(operator_driver)
        assert report_id is not None
        _set_status(operator_driver, report_id, "Rejected")
        _clear_note(operator_driver, report_id)
        _click_update(operator_driver, report_id)
        assert _wait_for_error_containing(operator_driver, "Rejection")

    def test_reject_with_note_succeeds(self, operator_driver):
        _go_to_operator(operator_driver)
        report_id = _first_assigned_report_id(operator_driver)
        assert report_id is not None
        _set_status(operator_driver, report_id, "Rejected")
        _set_note(operator_driver, report_id, "Not of municipal competence.")
        _click_update(operator_driver, report_id)
        assert _wait_for_status_updated(operator_driver, report_id, "Rejected")


@pytest.mark.implementation_bug("Flask session expired")
class TestOperatorUI:

    def test_operator_page_has_title(self, operator_driver):
        _go_to_operator(operator_driver)
        title = operator_driver.find_element(By.ID, "operator-title")
        assert title.is_displayed()
        assert len(title.text.strip()) > 0

    def test_update_button_is_clickable(self, operator_driver):
        _go_to_operator(operator_driver)
        report_id = _first_assigned_report_id(operator_driver)
        assert report_id is not None
        btn = operator_driver.find_element(By.ID, f"assigned-report-update-{report_id}")
        assert btn.is_enabled()

    def test_non_operator_cannot_access_page(self, driver):
        driver.get(f"{BASE_URL}/operator")
        deadline = time.time() + 5
        success = False
        while time.time() < deadline:
            # Check if redirected successfully
            if "/login" in driver.current_url:
                success = True
                break
            # Or if an error component is rendered
            try:
                els = driver.find_elements(By.CLASS_NAME, "error-text")
                if any(el.is_displayed() for el in els):
                    success = True
                    break
            except Exception:
                # Catch Javascript/Stale exceptions during React route transitions
                pass
            time.sleep(0.5)

        assert success, "Page should redirect to login or show an error."


@pytest.mark.implementation_bug("Flask session expired")
class TestOperatorNotifiesCitizen:

    def test_citizen_receives_notification_after_status_update(self, driver):
        _login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
        _go_to_operator(driver)

        report_id = _first_assigned_report_id(driver)
        assert report_id is not None, "No assigned report found."

        _set_status(driver, report_id, "In Progress")
        _set_note(driver, report_id, "Taken in charge by automated test.")
        _click_update(driver, report_id)
        assert _wait_for_status_updated(driver, report_id, "In Progress"), (
            f"The status of report {report_id} did not become 'In Progress'."
        )

        _logout(driver)
        _login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
        _go_to_dashboard(driver)

        notification_texts = _get_notification_texts(driver)
        assert len(notification_texts) > 0, (
            "No in-platform notifications found in the citizen dashboard."
        )

    def test_citizen_notification_mentions_report_or_status(self, driver):
        _login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
        _go_to_operator(driver)

        report_id = _first_assigned_report_id(driver)
        assert report_id is not None

        _set_status(driver, report_id, "Suspended")
        _set_note(driver, report_id, "Test notification content.")
        _click_update(driver, report_id)
        _wait_for_status_updated(driver, report_id, "Suspended")

        _logout(driver)
        _login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
        _go_to_dashboard(driver)

        notification_texts = _get_notification_texts(driver)
        assert notification_texts, "No notifications found in the citizen dashboard."

        keywords = [str(report_id), "suspended", "in progress", "resolved", "rejected", "report"]
        found = any(
            any(kw.lower() in t.lower() for kw in keywords)
            for t in notification_texts
        )
        assert found, (
            f"No notification mentions report {report_id} or a recognizable status. "
            f"Texts found: {notification_texts}"
        )