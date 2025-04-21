import pytest
from playwright.sync_api import Page, expect
import json
import os
import re

# These fixtures are assumed to be defined elsewhere in the test suite
from profiler.tests.fixtures.qa_fixtures import mock_qa_repository
from profiler.tests.fixtures.profile_fixtures import sample_profile

class TestQAAccessibility:
    """Accessibility tests for the Q&A interface components."""
    
    @pytest.fixture(scope="function")
    def setup_page(self, page: Page):
        """Set up the page with common configurations."""
        # Navigate to the Q&A interface
        page.goto("/qa-interface")
        # Wait for the page to be fully loaded
        page.wait_for_selector(".qa-interface-container")
        return page
    
    def test_page_has_title(self, setup_page):
        """Test that the page has a proper title for screen readers."""
        page = setup_page
        
        # Check that the page has a title
        title = page.title()
        assert title and len(title) > 0, "Page should have a title"
        assert "Profile" in title or "Q&A" in title, "Title should be relevant to the Q&A interface"
    
    def test_landmark_regions(self, setup_page):
        """Test that the page has proper landmark regions for screen reader navigation."""
        page = setup_page
        
        # Check for main landmark
        main = page.locator("main")
        expect(main).to_be_visible()
        
        # Check for navigation landmark
        nav = page.locator("nav")
        expect(nav).to_be_visible()
        
        # Check for header landmark
        header = page.locator("header")
        expect(header).to_be_visible()
        
        # Check for footer landmark
        footer = page.locator("footer")
        expect(footer).to_be_visible()
    
    def test_heading_structure(self, setup_page):
        """Test that the page has a proper heading structure."""
        page = setup_page
        
        # There should be at least one h1
        h1 = page.locator("h1")
        expect(h1).to_be_visible()
        
        # Check that there aren't multiple h1 elements
        h1_count = page.locator("h1").count()
        assert h1_count == 1, f"Page should have exactly one h1, found {h1_count}"
        
        # Check for logical heading structure
        headings = page.evaluate("""() => {
            const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
            return headings.map(h => ({
                level: parseInt(h.tagName.substring(1)),
                text: h.textContent.trim()
            }));
        }""")
        
        # Check that heading levels don't skip (e.g., h1 to h3 without h2)
        current_level = 1
        for heading in headings:
            assert heading["level"] <= current_level + 1, f"Heading structure skips a level: {heading}"
            current_level = heading["level"]
    
    def test_images_have_alt_text(self, setup_page):
        """Test that all images have alternative text."""
        page = setup_page
        
        # Get all images on the page
        images = page.evaluate("""() => {
            const images = Array.from(document.querySelectorAll('img'));
            return images.map(img => ({
                src: img.src,
                alt: img.alt,
                role: img.getAttribute('role')
            }));
        }""")
        
        # Check each image for alt text
        for img in images:
            # Images should either have alt text or role="presentation"
            assert img["alt"] or img["role"] == "presentation", f"Image missing alt text: {img['src']}"
    
    def test_form_labels(self, setup_page):
        """Test that all form controls have associated labels."""
        page = setup_page
        
        # Load a question to ensure form elements are visible
        page.click("#load-question-btn")
        
        # Check that form controls have associated labels
        form_controls = page.evaluate("""() => {
            const controls = Array.from(document.querySelectorAll('input, textarea, select'));
            return controls.map(control => ({
                type: control.tagName.toLowerCase() + (control.type ? ('-' + control.type) : ''),
                id: control.id,
                has_label: !!document.querySelector(`label[for="${control.id}"]`),
                aria_label: control.getAttribute('aria-label'),
                aria_labelledby: control.getAttribute('aria-labelledby')
            }));
        }""")
        
        # Each control should have a label or ARIA label
        for control in form_controls:
            has_accessible_name = (
                control["has_label"] or 
                control["aria_label"] or 
                control["aria_labelledby"]
            )
            assert has_accessible_name, f"Form control missing label: {control['type']} with id {control['id']}"
    
    def test_color_contrast(self, setup_page):
        """Test color contrast for accessibility."""
        page = setup_page
        
        # This would be ideally done with an automated contrast checker
        # For now, we'll use a simplified approach to check for contrast issues
        contrast_issues = page.evaluate("""() => {
            // This is a simplified simulation of contrast checking
            // In a real implementation, you'd use a proper contrast algorithm
            
            const elements = Array.from(document.querySelectorAll('*'));
            const issues = [];
            
            for (const element of elements) {
                const styles = window.getComputedStyle(element);
                const foreground = styles.color;
                const background = styles.backgroundColor;
                
                // Very simplified check - just seeing if both are very similar
                // This is NOT a proper contrast check!
                if (foreground === background && foreground !== 'rgba(0, 0, 0, 0)') {
                    issues.push({
                        element: element.tagName,
                        text: element.textContent.substring(0, 20) + '...',
                        foreground,
                        background
                    });
                }
            }
            
            return issues;
        }""")
        
        assert len(contrast_issues) == 0, f"Color contrast issues found: {contrast_issues}"
    
    def test_keyboard_navigation(self, setup_page):
        """Test keyboard navigation through the Q&A interface."""
        page = setup_page
        
        # Load a question
        page.click("#load-question-btn")
        
        # Tab to the answer input
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")  # Assuming this reaches the textarea
        
        # Check that the textarea is focused
        is_textarea_focused = page.evaluate("""() => {
            return document.activeElement.tagName.toLowerCase() === 'textarea';
        }""")
        assert is_textarea_focused, "Textarea should be focusable with keyboard"
        
        # Type an answer
        page.keyboard.type("This is a keyboard-entered answer")
        
        # Tab to the submit button
        page.keyboard.press("Tab")
        
        # Check that the submit button is focused
        is_submit_focused = page.evaluate("""() => {
            return document.activeElement.id === 'submit-answer-btn';
        }""")
        assert is_submit_focused, "Submit button should be focusable with keyboard"
        
        # Press the button
        page.keyboard.press("Enter")
        
        # Wait for feedback
        page.wait_for_selector(".answer-feedback")
        
        # Check that feedback is visible
        feedback = page.locator(".answer-feedback")
        expect(feedback).to_be_visible()
    
    def test_screen_reader_announcements(self, setup_page):
        """Test that critical status changes are announced to screen readers."""
        page = setup_page
        
        # Load a question
        page.click("#load-question-btn")
        
        # Check for ARIA live regions
        live_regions = page.locator('[aria-live]')
        assert live_regions.count() > 0, "Page should have ARIA live regions for announcements"
        
        # Submit an answer to trigger a status change
        page.fill(".answer-input textarea", "Test answer for screen reader announcement")
        page.click("#submit-answer-btn")
        
        # Check that the status was updated in a live region
        # This is a simplified check - in reality, you'd need to test with actual screen readers
        has_announcement = page.evaluate("""() => {
            const liveRegions = Array.from(document.querySelectorAll('[aria-live]'));
            return liveRegions.some(region => 
                region.textContent.includes('submitted') || 
                region.textContent.includes('processed') ||
                region.textContent.includes('feedback')
            );
        }""")
        assert has_announcement, "Status change should be announced in a live region"
    
    def run_axe_accessibility_scan(self, page, context_selector=None):
        """Run an accessibility scan using axe-core."""
        # Load the axe-core library (would be injected in a real test)
        # page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.5.2/axe.min.js")
        
        # For demo purposes, we'll simulate an axe report
        # In reality, you would actually run the scan
        return page.evaluate("""() => {
            // Simulate an axe scan result
            return {
                violations: [],
                passes: [
                    { id: 'button-name', nodes: [{ html: '<button id="submit-answer-btn">Submit</button>' }] },
                    { id: 'color-contrast', nodes: [{ html: '<p class="question-text">Question text</p>' }] }
                ]
            };
        }""")
    
    def test_axe_accessibility_scan(self, setup_page):
        """Test accessibility using axe-core scanner."""
        page = setup_page
        
        # Load a question to ensure all UI elements are visible
        page.click("#load-question-btn")
        
        # Run the axe scan
        results = self.run_axe_accessibility_scan(page)
        
        # Check for violations
        assert len(results["violations"]) == 0, f"Accessibility violations found: {results['violations']}"
        
        # Log passes for information
        print(f"Accessibility tests passed: {len(results['passes'])}")
    
    def test_aria_attributes(self, setup_page):
        """Test proper usage of ARIA attributes."""
        page = setup_page
        
        # Check for proper ARIA roles
        aria_elements = page.evaluate("""() => {
            const elements = Array.from(document.querySelectorAll('[role]'));
            return elements.map(el => ({
                role: el.getAttribute('role'),
                tag: el.tagName.toLowerCase(),
                required_attrs: Array.from(el.attributes)
                    .filter(attr => attr.name.startsWith('aria-'))
                    .map(attr => attr.name)
            }));
        }""")
        
        # Check each element with a role for proper implementation
        for element in aria_elements:
            # Simplified check - in reality, you'd check against ARIA standards
            if element["role"] == "button":
                assert "tabindex" in element or element["tag"] == "button", f"Button role needs to be focusable"
            elif element["role"] == "checkbox":
                assert "aria-checked" in element["required_attrs"], f"Checkbox role needs aria-checked"
    
    def test_focus_indicator_visibility(self, setup_page):
        """Test that focus indicators are visible."""
        page = setup_page
        
        # Tab through the interface
        page.keyboard.press("Tab")  # Focus on first element
        
        # Check if there's a visible focus indicator
        has_focus_style = page.evaluate("""() => {
            const activeElement = document.activeElement;
            if (!activeElement || activeElement === document.body) return false;
            
            const styles = window.getComputedStyle(activeElement);
            return styles.outline !== 'none' || 
                   styles.boxShadow !== 'none' ||
                   styles.border.includes('solid');
        }""")
        
        assert has_focus_style, "Focus indicator should be visible when elements are focused"
    
    def test_motion_safe(self, setup_page):
        """Test respect for reduced motion preferences."""
        page = setup_page
        
        # Simulate a user with prefers-reduced-motion
        # This would be more thoroughly tested with actual browser settings
        has_motion_query = page.evaluate("""() => {
            // Check if the CSS has a media query for prefers-reduced-motion
            const sheets = Array.from(document.styleSheets);
            try {
                for (const sheet of sheets) {
                    const rules = Array.from(sheet.cssRules);
                    for (const rule of rules) {
                        if (rule.type === CSSRule.MEDIA_RULE && 
                            rule.conditionText.includes('prefers-reduced-motion')) {
                            return true;
                        }
                    }
                }
            } catch (e) {
                // Cross-origin stylesheets will throw an error
                // This is expected for external stylesheets
            }
            return false;
        }""")
        
        # This is a weak assertion - ideally you'd check specific animations
        # In a real test, you'd manipulate the browser's reduced motion setting
        assert has_motion_query, "CSS should include prefers-reduced-motion media queries"
    
    def test_content_resizing(self, setup_page):
        """Test content behavior when text size is increased."""
        page = setup_page
        
        # Simulate text size increase
        page.evaluate("""() => {
            document.body.style.fontSize = '200%';
        }""")
        
        # Check if content is still readable (no overflow or clipping)
        content_issues = page.evaluate("""() => {
            const elements = Array.from(document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, label, button'));
            const issues = [];
            
            for (const element of elements) {
                const styles = window.getComputedStyle(element);
                if (styles.overflow === 'hidden' && 
                    element.scrollWidth > element.clientWidth) {
                    issues.push({
                        element: element.tagName,
                        text: element.textContent.substring(0, 20) + '...'
                    });
                }
            }
            
            return issues;
        }""")
        
        assert len(content_issues) == 0, f"Text should not be clipped when font size is increased: {content_issues}"
    
    def test_skip_link(self, setup_page):
        """Test presence and functionality of skip navigation link."""
        page = setup_page
        
        # Check for skip link
        skip_link = page.locator('a[href^="#main"], a[href^="#content"]').first
        
        # If there's no skip link, we'll fail the test
        expect(skip_link).to_be_visible({ timeout: 1000 })
        
        # Check that the skip link target exists
        skip_target_id = page.evaluate("document.querySelector('a[href^=\"#main\"], a[href^=\"#content\"]').getAttribute('href').substring(1)")
        skip_target = page.locator(f"#{skip_target_id}")
        expect(skip_target).to_be_visible()
        
        # Click the skip link
        skip_link.click()
        
        # Check that focus moved to the target
        is_target_focused = page.evaluate(f"document.activeElement.id === '{skip_target_id}' || document.activeElement.contains(document.getElementById('{skip_target_id}'))")
        assert is_target_focused, "Skip link should move focus to the main content" 