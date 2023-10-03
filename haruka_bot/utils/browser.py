import asyncio
import os
import re
import sys
import json
import time
import platform
from pathlib import Path
from typing import Optional

from nonebot.log import logger
from playwright.__main__ import main

try:
    from playwright.async_api import Browser, async_playwright
    from playwright._impl._api_structures import FloatRect
except ImportError:
    raise ImportError(
        "加载失败，请先安装 Visual C++ Redistributable: "
        "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    )

from .. import config
from .fonts_provider import fill_font

_browser: Optional[Browser] = None
mobile_js = Path(__file__).parent.joinpath("mobile.js")


async def init_browser(**kwargs) -> Browser:
    global _browser
    p = await async_playwright().start()
    if platform.system()=='Windows':
        _browser = await p.chromium.launch(proxy={"server":"per-context"}, **kwargs)
    else:
        _browser = await p.chromium.launch(**kwargs)
    return _browser


async def get_browser() -> Browser:
    global _browser
    if _browser is None or not _browser.is_connected():
        _browser = await init_browser()
    return _browser


async def get_dynamic_screenshot(dynamic_id, style=config.haruka_screenshot_style):
    """获取动态截图"""
    if style.lower() == "mobile":
        return await get_dynamic_screenshot_mobile(dynamic_id)
    else:
        return await get_dynamic_screenshot_pc(dynamic_id)


async def get_dynamic_screenshot_mobile(dynamic_id):
    """移动端动态截图"""
    from ..bili_auth import bili_auth

    url = f"https://m.bilibili.com/dynamic/{dynamic_id}"

    if config.haruka_browser_ua:
        user_agent = config.haruka_browser_ua
    else:
        user_agent = ("Mozilla/5.0 (Linux; Android 11; RMX3161 Build/RKQ1.201217.003; wv) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Version/4.0 Chrome/101.0.4896.59 Mobile Safari/537.36")

    browser:Browser = await get_browser()
    context = await browser.new_context(
        proxy={"server":config.haruka_proxy} if config.haruka_proxy else None,
        device_scale_factor=2,
        user_agent=user_agent,
        viewport={"width": 460, "height": 780},
    )
    page = await context.new_page()

    cookies= bili_auth.get_list_auth_cookies()
    if len(cookies) > 0:
        await page.context.add_cookies(cookies)
    else:
        logger.error("未登录，截图时未填充cookie")

    # cookies = config.get_dynamic_cookies()
    # if len(cookies) > 0:
    #     logger.debug(f"填充cookie到PlayWright:{cookies}")
    #     await page.context.add_cookies(cookies)
    # else:
    #     logger.error("截图时未填充cookie")

    try:
        await page.route(re.compile("^https://static.graiax/fonts/(.+)$"), fill_font)
        await page.goto(
            url,
            wait_until="networkidle",
            timeout=config.haruka_dynamic_timeout * 1000,
        )
        # 动态被删除或者进审核了
        if page.url == "https://m.bilibili.com/404":
            return None
        
        # 出现了验证码，等下一次重来
        if await page.query_selector(".geetest_panel"):
            logger.info(f'截图动态时遇到了验证码，等下一次重来: {url}')
            return None
        # await page.add_script_tag(
        #     content=
        #     # 去除打开app按钮
        #     "document.getElementsByClassName('m-dynamic-float-openapp').forEach(v=>v.remove());"
        #     # 去除关注按钮
        #     "document.getElementsByClassName('dyn-header__following').forEach(v=>v.remove());"
        #     # 修复字体与换行问题
        #     "const dyn=document.getElementsByClassName('dyn-card')[0];"
        #     "dyn.style.fontFamily='Noto Sans CJK SC, sans-serif';"
        #     "dyn.style.overflowWrap='break-word'"
        # )
        await page.add_script_tag(path=mobile_js)

        await page.evaluate(
            f'setFont("{config.haruka_dynamic_font}", '
            f'"{config.haruka_dynamic_font_source}")'
            if config.haruka_dynamic_font
            else "setFont()"
        )
        await page.wait_for_function("getMobileStyle()")

        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")

        await page.wait_for_timeout(
            200 if config.haruka_dynamic_font_source == "remote" else 50
        )

        # 判断字体是否加载完成
        need_wait = ["imageComplete", "fontsLoaded"]
        await asyncio.gather(*[page.wait_for_function(f"{i}()") for i in need_wait])

        card = await page.query_selector(
            ".opus-modules" if "opus" in page.url else ".dyn-card"
        )
        assert card
        clip = await card.bounding_box()
        assert clip

        # 将成功截图时的新cookie写入文件
        storage_state = await page.context.storage_state()
        new_cookies = storage_state["cookies"]
        bili_auth.save_cookies_to_file(new_cookies)

        return await page.screenshot(clip=clip, full_page=True)
    except Exception:
        logger.exception(f"截取动态时发生错误：{url}")
        return await page.screenshot(full_page=True)
    finally:
        await page.close()
        await context.close()


async def get_dynamic_screenshot_pc(dynamic_id):
    """电脑端动态截图"""
    url = f"https://t.bilibili.com/{dynamic_id}"
    browser = await get_browser()
    context = await browser.new_context(
        proxy={"server":config.haruka_proxy} if config.haruka_proxy else None,
        viewport={"width": 2560, "height": 1080},
        device_scale_factor=2,
    )
    await context.add_cookies(
        [
            {
                "name": "hit-dyn-v2",
                "value": "1",
                "domain": ".bilibili.com",
                "path": "/",
            }
        ]
    )
    page = await context.new_page()
    try:
        await page.goto(
            url, wait_until="networkidle", timeout=config.haruka_dynamic_timeout * 1000
        )
        # 动态被删除或者进审核了
        if page.url == "https://www.bilibili.com/404":
            return None
        card = await page.query_selector(".card")
        assert card
        clip = await card.bounding_box()
        assert clip
        bar = await page.query_selector(".bili-dyn-action__icon")
        assert bar
        bar_bound = await bar.bounding_box()
        assert bar_bound
        clip["height"] = bar_bound["y"] - clip["y"]
        return await page.screenshot(clip=clip, full_page=True)
    except Exception:
        logger.exception(f"截取动态时发生错误：{url}")
        return await page.screenshot(full_page=True)
    finally:
        await page.close()
        await context.close()


def install():
    """自动安装、更新 Chromium"""

    def restore_env():
        del os.environ["PLAYWRIGHT_DOWNLOAD_HOST"]
        if config.haruka_proxy:
            del os.environ["HTTPS_PROXY"]
        if original_proxy is not None:
            os.environ["HTTPS_PROXY"] = original_proxy

    logger.info("检查 Chromium 更新")
    sys.argv = ["", "install", "chromium"]
    original_proxy = os.environ.get("HTTPS_PROXY")
    if config.haruka_proxy:
        os.environ["HTTPS_PROXY"] = config.haruka_proxy
    os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = "https://npmmirror.com/mirrors/playwright/"
    success = False
    try:
        main()
    except SystemExit as e:
        if e.code == 0:
            success = True
    if not success:
        logger.info("Chromium 更新失败，尝试从原始仓库下载，速度较慢")
        os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = ""
        try:
            main()
        except SystemExit as e:
            if e.code != 0:
                restore_env()
                raise RuntimeError("未知错误，Chromium 下载失败")
    restore_env()


async def check_playwright_env():
    """检查 Playwright 依赖"""
    logger.info("检查 Playwright 依赖")
    try:
        async with async_playwright() as p:
            await p.chromium.launch()
    except Exception:
        raise ImportError(
            "加载失败，Playwright 依赖不全，"
            "解决方法：https://haruka-bot.sk415.icu/faq.html#playwright-依赖不全"
        )

async def get_github_screenshot(url: str):
    """github issue, pr截图"""

    assert('/issues/' in url or '/pull/' in url)

    if config.haruka_browser_ua:
        user_agent = config.haruka_browser_ua
    else:
        user_agent = ("Mozilla/5.0 (Linux; Android 11; RMX3161 Build/RKQ1.201217.003; wv) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Version/4.0 Chrome/101.0.4896.59 Mobile Safari/537.36")

    browser:Browser = await get_browser()
    context = await browser.new_context(
        proxy={"server": config.overseas_proxy} if config.overseas_proxy else None,
        device_scale_factor=2,
        user_agent=user_agent,
        viewport={"width": 980, "height": 780},
        )
    page = await context.new_page()

    try:
        dt1 = time.time()
        await page.goto(
                url,
                wait_until="networkidle",
                timeout=config.haruka_dynamic_timeout * 1000,
            )
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")

        dt2 = time.time()
        # print(f"visit github: {dt2 - dt1}")

        show_issue = await page.query_selector("#show_issue") or await page.query_selector(".js-issues-results") # 总框
        layout_main = await page.query_selector(".Layout-main") # 提取宽度
        discussion_timeline_actions = await page.query_selector(".discussion-timeline-actions") # 底部评论区
        pull_discussion_timeline = await page.query_selector(".pull-discussion-timeline") # 包含pull内容和评论区的block

        clip_show_issue = await show_issue.bounding_box() if show_issue else None
        clip_layout_main = await layout_main.bounding_box() if layout_main else None
        clip_discussion_timeline_actions = await discussion_timeline_actions.bounding_box() if discussion_timeline_actions else None
        clip_pull_discussion_timeline = await pull_discussion_timeline.bounding_box() if pull_discussion_timeline else None

        assert(clip_show_issue)
        assert(clip_layout_main)
        assert(clip_discussion_timeline_actions)
        margin = 17
        spacing_bottom = clip_layout_main['height'] - clip_pull_discussion_timeline["height"] if clip_pull_discussion_timeline else 0
        clip = FloatRect(
                x=clip_show_issue['x'] - margin,
                y= clip_show_issue['y'] - margin,
                width= clip_layout_main['width'] + margin * 2 - 1,
                height= clip_show_issue['height'] - clip_discussion_timeline_actions['height'] - spacing_bottom + margin * 2
        )

        screenshot = await page.screenshot(clip=clip, full_page=True)
        dt3 = time.time()
        # print(f"screenshot:{dt3 - dt2}")
        return screenshot

    except Exception as e:
        logger.exception(f"截取github网页时发生错误：{url}")
        return await page.screenshot(full_page=True)
    finally:
        await page.close()
        await context.close()

