from DrissionPage import ChromiumPage, ChromiumOptions
import time


def main():
    co = ChromiumOptions()

    try:
        print("Initializing DrissionPage...")
        page = ChromiumPage(co)
    except Exception as e:
        print(f"Failed to find browser automatically: {e}")
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser_path = p.chromium.executable_path
                print(f"Found Playwright Chromium at: {browser_path}")
                co.set_browser_path(browser_path)
                page = ChromiumPage(co)
        except Exception as e2:
            print(f"Could not setup browser: {e2}")
            return

    try:
        print("Navigating to https://www.europeanurology.com/ ...")
        page.get("https://www.europeanurology.com/")

        print("Checking for Cloudflare...")
        if page.ele("@id=challenge-stage", timeout=2):
            print("Cloudflare challenge detected. Attempting to solve...")
            time.sleep(2)
            try:
                iframe = page.get_frame("@src^https://challenges.cloudflare.com")
                if iframe:
                    print("Found Cloudflare iframe")
                    cb = iframe.ele(
                        'css:input[type="checkbox"]', timeout=2
                    ) or iframe.ele("@class=ctp-checkbox-label", timeout=2)
                    if cb:
                        print("Clicking checkbox...")
                        cb.click()
                    else:
                        print("Checkbox not found in iframe")
                else:
                    print("Cloudflare iframe not found")
            except Exception as e:
                print(f"Error handling iframe: {e}")

            time.sleep(5)

        title = page.title
        print(f"Current Page Title: {title}")

        if "European Urology" in title or "Elsevier" in title:
            print("SUCCESS: Successfully bypassed Cloudflare!")
        elif "Just a moment" in title:
            print("FAILURE: Still stuck on Cloudflare challenge.")
        else:
            print("UNKNOWN: Loaded a page, but title is unexpected.")

    except Exception as e:
        print(f"An error occurred during navigation: {e}")

    finally:
        print("Closing browser...")
        page.quit()


if __name__ == "__main__":
    main()
