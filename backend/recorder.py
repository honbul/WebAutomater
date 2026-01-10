import asyncio
from playwright.async_api import async_playwright
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INJECTED_JS = """
(() => {
    window.__recorderReady = false;
    window.__capturedEvents = [];
    
    function getCssSelector(el) {
        if (!el) return;
        const path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            let selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + el.id;
                path.unshift(selector);
                break;
            } else {
                let sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() == selector)
                       nth++;
                }
                if (nth != 1)
                    selector += ":nth-of-type("+nth+")";
            }
            path.unshift(selector);
            el = el.parentNode;
        }
        return path.join(" > ");
    }

    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM fully loaded. Setting up event listeners...');
        
        document.addEventListener('click', (e) => {
            const selector = getCssSelector(e.target);
            const eventData = {
                type: 'click',
                selector: selector,
                timestamp: Date.now()
            };
            console.log('Event captured:', eventData);
            window.__capturedEvents.push(eventData);
            window.recordEvent(eventData);
        }, true);

        document.addEventListener('input', (e) => {
            const selector = getCssSelector(e.target);
            const eventData = {
                type: 'input',
                selector: selector,
                value: e.target.value,
                timestamp: Date.now()
            };
            console.log('Event captured:', eventData);
            window.__capturedEvents.push(eventData);
            window.recordEvent(eventData);
        }, true);

        document.addEventListener('change', (e) => {
            const selector = getCssSelector(e.target);
            const eventData = {
                type: 'change',
                selector: selector,
                value: e.target.value,
                timestamp: Date.now()
            };
            console.log('Event captured:', eventData);
            window.__capturedEvents.push(eventData);
            window.recordEvent(eventData);
        }, true);

        console.log('Event listeners set up. Recorder is active.');
    });
})();
"""


class Recorder:
    def __init__(self):
        self.events = []
        self.browser = None
        self.page = None
        self.playwright = None
        self.stop_event = asyncio.Event()

    async def handle_event(self, event):
        logger.info(f"Captured Event: {event}")
        self.events.append(event)

    async def start_recording(self, url: str):
        try:
            logger.info("Initializing Playwright...")
            self.playwright = await async_playwright().start()
            logger.info("Launching browser...")
            self.browser = await self.playwright.chromium.launch(headless=False)

            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

            async def handle_popup(popup):
                logger.info(f"Popup detected: {popup.url}")
                try:
                    if popup.url == "about:blank":
                        await popup.wait_for_event("load", timeout=2000)

                    await popup.expose_function("recordEvent", self.handle_event)
                    await popup.add_init_script(INJECTED_JS)
                    await popup.evaluate(INJECTED_JS)
                    logger.info(f"Recorder injected into popup {popup.url}")
                except Exception as e:
                    logger.error(f"Failed to setup recorder for popup {popup.url}: {e}")

                popup.on("close", lambda p: logger.info(f"Popup closed: {p.url}"))

            self.context.on(
                "page", lambda page: asyncio.create_task(handle_popup(page))
            )

            self.page.on("close", lambda p: self.stop_event.set())

            await self.page.expose_function("recordEvent", self.handle_event)
            await self.page.add_init_script(INJECTED_JS)

            logger.info(f"Navigating to {url}...")
            try:
                await self.page.goto(url, timeout=15000)
            except Exception as e:
                logger.error(f"Navigation failed (proceeding anyway): {e}")

            logger.info(f"Recorder ready on {url}. Waiting for user interaction...")

            await self.stop_event.wait()

            logger.info("Stop event received. Cleaning up...")

        except Exception as e:
            logger.error(f"Critical error during recording session: {e}")
        finally:
            await self.stop_recording()

    async def stop_recording(self):
        logger.info("Stopping recording...")
        self.stop_event.set()

        try:
            if self.browser:
                logger.info("Closing browser...")
                await self.browser.close()
                self.browser = None

            if self.playwright:
                logger.info("Stopping Playwright...")
                await self.playwright.stop()
                self.playwright = None

            logger.info("Recording session ended successfully.")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        return self.events


