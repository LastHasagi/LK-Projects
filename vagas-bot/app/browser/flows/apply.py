from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import BrowserContext, Page

from app.core.logging import get_logger

log = get_logger(__name__)

DISMISS_TEXT_FRAGMENTS = [
    "OBRIGADO",
    "Obrigado",
    "obrigado",
    "Rejeitar Todos",
    "Rejeitar todos",
    "Rejeitar",
    "Recusar",
    "Fechar",
]
APPLY_BUTTON_SELECTORS = [
    "button:has-text('Candidatar-se')",
    "button:has-text('Candidatar')",
    "a:has-text('Candidatar-se')",
]
STAGE_START_TEXT_FRAGMENTS = [
    "Começar",
    "Iniciar etapa",
    "Iniciar",
    "Retomar",
    "Continuar etapa",
]
ADVANCE_TEXT_FRAGMENTS = [
    "Salvar e continuar",
    "Responder agora",
    "Próximo",
    "Próxima",
    "Avançar",
    "Seguir",
    "Continuar",
]
SUBMIT_TEXT_FRAGMENTS = [
    "Finalizar candidatura",
    "Enviar candidatura",
    "Confirmar candidatura",
    "Enviar respostas",
    "Concluir candidatura",
    "Concluir",
    "Finalizar",
    "Confirmar",
    "Enviar",
]

TEXT_FIELD_SELECTOR = (
    "input[type='text']:not([disabled]):visible, "
    "input[type='number']:not([disabled]):visible, "
    "input[type='email']:not([disabled]):visible, "
    "input[type='tel']:not([disabled]):visible, "
    "textarea:not([disabled]):visible, "
    "select:not([disabled]):visible"
)
RADIO_SELECTOR = "input[type='radio']:not([disabled]):visible"


@dataclass
class AppliedResult:
    screenshot_path: str


@dataclass
class PendingQuestion:
    field_id: str
    pergunta: str
    screenshot_path: str
    prompt_extra: str | None = None


async def _click_button_with_text(page: Page, text: str, timeout: int = 1500) -> bool:
    candidates = [
        page.get_by_role("button", name=text, exact=False),
        page.get_by_role("link", name=text, exact=False),
        page.locator(f"button:has-text('{text}')"),
        page.locator(f"a:has-text('{text}')"),
        page.locator(f"[role='button']:has-text('{text}')"),
        page.locator(f"text='{text}'"),
    ]
    for locator in candidates:
        try:
            count = await locator.count()
            if count == 0:
                continue
            for i in range(min(count, 3)):
                target = locator.nth(i)
                try:
                    if not await target.is_visible():
                        continue
                except Exception:
                    continue
                for click_kwargs in ({}, {"force": True}):
                    try:
                        await target.click(timeout=timeout, **click_kwargs)
                        log.info("clicked", text=text, strategy=str(locator))
                        return True
                    except Exception:
                        continue
                try:
                    await target.evaluate("el => el.click()")
                    log.info("clicked_js", text=text)
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


async def _click_any(page: Page, texts: list[str], timeout: int = 1500) -> str | None:
    for txt in texts:
        if await _click_button_with_text(page, txt, timeout=timeout):
            return txt
    return None


async def _dismiss_popups(page: Page) -> int:
    dismissed = 0
    for txt in DISMISS_TEXT_FRAGMENTS:
        for selector in (
            f"button:has-text('{txt}')",
            f"a:has-text('{txt}')",
            f"[role='button']:has-text('{txt}')",
        ):
            locator = page.locator(selector)
            count = await locator.count()
            for i in range(count):
                el = locator.nth(i)
                try:
                    if await el.is_visible():
                        await el.click(timeout=1500, force=True)
                        dismissed += 1
                        await page.wait_for_timeout(400)
                except Exception:
                    continue
    return dismissed


async def _click_apply(page: Page, timeout: int = 10_000) -> bool:
    for sel in APPLY_BUTTON_SELECTORS:
        try:
            btn = await page.wait_for_selector(sel, timeout=timeout, state="visible")
            if btn:
                await btn.click()
                return True
        except Exception:
            continue
    return False


