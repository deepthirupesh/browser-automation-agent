"""Script Generator Agent — hybrid local storage with incremental generation."""

from __future__ import annotations

import logging
from typing import Any

from config import get_settings
from state.schema import AgentState
from storage.script_store import ScriptStore, compute_flow_hash
from test_data import credentials_file_path, get_login_credentials

logger = logging.getLogger(__name__)

_LOGIN_LINES = """
import json
from pathlib import Path

creds_path = Path("{creds_path}")
creds = {default_creds}
if creds_path.exists():
    creds = json.loads(creds_path.read_text(encoding="utf-8")).get("login", creds)

username = page.locator(
    'input[name="username"], input[type="email"], input[name="email"]'
).first
password = page.locator(
    'input[name="password"], input[type="password"]'
).first
submit = page.get_by_role("button", name="Login").or_(
    page.locator('button[type="submit"]')
).first

if await username.count() > 0:
    await username.fill(creds["username"])
if await password.count() > 0:
    await password.fill(creds["password"])
if await submit.count() > 0:
    await submit.click(timeout=10000)

await page.wait_for_url(
    lambda current_url: "auth/login" not in current_url.lower()
    or "dashboard" in current_url.lower(),
    timeout=30000,
)
await page.wait_for_load_state("networkidle", timeout=30000)

login_form = page.locator(
    'input[name="username"], input[type="email"], input[name="email"]'
).first
if await login_form.count() > 0 and await login_form.is_visible():
    raise RuntimeError("Login failed: login form still visible after submit")

home_screen = page.get_by_role("heading", name="Dashboard").or_(
    page.locator(".oxd-topbar-header-breadcrumb-module")
).or_(page.locator(".oxd-userdropdown-tab, nav, [role='navigation']"))
await home_screen.first.wait_for(state="visible", timeout=30000)

result["home_page_verified"] = True
os.makedirs(screenshot_dir, exist_ok=True)
screenshot_path = os.path.join(screenshot_dir, "{screenshot_name}.png")
await page.screenshot(path=screenshot_path, full_page=True)
result["screenshots"].append(screenshot_path)
"""


def _indent_block(block: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line.strip() else line for line in block.strip().splitlines())


def _is_login_flow(flow: str) -> bool:
    return flow == "login" or "login" in flow.lower()


def build_script(flow: str, url: str) -> str:
    """Build a Playwright script string for a single flow."""
    safe_flow = flow.replace('"', '\\"')
    creds = get_login_credentials()
    default_creds = '{"username": "' + creds["username"] + '", "password": "' + creds["password"] + '"}'
    creds_path = str(credentials_file_path()).replace("\\", "\\\\")
    is_login = _is_login_flow(flow)

    login_body = _indent_block(
        _LOGIN_LINES.format(
            creds_path=creds_path,
            default_creds=default_creds,
            screenshot_name=flow,
        ),
        8,
    )

    checkout_block = _indent_block(
        '''
elif "{flow}" == "checkout":
    checkout = page.get_by_role("button", name="Checkout").or_(
        page.get_by_test_id("checkout-cta")
    ).or_(page.locator("#checkout-btn"))
    if await checkout.count() > 0:
        await checkout.click(timeout=5000)
        '''.format(flow=flow),
        8,
    )

    flow_actions = login_body if is_login else checkout_block if flow == "checkout" else ""

    pre_action_screenshot = ""
    if not is_login:
        pre_action_screenshot = _indent_block(
            f'''
os.makedirs(screenshot_dir, exist_ok=True)
screenshot_path = os.path.join(screenshot_dir, "{flow}.png")
await page.screenshot(path=screenshot_path, full_page=True)
result["screenshots"].append(screenshot_path)
            ''',
            8,
        )

    return f'''async def run(page, url: str, screenshot_dir: str) -> dict:
    """Automate flow: {safe_flow}"""
    import os

    result = {{"status": "success", "screenshots": [], "flow": "{safe_flow}"}}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
{pre_action_screenshot}{flow_actions}
    except Exception as exc:
        result = {{
            "status": "fail",
            "error": type(exc).__name__ + ": " + str(exc),
            "flow": "{safe_flow}",
            "screenshots": result.get("screenshots", []),
        }}
    return result
'''


def _is_valid_cached_script(flow: str, script: str) -> bool:
    if _is_login_flow(flow):
        return "home_page_verified" in script
    return True


