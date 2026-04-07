"""
PDF Generator — Playwright headless Chromium.

Render HTML template → PDF bytes.
Async vì Playwright chạy async.
"""

import logging

logger = logging.getLogger(__name__)


async def generate_debate_pdf(session_data: dict) -> bytes:
    """
    Tạo PDF từ debate session.

    Args:
        session_data: {idea, industry, messages, report_card, created_at}

    Returns:
        bytes: PDF file content

    Raises:
        RuntimeError: nếu Playwright/Chromium không khả dụng
    """
    from backend.app.services.pdf_template import render_pdf_template

    # 1. Render HTML
    html_content = render_pdf_template(session_data)
    logger.info(f"[PDF] HTML template rendered — {len(html_content)} chars")

    # 2. Playwright → PDF
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.set_content(html_content, wait_until="networkidle")

                pdf_bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "20mm",
                        "bottom": "20mm",
                        "left": "15mm",
                        "right": "15mm",
                    },
                )
            finally:
                await browser.close()  # Always close — kể cả khi exception

        logger.info(f"[PDF] Generated — {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"[PDF] Generation failed: {e}")
        raise RuntimeError(f"PDF generation failed: {e}")
