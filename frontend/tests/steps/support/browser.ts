import { chromium, Page, Browser } from '@playwright/test';

let browser: Browser;
let page: Page;
const baseUrl = process.env.FRONTEND_URL || 'http://localhost:3000';

/**
 * Initializes the browser for testing
 * 
 * @returns The page object for interaction
 */
export async function initBrowser(): Promise<Page> {
  // Launch browser if not already launched
  if (!browser) {
    console.log('Launching browser');
    browser = await chromium.launch({
      headless: process.env.HEADLESS !== 'false',
      slowMo: process.env.SLOW_MO ? parseInt(process.env.SLOW_MO, 10) : 0,
    });
  }
  
  // Create a new context and page
  const context = await browser.newContext();
  page = await context.newPage();
  
  return page;
}

/**
 * Gets the current page or initializes a new one
 * 
 * @returns The page object for interaction
 */
export async function getPage(): Promise<Page> {
  if (!page) {
    return await initBrowser();
  }
  return page;
}

/**
 * Navigates to a URL, prepending the base URL if needed
 * 
 * @param page The page object
 * @param url The URL to navigate to
 */
export async function navigateTo(page: Page, url: string): Promise<void> {
  const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;
  console.log(`Navigating to ${fullUrl}`);
  await page.goto(fullUrl);
}

/**
 * Closes the browser
 */
export async function closeBrowser(): Promise<void> {
  if (browser) {
    await browser.close();
    browser = null;
    page = null;
  }
} 