class Runner:
    def __init__(self):
        self.context = None
        self.pages = []
        self.active_page = None

    async def run_workflow(self, url: str, actions: list):
        logger.info(f"Starting workflow execution on {url} with {len(actions)} actions")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=False)
                self.context = await browser.new_context()
                self.active_page = await self.context.new_page()
                self.pages.append(self.active_page)

                self.context.on("page", self.handle_new_page)

                try:
                    await self.active_page.goto(url, timeout=30000)
                except Exception as e:
                    logger.error(f"Failed to load URL {url}: {e}")
                    await browser.close()
                    return

                await self.execute_steps(actions)

                logger.info("Workflow execution complete.")
                await asyncio.sleep(5)
                await browser.close()
            except Exception as e:
                logger.error(f"Critical error during workflow execution: {e}")

    def handle_new_page(self, page):
        logger.info(f"New popup detected: {page.url}")
        self.pages.append(page)
        page.on("close", lambda: self.handle_page_close(page))

    def handle_page_close(self, page):
        logger.info(f"Page closed: {page.url}")
        if page in self.pages:
            self.pages.remove(page)
        if self.active_page == page:
            self.active_page = self.pages[-1] if self.pages else None
            logger.info("Active page closed, reverting to previous page.")

    async def find_element_on_any_page(self, selector):
        async def search_page(p):
            if p.is_closed():
                return None
            try:
                element = await p.query_selector(selector)
                if element and await element.is_visible():
                    return element

                for frame in p.frames:
                    try:
                        element = await frame.query_selector(selector)
                        if element and await element.is_visible():
                            return element
                    except:
                        pass
            except:
                pass
            return None

        if self.active_page:
            element = await search_page(self.active_page)
            if element:
                return self.active_page, element

        for page in reversed(self.pages):
            if page == self.active_page:
                continue

            element = await search_page(page)
            if element:
                logger.info(
                    f"Element {selector} found on another page ({page.url}). Switching context."
                )
                return page, element

        return None, None

    async def execute_steps(self, steps):
        for i, step in enumerate(steps):
            try:
                step_type = step.get("type")
                selector = step.get("selector")

                if step_type == "loop":
                    loop_selector = step.get("loop_selector")
                    loop_count = step.get("count")
                    inner_steps = step.get("inner_steps", [])

                    if loop_count is not None:
                        logger.info(f"Looping {loop_count} times...")
                        for j in range(int(loop_count)):
                            await self.execute_steps(inner_steps)
                    elif loop_selector:
                        if self.active_page:
                            elements = await self.active_page.query_selector_all(
                                loop_selector
                            )
                            for j in range(len(elements)):
                                current_elements = (
                                    await self.active_page.query_selector_all(
                                        loop_selector
                                    )
                                )
                                if j < len(current_elements):
                                    await self.execute_steps(inner_steps)
                    continue

                if not selector:
                    continue

                found_page = None
                found_element = None

                for attempt in range(30):
                    found_page, found_element = await self.find_element_on_any_page(
                        selector
                    )
                    if found_page:
                        if self.active_page != found_page:
                            logger.info(
                                f"Context switch: {self.active_page.url if self.active_page else 'None'} -> {found_page.url}"
                            )
                        self.active_page = found_page
                        break

                    if attempt % 5 == 0:
                        urls = [p.url for p in self.pages if not p.is_closed()]
                        logger.info(
                            f"Searching for {selector}... Attempt {attempt + 1}/30. Open pages: {urls}"
                        )

                    await asyncio.sleep(0.5)

                if not found_element:
                    logger.error(
                        f"Failed to find element {selector} on any open page after 15s."
                    )
                    continue

                if step_type == "click":
                    logger.info(f"Executing Click: {selector}")
                    await found_element.click()

                elif step_type == "input":
                    value = step.get("value", "")
                    logger.info(f"Executing Input: {selector} -> {value}")
                    await found_element.fill(value)

                elif step_type == "change":
                    value = step.get("value", "")
                    logger.info(f"Executing Change: {selector} -> {value}")
                    await self.active_page.select_option(selector, value)

            except Exception as e:
                logger.error(f"Error executing step {i}: {e}")


if __name__ == "__main__":
    recorder = Recorder()
    asyncio.run(recorder.start_recording("https://example.com"))