def _resolve_scripts_for_flows(
    url: str,
    intent: str,
    flows: list[str],
    *,
    force_flows: set[str] | None = None,
) -> tuple[list[str], dict[str, str], list[str], list[str], list[str]]:
    store = ScriptStore(url)
    store.archive_removed_flows(flows)

    scripts: list[str] = []
    script_sources: dict[str, str] = {}
    flows_reused: list[str] = []
    flows_generated: list[str] = []
    flows_regenerated: list[str] = []
    force = force_flows or set()

    for flow in flows:
        flow_hash = compute_flow_hash(url, intent, flow)
        must_regenerate = flow in force

        if not must_regenerate and store.should_reuse(flow, flow_hash):
            script = store.read_script(flow)
            if script and not _is_valid_cached_script(flow, script):
                script = None
            if script:
                scripts.append(script)
                script_sources[flow] = "cached"
                flows_reused.append(flow)
                logger.info("Reusing cached script for flow=%s", flow)
                continue

        script = build_script(flow, url)
        scripts.append(script)
        source = "regenerated" if must_regenerate else "generated"
        if source == "regenerated":
            flows_regenerated.append(flow)
        else:
            flows_generated.append(flow)
        script_sources[flow] = source
        store.save_script(
            flow,
            script,
            flow_hash=flow_hash,
            intent=intent,
            source=source,
            repair_count=0,
            last_status="pending",
        )
        logger.info("%s script for flow=%s", source.capitalize(), flow)

    return scripts, script_sources, flows_reused, flows_generated, flows_regenerated


def generate_scripts(state: AgentState) -> dict[str, Any]:
    """Resolve scripts using hybrid strategy: reuse cached, generate only new/changed flows."""
    flows = state.get("discovered_flows", [])
    url = state["url"]
    intent = state["intent"]
    logger.info("Resolving scripts for %d flows (hybrid/local storage)", len(flows))

    scripts, script_sources, flows_reused, flows_generated, flows_regenerated = _resolve_scripts_for_flows(
        url, intent, flows
    )

    return {
        "generated_scripts": scripts,
        "script_sources": script_sources,
        "flows_reused": flows_reused,
        "flows_generated": flows_generated,
        "flows_regenerated": flows_regenerated,
        "flow_repair_counts": state.get("flow_repair_counts", {}),
        "status": "scripts_generated",
        "current_script_index": 0,
    }


def regenerate_current_flow(state: AgentState) -> dict[str, Any]:
    """Regenerate script from scratch after repeated repair failures."""
    url = state["url"]
    intent = state["intent"]
    flows = state.get("discovered_flows", [])
    index = state.get("current_script_index", 0)
    scripts = list(state.get("generated_scripts", []))

    if not flows or index >= len(flows):
        return {"status": "execution_failed"}

    flow = flows[index]
    logger.info("Regenerating script from scratch for flow=%s after repair exhaustion", flow)

    new_script = build_script(flow, url)
    flow_hash = compute_flow_hash(url, intent, flow)
    store = ScriptStore(url)
    store.save_script(
        flow,
        new_script,
        flow_hash=flow_hash,
        intent=intent,
        source="regenerated",
        repair_count=0,
        last_status="pending",
    )

    if index < len(scripts):
        scripts[index] = new_script
    else:
        scripts.append(new_script)

    script_sources = dict(state.get("script_sources", {}))
    script_sources[flow] = "regenerated"

    flows_regenerated = list(state.get("flows_regenerated", []))
    if flow not in flows_regenerated:
        flows_regenerated.append(flow)

    flow_repair_counts = dict(state.get("flow_repair_counts", {}))
    flow_repair_counts[flow] = 0

    return {
        "generated_scripts": scripts,
        "repaired_script": new_script,
        "script_sources": script_sources,
        "flows_regenerated": flows_regenerated,
        "flow_repair_counts": flow_repair_counts,
        "status": "regenerated",
    }


def persist_script_for_flow(state: AgentState, flow: str, script: str, source: str) -> None:
    """Save a script to local storage after successful execution or repair."""
    if _is_login_flow(flow) and "home_page_verified" not in script:
        logger.warning("Skipping persist for flow=%s: script missing home page verification", flow)
        return

    url = state["url"]
    intent = state["intent"]
    flow_hash = compute_flow_hash(url, intent, flow)
    store = ScriptStore(url)
    entry = store.get_flow_entry(flow) or {}
    store.save_script(
        flow,
        script,
        flow_hash=flow_hash,
        intent=intent,
        source=source,
        repair_count=entry.get("repair_count", 0),
        last_status="success",
    )
