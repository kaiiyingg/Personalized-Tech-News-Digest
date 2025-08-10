"""
Accessibility Testing Suite for TechPulse
Tests color contrast, keyboard navigation, screen reader compatibility,
and WCAG 2.1 AA compliance across all pages.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from axe_selenium_python import Axe
import colorsys


class TestAccessibility:
    """Comprehensive accessibility testing suite"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome driver with accessibility options"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_color_contrast_ratios(self, driver, live_server):
        """Test WCAG AA color contrast requirements (4.5:1)"""
        driver.get(live_server.url)
        
        # Define critical text/background combinations
        contrast_tests = [
            ("#ffffff", "#8B5CF6"),  # White text on purple
            ("#e3e3e3", "#2a2e36"),  # Light gray on dark background
            ("#b3b3b3", "#2a2e36"),  # Medium gray on dark background
            ("#ffffff", "#9333ea"),  # White on gradient purple
        ]
        
        for text_color, bg_color in contrast_tests:
            ratio = self.calculate_contrast_ratio(text_color, bg_color)
            assert ratio >= 4.5, f"Contrast ratio {ratio:.2f} fails WCAG AA for {text_color} on {bg_color}"

    def test_keyboard_navigation(self, driver, live_server):
        """Test full keyboard navigation without mouse"""
        driver.get(live_server.url)
        
        # Start from body and tab through all interactive elements
        body = driver.find_element(By.TAG_NAME, "body")
        body.click()
        
        interactive_elements = driver.find_elements(
            By.CSS_SELECTOR, 
            "a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])"
        )
        
        # Test tab navigation
        for i, element in enumerate(interactive_elements):
            body.send_keys(Keys.TAB)
            focused_element = driver.switch_to.active_element
            
            # Verify element is focusable and visible
            assert focused_element.is_displayed(), f"Element {i} not visible when focused"
            assert focused_element.is_enabled(), f"Element {i} not enabled when focused"
            
            # Verify focus indicators are visible
            focus_outline = focused_element.value_of_css_property("outline")
            box_shadow = focused_element.value_of_css_property("box-shadow")
            assert focus_outline != "none" or box_shadow != "none", f"No focus indicator on element {i}"

    def test_screen_reader_compatibility(self, driver, live_server):
        """Test screen reader accessibility"""
        driver.get(live_server.url)
        
        # Test semantic HTML structure
        main_content = driver.find_elements(By.TAG_NAME, "main")
        assert len(main_content) == 1, "Page must have exactly one main landmark"
        
        # Test heading hierarchy
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        heading_levels = [int(h.tag_name[1]) for h in headings]
        
        # Verify proper heading hierarchy (no skipped levels)
        for i in range(1, len(heading_levels)):
            level_jump = heading_levels[i] - heading_levels[i-1]
            assert level_jump <= 1, f"Heading hierarchy skip detected: h{heading_levels[i-1]} to h{heading_levels[i]}"

    def test_aria_labels_and_descriptions(self, driver, live_server):
        """Test ARIA labels for interactive elements"""
        driver.get(live_server.url)
        
        # Test buttons have accessible names
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            accessible_name = (
                button.get_attribute("aria-label") or
                button.get_attribute("aria-labelledby") or
                button.text.strip()
            )
            assert accessible_name, "Button missing accessible name"

        # Test images have alt text
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            assert alt_text is not None, "Image missing alt attribute"

    def test_form_accessibility(self, driver, live_server):
        """Test form accessibility"""
        # Test login form
        driver.get(f"{live_server.url}/login")
        
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for input_element in inputs:
            if input_element.get_attribute("type") not in ["hidden", "submit"]:
                # Check for labels
                input_id = input_element.get_attribute("id")
                if input_id:
                    label = driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    aria_label = input_element.get_attribute("aria-label")
                    aria_labelledby = input_element.get_attribute("aria-labelledby")
                    
                    assert (
                        label or aria_label or aria_labelledby
                    ), f"Input {input_id} missing accessible label"

    def test_wcag_compliance(self, driver, live_server):
        """Test WCAG 2.1 AA compliance using axe-core"""
        driver.get(live_server.url)
        axe = Axe(driver)
        
        # Inject axe-core and run accessibility scan
        axe.inject()
        results = axe.run()
        
        # Assert no violations
        violations = results["violations"]
        if violations:
            violation_details = []
            for violation in violations:
                violation_details.append(f"- {violation['id']}: {violation['description']}")
            
            pytest.fail(f"WCAG violations found:\n" + "\n".join(violation_details))

    def test_mobile_accessibility(self, driver, live_server):
        """Test mobile accessibility and touch targets"""
        driver.set_window_size(375, 667)  # iPhone SE size
        driver.get(live_server.url)
        
        # Test touch target sizes (minimum 44x44px)
        interactive_elements = driver.find_elements(
            By.CSS_SELECTOR, 
            "button, a, input[type='button'], input[type='submit']"
        )
        
        for element in interactive_elements:
            size = element.size
            assert size["width"] >= 44 and size["height"] >= 44, (
                f"Touch target too small: {size['width']}x{size['height']}px"
            )

    @staticmethod
    def calculate_contrast_ratio(color1, color2):
        """Calculate WCAG contrast ratio between two colors"""
        def get_luminance(hex_color):
            # Convert hex to RGB
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Convert to relative luminance
            rgb_norm = [c / 255.0 for c in rgb]
            rgb_linear = [
                c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in rgb_norm
            ]
            
            return 0.2126 * rgb_linear[0] + 0.7152 * rgb_linear[1] + 0.0722 * rgb_linear[2]
        
        lum1 = get_luminance(color1)
        lum2 = get_luminance(color2)
        
        # Ensure lighter color is in numerator
        if lum1 < lum2:
            lum1, lum2 = lum2, lum1
            
        return (lum1 + 0.05) / (lum2 + 0.05)
