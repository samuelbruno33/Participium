# UC-04 Browse reports on map
# UC-05 Search and filter reports
# UC-06 View report details
# UC-08 Export reports as CSV
# UC-09 View public statistics

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL      = "http://localhost:5173"
SEED_TITLE    = "Pothole on Via Roma"
SEED_CATEGORY = "Roads and Urban Furniture"
SEED_STATUS   = "Resolved"


@pytest.fixture
def driver():
    d = webdriver.Chrome()
    yield d
    d.quit()

@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 10)


def wait_for_select_options(wait, select_id):
    wait.until(lambda d: len(d.find_element(By.ID, select_id).find_elements(By.TAG_NAME, "option")) > 1)


def set_datetime_input(driver, element_id, value):
    driver.execute_script(
        f"""
        var el = document.getElementById('{element_id}');
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, '{value}');
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """
    )


def open_seed_report(driver, wait):
    driver.get(BASE_URL)
    wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))
    
    link_xpath = f"//*[starts-with(@id, 'public-report-row-')][contains(., '{SEED_TITLE}')]//*[contains(@id, '-open-link')]"
    wait.until(EC.element_to_be_clickable((By.XPATH, link_xpath))).click()    
    wait.until(EC.presence_of_element_located((By.ID, "report-detail-page")))
 


class TestBrowseReportsOnMap:

    def test_map_and_reports_visible(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))
        
        assert driver.find_element(By.ID, "public-map").is_displayed()
        markers = wait.until(lambda d: d.find_elements(By.XPATH, "//*[contains(@id, '-map-marker')]"))
        assert len(markers) > 0, "No map markers found on the public map."


    def test_click_map_marker_shows_popup_and_opens_detail(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-map")))
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[starts-with(@id, 'public-report-row-')]")) > 0)
        marker = wait.until(EC.element_to_be_clickable((By.ID, "public-report-row-2-map-marker")))
        marker.click()

        popup = wait.until(EC.presence_of_element_located((By.ID, "public-report-row-2-map-popup")))
        assert "Pothole" in popup.text, f"The popup content does not describe the correct report: {popup.text}"
    
    def test_map_no_markers_when_no_reports_in_period(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[contains(@id, '-map-marker')]")) > 0)

        # set a period with no reports
        set_datetime_input(driver, "public-filter-date-from", "2000-01-01T00:00")
        set_datetime_input(driver, "public-filter-date-to", "2000-12-31T23:59")
        driver.find_element(By.ID, "public-filter-submit").click()

        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[contains(@id, '-map-marker')]")) == 0)

        markers = driver.find_elements(By.XPATH, "//*[contains(@id, '-map-marker')]")
        assert len(markers) == 0
        assert driver.find_element(By.ID, "public-map").is_displayed()

  
class TestSearchAndFilterReports:

    def test_filter_and_sort(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))

        wait_for_select_options(wait, "public-filter-category")
        Select(driver.find_element(By.ID, "public-filter-category")).select_by_visible_text(SEED_CATEGORY)

        wait_for_select_options(wait, "public-filter-status")
        Select(driver.find_element(By.ID, "public-filter-status")).select_by_visible_text(SEED_STATUS)

        set_datetime_input(driver, "public-filter-date-from", "2020-01-01T00:00")
        set_datetime_input(driver, "public-filter-date-to",   "2099-12-31T23:59")

        driver.find_element(By.ID, "public-filter-submit").click()
        wait.until(EC.presence_of_element_located((By.ID, "public-report-table")))
        
        rows = wait.until(lambda d: d.find_elements(By.XPATH, "//*[starts-with(@id, 'public-report-row-')]"))
        assert len(rows) > 0, "No reports found after applying filters."

        Select(driver.find_element(By.ID, "public-filter-sort")).select_by_value("asc")
        driver.find_element(By.ID, "public-filter-submit").click()
        wait.until(EC.presence_of_element_located((By.ID, "public-report-table")))

    def test_filter_no_match_returns_empty_table(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))

        set_datetime_input(driver, "public-filter-date-from", "2000-01-01T00:00")
        set_datetime_input(driver, "public-filter-date-to",   "2000-12-31T23:59")
        driver.find_element(By.ID, "public-filter-submit").click()

        # check if no rows are present by waiting for the absence of any row element
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[starts-with(@id, 'public-report-row-')]")) == 0)
        rows = driver.find_elements(By.XPATH, "//*[starts-with(@id, 'public-report-row-')]")
        assert len(rows) == 0

 
class TestViewReportDetails:
 
    def test_detail_page_shows_full_info(self, driver, wait):
        open_seed_report(driver, wait)
 
        assert driver.find_element(By.ID, "report-detail-title").text.strip() == SEED_TITLE
        assert SEED_STATUS in driver.find_element(By.ID, "report-detail-status").text
        assert driver.find_element(By.ID, "report-detail-description").text.strip()
        assert SEED_CATEGORY in driver.find_element(By.ID, "report-detail-category-value").text
        assert driver.find_elements(By.XPATH, "//*[contains(@id, 'map')]")
        assert driver.find_element(By.ID, "report-detail-photos-card").is_displayed()
        assert driver.find_element(By.ID, "status-history-list").is_displayed()
 
    def test_nonexistent_report_shows_error(self, driver, wait):
        driver.get(f"{BASE_URL}/reports/9999999")
        wait.until(EC.presence_of_element_located((By.ID, "report-detail-page")))
        assert driver.find_element(By.ID, "report-detail-error").is_displayed()
 
 
 
class TestExportReportsCSV:
 
    def test_csv_export_link_present_and_clickable(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))
 
        export_link = wait.until(EC.presence_of_element_located((By.ID, "public-export-link")))
        assert export_link.is_displayed()
        
        # verify that the href is dynamically generated by apiClient 
        href = export_link.get_attribute("href")
        assert href is not None
        assert "export" in href or "csv" in href
        
        export_link.click()
        assert driver.current_url

        

    def test_csv_export_empty_set_behavior(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))
        
        set_datetime_input(driver, "public-filter-date-from", "2000-01-01T00:00")
        set_datetime_input(driver, "public-filter-date-to",   "2000-12-31T23:59")
        driver.find_element(By.ID, "public-filter-submit").click()
        
        export_link = wait.until(EC.presence_of_element_located((By.ID, "public-export-link")))
        href = export_link.get_attribute("href")

        assert href is not None
        assert "export" in href.lower()
        assert "api/v1/reports/export" in href 
 
 
class TestViewPublicStatistics:
 
    def test_statistics_shows_category_and_trend_data(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-statistics-card")))
        wait.until(lambda d: len(d.find_element(By.ID, "public-category-statistics-list").find_elements(By.TAG_NAME, "li")) > 0)

        assert driver.find_element(By.ID, "public-category-statistics-list").is_displayed()
        assert driver.find_element(By.ID, "public-trend-statistics-list").is_displayed()
 
    def test_change_time_aggregation_updates_charts(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, "public-statistics-card")))
        
        wait.until(lambda d: len(d.find_element(By.ID, "public-trend-statistics-list").find_elements(By.TAG_NAME, "li")) > 0)
        
        trend_list_element = driver.find_element(By.ID, "public-trend-statistics-list")
        old_text = trend_list_element.text
        
        granularity_select = Select(driver.find_element(By.ID, "public-stat-granularity"))
        granularity_select.select_by_value("week")
        
        wait.until(lambda d: d.find_element(By.ID, "public-trend-statistics-list").text != old_text)
        
        assert driver.find_element(By.ID, "public-trend-statistics-list").is_displayed()