async def _field_label(field) -> str:
    label = await field.evaluate("""
        e => {
            if (e.id) {
                const lbl = document.querySelector(`label[for='${e.id}']`);
                if (lbl) {
                    const t = lbl.innerText.trim();
                    if (t) return t;
                }
            }
            const parent = e.closest('label');
            if (parent) {
                const t = parent.innerText.trim();
                if (t) return t;
            }
            const aria = e.getAttribute('aria-label');
            if (aria && aria.trim()) return aria.trim();
            let node = e.parentElement;
            for (let i = 0; i < 6 && node; i++) {
                const prev = node.previousElementSibling;
                if (prev) {
                    const t = (prev.innerText || '').trim();
                    if (t && t.length > 3 && t.length < 300) return t;
                }
                node = node.parentElement;
            }
            const ph = e.getAttribute('placeholder');
            if (ph && ph.trim()) return ph.trim();
            return '';
        }
    """)
    return label or ""


async def _radio_group_question(field) -> str:
    return await field.evaluate("""
        e => {
            const fs = e.closest('fieldset');
            if (fs) {
                const legend = fs.querySelector('legend');
                if (legend && legend.innerText.trim()) return legend.innerText.trim();
            }
            let node = e.parentElement;
            for (let i = 0; i < 6 && node; i++) {
                const prev = node.previousElementSibling;
                if (prev) {
                    const t = (prev.innerText || '').trim();
                    if (t && t.length > 3 && t.length < 400) return t;
                }
                const labelInside = node.querySelector(':scope > p, :scope > span, :scope > div > p');
                if (labelInside) {
                    const t = labelInside.innerText.trim();
                    if (t && t.length > 3 && t.length < 400) return t;
                }
                node = node.parentElement;
            }
            return '';
        }
    """)


async def _fill_field(field, value: str) -> None:
    tag = await field.evaluate("e => e.tagName.toLowerCase()")
    if tag == "select":
        try:
            await field.select_option(label=value)
        except Exception:
            await field.select_option(value=value)
    else:
        await field.fill(value)


async def _radio_group_options(page: Page, name: str) -> list[str]:
    raw = await page.evaluate(
        """
        (name) => {
            const out = [];
            document.querySelectorAll(`input[type='radio'][name='${name}']:not([disabled])`).forEach(e => {
                let label = '';
                if (e.id) {
                    const lbl = document.querySelector(`label[for='${e.id}']`);
                    if (lbl) label = lbl.innerText.trim();
                }
                if (!label) {
                    const parent = e.closest('label');
                    if (parent) label = parent.innerText.trim();
                }
                if (!label) label = (e.value || '').trim();
                if (label) out.push(label);
            });
            return out;
        }
        """,
        name,
    )
    return [str(x) for x in (raw or []) if str(x).strip()]


async def _find_required_empty_text(page: Page) -> list[dict]:
    return await page.evaluate(
        """
        () => {
            const out = [];
            const SEL = 'input:not([disabled]):not([type="radio"]):not([type="checkbox"]):not([type="file"]):not([type="hidden"]), textarea:not([disabled]), select:not([disabled])';
            document.querySelectorAll(SEL).forEach(e => {
                if (e.offsetParent === null) return;
                const val = (e.value || '').toString().trim();
                if (val) return;
                const required = e.required || e.getAttribute('aria-required') === 'true';
                let hasErr = false;
                let n = e.parentElement;
                for (let i = 0; i < 4 && n; i++) {
                    const txt = (n.innerText || '').toLowerCase();
                    if (txt.includes('campo obrigat') || txt.includes('obrigatório') || txt.includes('required')) {
                        hasErr = true; break;
                    }
                    n = n.parentElement;
                }
                if (!required && !hasErr) return;
                let label = '';
                if (e.id) {
                    const lbl = document.querySelector(`label[for='${e.id}']`);
                    if (lbl) label = lbl.innerText.trim();
                }
                if (!label) {
                    let node = e.parentElement;
                    for (let i = 0; i < 6 && node; i++) {
                        const prev = node.previousElementSibling;
                        if (prev) {
                            const t = (prev.innerText || '').trim();
                            if (t && t.length > 3 && t.length < 300) { label = t; break; }
                        }
                        node = node.parentElement;
                    }
                }
                out.push({ name: e.name || e.id || '', label: label });
            });
            return out;
        }
        """
    )


