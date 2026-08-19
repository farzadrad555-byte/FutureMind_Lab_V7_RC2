
import asyncio
import sys
from pathlib import Path

ROOT = Path(
    "/content/drive/MyDrive/"
    "FutureMind_Lab_V7_RC2_LANGUAGE_FULL_FIX_WORKING_20260807"
)

URL = "http://127.0.0.1:8002/"


async def main():

    print("=" * 70)
    print("FUTUREMIND BROWSER RUNTIME")
    print("=" * 70)

    from playwright.async_api import async_playwright

    async with async_playwright() as pw:

        print("[1] Launch Chromium")

        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )

        print("    Chromium -> PASS")

        page = await browser.new_page()

        console_errors = []
        page_errors = []
        request_failures = []

        page.on(
            "console",
            lambda msg:
                console_errors.append(msg.text)
                if msg.type == "error"
                else None
        )

        page.on(
            "pageerror",
            lambda exc:
                page_errors.append(str(exc))
        )

        page.on(
            "requestfailed",
            lambda req:
                request_failures.append(
                    f"{req.method} {req.url} :: {req.failure}"
                )
        )

        print("[2] Open FutureMind")
        print("    URL:", URL)

        try:
            response = await page.goto(
                URL,
                wait_until="networkidle",
                timeout=30000
            )

            status = response.status if response else None

            print(
                "    HTTP STATUS ->",
                status
            )

        except Exception as exc:
            print("    PAGE LOAD -> FAIL")
            print("    ", repr(exc))

            await browser.close()
            return 1

        print("[3] DOM")

        title = await page.title()

        print("    TITLE:", title)

        print("[4] RUNTIME ERRORS")

        print(
            "    Console errors :",
            len(console_errors)
        )

        print(
            "    Page errors    :",
            len(page_errors)
        )

        print(
            "    Request fails  :",
            len(request_failures)
        )

        if console_errors:
            print("\n    CONSOLE ERRORS:")
            for x in console_errors[:20]:
                print("    ", x)

        if page_errors:
            print("\n    PAGE ERRORS:")
            for x in page_errors[:20]:
                print("    ", x)

        if request_failures:
            print("\n    REQUEST FAILURES:")
            for x in request_failures[:20]:
                print("    ", x)

        print("\n[5] FutureMind DOM markers")

        markers = {
            "data-i18n": await page.locator(
                "[data-i18n]"
            ).count(),

            "data-lang": await page.locator(
                "[data-lang]"
            ).count(),

            "i18n placeholders": await page.locator(
                "[data-i18n-placeholder]"
            ).count(),

            "lang placeholders": await page.locator(
                "[data-lang-placeholder]"
            ).count(),
        }

        for key, value in markers.items():
            print(
                f"    {key:24} -> {value}"
            )

        print("\n[6] Language Runtime")

        runtime = await page.evaluate("""
        () => ({
            language:
                window.futureMindLanguage?.lang ??
                window.currentLanguage ??
                localStorage.getItem("language") ??
                localStorage.getItem("lang") ??
                null,

            engine:
                !!window.futureMindLanguage,

            body:
                document.body?.innerText?.length ?? 0
        })
        """)

        for key, value in runtime.items():
            print(
                f"    {key:24} -> {value}"
            )

        await browser.close()

    print("\n" + "=" * 70)
    print("BROWSER RUNTIME COMPLETE")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
