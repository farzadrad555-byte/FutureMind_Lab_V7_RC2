
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:

        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        page = await browser.new_page()

        await page.goto(
            "data:text/html,"
            "<html><body>"
            "<h1>FutureMind Browser Harness OK</h1>"
            "</body></html>"
        )

        text = await page.locator("h1").inner_text()

        print("BROWSER:", "PASS")
        print("DOM    :", text)

        await browser.close()

asyncio.run(main())