async def _handle_radio_group(page: Page, name: str, answer: str) -> bool:
    target = answer.strip().lower()
    radios = await page.query_selector_all(
        f"input[type='radio'][name='{name}']:not([disabled])"
    )
    if not radios:
        return False
    for r in radios:
        opt_label = await r.evaluate("""
            e => {
                if (e.id) {
                    const lbl = document.querySelector(`label[for='${e.id}']`);
                    if (lbl) return lbl.innerText.trim().toLowerCase();
                }
                const parent = e.closest('label');
                if (parent) return parent.innerText.trim().toLowerCase();
                const val = e.value || '';
                return val.toLowerCase();
            }
        """)
        if opt_label and (opt_label == target or target in opt_label or opt_label in target):
            await r.check()
            return True
    return False


async def _screenshot(page: Page, *, dest_dir: Path, prefix: str) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{prefix}.png"
    await page.screenshot(path=str(path), full_page=True)
    return str(path)


async def _form_signature(page: Page) -> str:
    return await page.evaluate("""
        () => {
            const ids = [];
            document.querySelectorAll(
                "input:not([disabled]), textarea:not([disabled]), select:not([disabled])"
            ).forEach(e => ids.push(`${e.tagName}:${e.type || ''}:${e.name || e.id || ''}`));
            const url = window.location.href;
            const heading = (
                document.querySelector('h1, h2, h3, [role="heading"]')
                    ?.innerText || ''
            ).trim().slice(0, 200);
            const progress = (
                document.querySelector(
                    '[role="progressbar"], [aria-valuenow], .progress'
                )?.getAttribute('aria-valuenow') || ''
            );
            return `${url}|${heading}|${progress}|${ids.sort().join('|')}`;
        }
    """)


