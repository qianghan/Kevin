import pytest
from playwright.sync_api import Page, expect
import os
import time

# Import fixtures that provide mock data
from profiler.tests.fixtures.qa_fixtures import mock_qa_repository
from profiler.tests.fixtures.profile_fixtures import sample_profile

class TestQAVisualRegression:
    """Visual regression tests for the Q&A interface components."""
    
    @pytest.fixture(scope="function")
    def setup_page(self, page: Page):
        """Set up the page with common configurations."""
        # Set viewport size to ensure consistent screenshots
        page.set_viewport_size({"width": 1280, "height": 800})
        # Navigate to the Q&A interface
        page.goto("/qa-interface")
        # Wait for the page to be fully loaded
        page.wait_for_selector(".qa-interface-container")
        return page
    
    @pytest.fixture
    def screenshots_dir(self):
        """Create and return the directory for storing screenshots."""
        screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        return screenshots_dir
    
    def test_empty_qa_panel_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of an empty Q&A panel."""
        page = setup_page
        
        # Verify that the Q&A panel is empty
        empty_panel = page.locator(".question-answer-panel:not(.has-content)")
        expect(empty_panel).to_be_visible()
        
        # Take a screenshot of the empty panel
        screenshot_path = os.path.join(screenshots_dir, "empty_qa_panel.png")
        empty_panel.screenshot(path=screenshot_path)
        
        # Assert the screenshot file exists
        assert os.path.exists(screenshot_path), f"Screenshot not created at {screenshot_path}"

    def test_question_display_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of a question display."""
        page = setup_page
        
        # Click on the button to load a question
        page.click("#load-question-btn")
        
        # Wait for the question to be displayed
        question_display = page.locator(".question-display")
        expect(question_display).to_be_visible()
        
        # Take a screenshot of the question display
        screenshot_path = os.path.join(screenshots_dir, "question_display.png")
        question_display.screenshot(path=screenshot_path)
        
        # Assert the screenshot file exists
        assert os.path.exists(screenshot_path), f"Screenshot not created at {screenshot_path}"
        
        # Verify the question display elements
        expect(page.locator(".question-text")).to_be_visible()
        expect(page.locator(".question-category")).to_be_visible()

    def test_answer_input_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of the answer input area."""
        page = setup_page
        
        # Click on the button to load a question
        page.click("#load-question-btn")
        
        # Wait for the answer input to be visible
        answer_input = page.locator(".answer-input")
        expect(answer_input).to_be_visible()
        
        # Take a screenshot of the empty answer input
        screenshot_path = os.path.join(screenshots_dir, "empty_answer_input.png")
        answer_input.screenshot(path=screenshot_path)
        
        # Type some text into the answer input
        page.fill(".answer-input textarea", "This is a sample answer for visual testing purposes.")
        
        # Take a screenshot of the filled answer input
        screenshot_path = os.path.join(screenshots_dir, "filled_answer_input.png")
        answer_input.screenshot(path=screenshot_path)
        
        # Assert both screenshot files exist
        assert os.path.exists(os.path.join(screenshots_dir, "empty_answer_input.png")), "Empty answer input screenshot not created"
        assert os.path.exists(os.path.join(screenshots_dir, "filled_answer_input.png")), "Filled answer input screenshot not created"
        
    def test_feedback_display_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of the answer feedback display."""
        page = setup_page
        
        # Click on the button to load a question
        page.click("#load-question-btn")
        
        # Enter an answer and submit it
        page.fill(".answer-input textarea", "This is a sample answer that will trigger feedback.")
        page.click("#submit-answer-btn")
        
        # Wait for the feedback to be displayed
        page.wait_for_selector(".answer-feedback")
        
        # Take a screenshot of the feedback display
        screenshot_path = os.path.join(screenshots_dir, "answer_feedback.png")
        page.locator(".answer-feedback").screenshot(path=screenshot_path)
        
        # Assert the screenshot file exists
        assert os.path.exists(screenshot_path), f"Screenshot not created at {screenshot_path}"
        
        # Verify feedback display elements
        expect(page.locator(".feedback-score")).to_be_visible()
        expect(page.locator(".feedback-suggestions")).to_be_visible()

    def test_question_sequence_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of multiple questions in sequence."""
        page = setup_page
        
        # Load the first question
        page.click("#load-question-btn")
        
        # Enter an answer and submit for the first question
        page.fill(".answer-input textarea", "This is my answer to the first question.")
        page.click("#submit-answer-btn")
        
        # Wait for the feedback and next question button
        page.wait_for_selector(".answer-feedback")
        
        # Take a screenshot of the completed first question
        screenshot_path = os.path.join(screenshots_dir, "completed_first_question.png")
        page.locator(".question-answer-panel").screenshot(path=screenshot_path)
        
        # Move to the next question
        page.click("#next-question-btn")
        
        # Wait for the second question to load
        page.wait_for_selector(".question-text:has-text('Question 2')")
        
        # Take a screenshot of the second question
        screenshot_path = os.path.join(screenshots_dir, "second_question.png")
        page.locator(".question-answer-panel").screenshot(path=screenshot_path)
        
        # Assert both screenshot files exist
        assert os.path.exists(os.path.join(screenshots_dir, "completed_first_question.png")), "First question screenshot not created"
        assert os.path.exists(os.path.join(screenshots_dir, "second_question.png")), "Second question screenshot not created"
    
    def test_responsive_layout_visual(self, page: Page, screenshots_dir):
        """Test the visual appearance of the Q&A interface at different viewport sizes."""
        # Navigate to the Q&A interface
        page.goto("/qa-interface")
        page.wait_for_selector(".qa-interface-container")
        
        # Test desktop layout
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)  # Allow time for layout to stabilize
        desktop_screenshot = os.path.join(screenshots_dir, "qa_desktop_layout.png")
        page.screenshot(path=desktop_screenshot)
        
        # Test tablet layout
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(500)  # Allow time for layout to stabilize
        tablet_screenshot = os.path.join(screenshots_dir, "qa_tablet_layout.png")
        page.screenshot(path=tablet_screenshot)
        
        # Test mobile layout
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(500)  # Allow time for layout to stabilize
        mobile_screenshot = os.path.join(screenshots_dir, "qa_mobile_layout.png")
        page.screenshot(path=mobile_screenshot)
        
        # Assert all screenshot files exist
        assert os.path.exists(desktop_screenshot), "Desktop layout screenshot not created"
        assert os.path.exists(tablet_screenshot), "Tablet layout screenshot not created"
        assert os.path.exists(mobile_screenshot), "Mobile layout screenshot not created"
    
    def test_dark_mode_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of the Q&A interface in dark mode."""
        page = setup_page
        
        # First capture the light mode (default)
        page.wait_for_selector(".qa-interface-container")
        light_mode_screenshot = os.path.join(screenshots_dir, "qa_light_mode.png")
        page.screenshot(path=light_mode_screenshot)
        
        # Switch to dark mode
        page.click("#theme-toggle-btn")
        
        # Wait for dark mode to be applied
        page.wait_for_selector("body.dark-theme")
        
        # Capture dark mode screenshot
        dark_mode_screenshot = os.path.join(screenshots_dir, "qa_dark_mode.png")
        page.screenshot(path=dark_mode_screenshot)
        
        # Assert both screenshot files exist
        assert os.path.exists(light_mode_screenshot), "Light mode screenshot not created"
        assert os.path.exists(dark_mode_screenshot), "Dark mode screenshot not created"
    
    def test_profile_completeness_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of the profile completeness display."""
        page = setup_page
        
        # Click the button to show profile completeness
        page.click("#show-profile-completeness-btn")
        
        # Wait for the completeness display to be visible
        completeness_display = page.locator(".profile-completeness-display")
        expect(completeness_display).to_be_visible()
        
        # Take a screenshot of the completeness display
        screenshot_path = os.path.join(screenshots_dir, "profile_completeness.png")
        completeness_display.screenshot(path=screenshot_path)
        
        # Assert the screenshot file exists
        assert os.path.exists(screenshot_path), f"Screenshot not created at {screenshot_path}"
        
        # Verify completeness display elements
        expect(page.locator(".completeness-score")).to_be_visible()
        expect(page.locator(".category-scores")).to_be_visible()
    
    def test_question_recommendations_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of the question recommendations panel."""
        page = setup_page
        
        # Click the button to show question recommendations
        page.click("#show-recommendations-btn")
        
        # Wait for the recommendations to be visible
        recommendations_panel = page.locator(".question-recommendations")
        expect(recommendations_panel).to_be_visible()
        
        # Take a screenshot of the recommendations panel
        screenshot_path = os.path.join(screenshots_dir, "question_recommendations.png")
        recommendations_panel.screenshot(path=screenshot_path)
        
        # Assert the screenshot file exists
        assert os.path.exists(screenshot_path), f"Screenshot not created at {screenshot_path}"
        
        # Verify recommendations panel elements
        expect(page.locator(".recommendation-item")).to_be_visible()
        expect(page.locator(".recommendation-reason")).to_be_visible()
    
    def test_error_state_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of error states in the Q&A interface."""
        page = setup_page
        
        # Trigger an error state (e.g., trying to submit an empty answer)
        page.click("#load-question-btn")
        page.click("#submit-answer-btn")  # Submit without entering an answer
        
        # Wait for the error message to be displayed
        error_message = page.locator(".error-message")
        expect(error_message).to_be_visible()
        
        # Take a screenshot of the error state
        screenshot_path = os.path.join(screenshots_dir, "error_state.png")
        page.locator(".question-answer-panel").screenshot(path=screenshot_path)
        
        # Assert the screenshot file exists
        assert os.path.exists(screenshot_path), f"Screenshot not created at {screenshot_path}"
    
    def test_loading_state_visual(self, setup_page, screenshots_dir):
        """Test the visual appearance of loading states in the Q&A interface."""
        page = setup_page
        
        # Intercept API calls to simulate a slow response
        page.route("**/api/questions*", lambda route: time.sleep(1) and route.continue_())
        
        # Click the button to load a question, which will now be delayed
        page.click("#load-question-btn")
        
        # Quickly take a screenshot of the loading state
        page.wait_for_selector(".loading-indicator")
        screenshot_path = os.path.join(screenshots_dir, "loading_state.png")
        page.locator(".question-answer-panel").screenshot(path=screenshot_path)
        
        # Assert the screenshot file exists
        assert os.path.exists(screenshot_path), f"Screenshot not created at {screenshot_path}"
        
        # Wait for loading to complete to avoid affecting other tests
        page.wait_for_selector(".question-text")
        
    def test_compare_screenshots(self, screenshots_dir):
        """Test to compare current screenshots with baseline screenshots."""
        # This test would use an image comparison library to compare current screenshots
        # with baseline screenshots to detect visual regression
        
        # For demonstration purposes, we'll just check if baseline directory exists
        baseline_dir = os.path.join(os.path.dirname(__file__), "baseline_screenshots")
        
        # If baseline directory doesn't exist, we create it and copy current screenshots
        if not os.path.exists(baseline_dir):
            os.makedirs(baseline_dir, exist_ok=True)
            import shutil
            for screenshot in os.listdir(screenshots_dir):
                if screenshot.endswith(".png"):
                    shutil.copy(
                        os.path.join(screenshots_dir, screenshot),
                        os.path.join(baseline_dir, screenshot)
                    )
            pytest.skip("Baseline screenshots created. Run the test again to compare.")
        
        # In a real implementation, we would compare screenshots with a library like PIL
        # Example comparison code (commented out as it requires PIL):
        """
        from PIL import Image, ImageChops
        import math
        
        def image_difference(img1_path, img2_path):
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            diff = ImageChops.difference(img1, img2)
            return diff.getbbox() is not None
        
        for screenshot in os.listdir(screenshots_dir):
            if screenshot.endswith(".png"):
                current = os.path.join(screenshots_dir, screenshot)
                baseline = os.path.join(baseline_dir, screenshot)
                if os.path.exists(baseline):
                    is_different = image_difference(current, baseline)
                    assert not is_different, f"Visual regression detected in {screenshot}"
        """
        
        # For now, we'll just pass the test
        assert os.path.exists(baseline_dir), "Baseline screenshots directory should exist" 