async def apply_to_vaga(
    context: BrowserContext,
    *,
    url: str,
    answer_lookup,
    screenshot_dir: Path,
    candidatura_id: int,
) -> AppliedResult | PendingQuestion:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        await page.wait_for_timeout(2000)
        await _dismiss_popups(page)

        if not await _click_apply(page, timeout=10_000):
            stage_clicked = await _click_any(
                page, STAGE_START_TEXT_FRAGMENTS, timeout=3000
            )
            if stage_clicked:
                log.info(
                    "apply_stage_start_fallback",
                    candidatura_id=candidatura_id, text=stage_clicked,
                )
                await page.wait_for_timeout(3000)
            else:
                shot = await _screenshot(
                    page, dest_dir=screenshot_dir,
                    prefix=f"{candidatura_id}_no_apply_btn",
                )
                raise RuntimeError(
                    f"botao Candidatar-se nao encontrado (screenshot {shot})"
                )
        else:
            await page.wait_for_timeout(3000)

        prev_signature: str | None = None
        repeat_count = 0
        blank_count = 0
        max_steps = 18
        for step in range(max_steps):
            await page.wait_for_timeout(1500)
            await _dismiss_popups(page)

            text_fields = await page.query_selector_all(TEXT_FIELD_SELECTOR)
            radios = await page.query_selector_all(RADIO_SELECTOR)
            log.info(
                "apply_step", candidatura_id=candidatura_id,
                step=step, text_fields=len(text_fields), radios=len(radios),
            )

            for field in text_fields:
                value_already = await field.evaluate("e => e.value || ''")
                if value_already.strip():
                    continue
                label = await _field_label(field)
                if not label:
                    continue
                resposta = await answer_lookup(label)
                if resposta is None:
                    shot = await _screenshot(
                        page, dest_dir=screenshot_dir,
                        prefix=f"{candidatura_id}_pending_{step}",
                    )
                    field_id = await field.evaluate("e => e.id || e.name || ''") or label[:80]
                    return PendingQuestion(
                        field_id=field_id, pergunta=label, screenshot_path=shot
                    )
                try:
                    await _fill_field(field, resposta)
                except Exception as e:
                    log.warning("fill_failed", label=label, error=str(e))

            handled_names: set[str] = set()
            for radio in radios:
                name = await radio.evaluate("e => e.name || ''")
                if not name or name in handled_names:
                    continue
                group_checked = await page.evaluate(
                    f"() => !!document.querySelector(\"input[type='radio'][name='{name}']:checked\")"
                )
                if group_checked:
                    handled_names.add(name)
                    continue
                pergunta = await _radio_group_question(radio)
                if not pergunta:
                    continue
                resposta = await answer_lookup(pergunta)
                if resposta is None:
                    shot = await _screenshot(
                        page, dest_dir=screenshot_dir,
                        prefix=f"{candidatura_id}_pending_radio_{step}",
                    )
                    return PendingQuestion(
                        field_id=name, pergunta=pergunta, screenshot_path=shot
                    )
                ok = await _handle_radio_group(page, name, resposta)
                if ok:
                    handled_names.add(name)
                else:
                    log.warning(
                        "radio_option_not_matched",
                        pergunta=pergunta, resposta=resposta, name=name,
                    )
                    options = await _radio_group_options(page, name)
                    options_str = (
                        " Opções: " + " | ".join(options) if options else ""
                    )
                    extra = (
                        f"(resposta sugerida '{resposta}' não bateu com nenhuma "
                        f"opção).{options_str}"
                    )
                    shot = await _screenshot(
                        page, dest_dir=screenshot_dir,
                        prefix=f"{candidatura_id}_pending_radio_mismatch_{step}",
                    )
                    return PendingQuestion(
                        field_id=name,
                        pergunta=pergunta,
                        screenshot_path=shot,
                        prompt_extra=extra,
                    )

            clicked = await _click_any(page, SUBMIT_TEXT_FRAGMENTS, timeout=1500)
            if clicked:
                await page.wait_for_timeout(4000)
                shot = await _screenshot(
                    page, dest_dir=screenshot_dir, prefix=f"{candidatura_id}_applied"
                )
                return AppliedResult(screenshot_path=shot)

            clicked = await _click_any(page, ADVANCE_TEXT_FRAGMENTS, timeout=1500)
            if not clicked:
                no_form = (len(text_fields) == 0 and len(radios) == 0)
                if no_form and blank_count < 4:
                    blank_count += 1
                    log.info("apply_blank_wait", candidatura_id=candidatura_id, step=step,
                             blank_count=blank_count)
                    await page.wait_for_timeout(3000)
                    continue
                shot = await _screenshot(
                    page, dest_dir=screenshot_dir, prefix=f"{candidatura_id}_stuck"
                )
                raise RuntimeError(f"sem botao para avancar (screenshot {shot})")
            blank_count = 0

            await page.wait_for_timeout(1500)
            signature = await _form_signature(page)
            if signature == prev_signature:
                repeat_count += 1
                if repeat_count >= 2:
                    unfilled = await _find_required_empty_text(page)
                    if unfilled:
                        first = unfilled[0]
                        label = (first.get("label") or "").strip() or (
                            first.get("name") or "campo obrigatório"
                        )
                        shot = await _screenshot(
                            page, dest_dir=screenshot_dir,
                            prefix=f"{candidatura_id}_pending_required_{step}",
                        )
                        return PendingQuestion(
                            field_id=first.get("name") or label[:80],
                            pergunta=label,
                            screenshot_path=shot,
                        )
                    shot = await _screenshot(
                        page, dest_dir=screenshot_dir,
                        prefix=f"{candidatura_id}_stalled_{step}",
                    )
                    raise RuntimeError(
                        f"formulario nao avancou apos {repeat_count + 1} cliques "
                        f"(screenshot {shot})"
                    )
            else:
                repeat_count = 0
            prev_signature = signature

        shot = await _screenshot(
            page, dest_dir=screenshot_dir, prefix=f"{candidatura_id}_max_steps"
        )
        raise RuntimeError(f"max_steps atingido (screenshot {shot})")
    finally:
        await page.close()
