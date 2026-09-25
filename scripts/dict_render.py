#!/usr/bin/env python3
"""
dict_render.py
===============

Turns a DictCapture's raw content (from dict_extract.py) into actual
dictionary-file text, and generates shloka dictionary keys from a
shloka's ending ॥...॥ marker. Imports generate_indices.py for
parse_divs/apply_splices/commentary_label/BRACKET_ATTR_SPAN_RE rather
than duplicating them — unlike dict_extract.py, there's no reason for
THIS module to be import-independent, since it only ever runs inside
generate_dict.py, which already imports generate_indices.py anyway.

NOT yet handled here (deliberately) — see generate_dict.py's own
docstring for why: the shloka-format record's "++" summary line, and
the heuristic for associating a shloka div with the gloss divs that
follow it. Both are open design questions, not implementation gaps.
"""
from __future__ import annotations

import re

import dict_extract as de
import generate_indices as gi


# ---------------------------------------------------------------------------
# Notes-format entry text: `.action` -> <i>, gloss div -> <b>label</b><i>...</i>
# (or just <i>...</i> with no label). Everything else (markdown **bold**,
# literal ॥...॥ markers, plain text) is left completely untouched — per
# the spec's own worked example, **सूतः** stays as literal asterisks in
# the dict output; only these two transforms apply.
# ---------------------------------------------------------------------------

def render_action_spans(text: str, source_for_warning: object = "") -> str:
    """Only `.action`-classed bracket/paren spans become <i>...</i>; any
    OTHER `{: .cls}` span is left exactly as authored (the spec only
    documents `.action` — nothing else)."""
    def repl(m: re.Match) -> str:
        if m.group("cls") != "action":
            return m.group(0)
        content = m.group("bracketed") if m.group("bracketed") is not None else m.group("bare")
        return f"<i>{content}</i>"
    return gi.BRACKET_ATTR_SPAN_RE.sub(repl, text)


def render_structural_divs(text: str, gloss_types: dict) -> str:
    """Two kinds of div, in one pass (they're always siblings, never
    nested in each other, in every real example seen so far):
      - a "shloka"-classed div is unwrapped to its bare inner verse text
        — never <i>-wrapped, exactly as the dedicated Shloka format
        treats verse text; only its structural <div> tag is noise here.
      - any OTHER div whose base class is one gloss_types.yaml routes
        (almost always "gloss" itself) becomes
        `<b>{label}</b><i>{content}</i>` (or just `<i>{content}</i>` if
        this type has no label) — content already has its own `.action`
        spans converted (render_notes_entry runs render_action_spans
        over the WHOLE text first, before this).
    A div nested inside either of the above (not seen in any real
    content so far) is left unconverted, deliberately — rendering it
    would need a nesting decision the spec doesn't make."""
    tree = gi.parse_divs(text)
    splices: list[tuple[int, int, str]] = []
    recognized = gi.recognized_div_classes(gloss_types)

    for node in tree:
        inner = text[node.tag_end:node.inner_end].strip()
        if node.base_cls == "shloka":
            splices.append((node.start, node.end, inner))
        elif node.base_cls in recognized:
            attrs = node.attrs_str
            type_key = gi.parse_attrs(attrs).get("data-type", "").strip()
            label = gi.commentary_label(type_key, attrs, gloss_types)
            rendered = f"<b>{label}</b><i>{inner}</i>" if label else f"<i>{inner}</i>"
            splices.append((node.start, node.end, rendered))

    return gi.apply_splices(text, splices) if splices else text


def render_notes_entry(raw_content: str, gloss_types: dict, source_for_warning: object = "") -> str:
    """The full notes-format transform for one dict entry's raw content
    (a DictCapture.raw_content). The chapter_key full-chapter entry uses
    render_full_chapter_entry instead."""
    text = render_action_spans(raw_content, source_for_warning)
    text = render_structural_divs(text, gloss_types)
    return text.strip()


# ---------------------------------------------------------------------------
# Notes-format full-chapter entry (dict.chapter_key) — tags_keep rendering
# ---------------------------------------------------------------------------
#
# The whole chapter as one entry. Input is the chapter's dict view
# (dict_extract.extract_dict_views: <dict> tags gone, display="False"
# entries gone, <dictref/> resolved to bword links). Rules:
#   - Every <div> is named by its gloss data-type (for a gloss-routed
#     class, see gloss_types.yaml) or else by its class. A div whose
#     name is in `keep` keeps its content (a gloss as
#     <b>label</b><i>...</i>, anything else as plain text); any other
#     div is dropped WITH its content. Nested divs follow the same rule
#     independently, so an unlisted div inside a kept one is dropped.
#     A div with no class at all is transparent (content kept).
#   - <topic> tags go, their content stays. <details> blocks (and
#     <audio>/<video>/<script>/<style>, HTML comments) go entirely.
#   - Markdown: `.action` spans -> <i>; other {: .cls} spans -> their
#     text; headings -> <b>heading</b>; links (incl. xref() macros) ->
#     their text; images, footnote markers/definitions, {{ }}/{% %}
#     macros, stray {: ...} attribute lists -> removed. **bold**,
#     *italic*, list markers and newlines are left exactly as written.
#   - HTML: only <b>, <i>, <u>, <br> and bword:// links survive; every
#     other tag is removed and its text kept.

DEFAULT_KEEP_EXTRA = ("shloka",)  # kept by default alongside every gloss type
NEVER_KEEP = ("details",)         # can't be listed in tags_keep

_DROP_BLOCK_RE = re.compile(
    r"<(details|audio|video|script|style)\b.*?</\1\s*>|<!--.*?-->", re.DOTALL | re.IGNORECASE,
)
_JINJA_RE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)
_IMAGE_RE = re.compile(r"!\[[^\]\n]*\]\([^)\n]*\)")
# a footnote definition line plus any indented continuation lines
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^[^\]\n]+\]:[^\n]*(?:\n[ \t]+[^\n]*)*", re.MULTILINE)
_FOOTNOTE_REF_RE = re.compile(r"\[\^[^\]\n]+\]")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\([^)\n]*\)")
_HEADING_RE = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$", re.MULTILINE)
_ATTR_LIST_RE = re.compile(r"[ \t]*\{[:#][^}\n]*\}")
_BWORD_LINK_RE = re.compile(r'<a href="bword://[^"]*">.*?</a>', re.DOTALL)
_KEPT_TAG_RE = re.compile(r"</?(?:b|i|u)\s*>|<br\s*/?>", re.IGNORECASE)
_ANY_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_EXTRA_BLANK_LINES_RE = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")
_GONE = de.REMOVED_MARK  # marks where something was removed, until the final cleanup
_GONE_LINE_RE = re.compile(r"^[ \t\x01]*\x01[ \t\x01]*(?:\n|\Z)", re.MULTILINE)


def div_name(node: "gi.DivNode", gloss_classes: set[str]) -> str:
    """What a div is called in tags_keep: its gloss data-type if its
    class is gloss-routed (and it has one), otherwise its base class."""
    if node.base_cls in gloss_classes:
        dt = gi.parse_attrs(node.attrs_str).get("data-type", "").strip().lower()
        if dt:
            return dt
    return node.base_cls


def div_names_in(text: str, gloss_types: dict) -> set[str]:
    """Every div name (see div_name) used anywhere in `text`."""
    gloss_classes = gi.recognized_div_classes(gloss_types)
    names: set[str] = set()

    def walk(nodes):
        for n in nodes:
            if n.base_cls:
                names.add(div_name(n, gloss_classes))
            walk(n.children)
    walk(gi.parse_divs(text))
    return names


def default_tags_keep(gloss_types: dict) -> set[str]:
    return set(gloss_types) | set(DEFAULT_KEEP_EXTRA)


def _render_divs(text: str, gloss_types: dict, keep: set[str], dropped: dict[str, int]) -> str:
    gloss_classes = gi.recognized_div_classes(gloss_types)

    def render_span(start: int, end: int, nodes: list) -> str:
        out, pos = [], start
        for n in nodes:
            out.append(text[pos:n.start])
            out.append(render_node(n))
            pos = n.end
        out.append(text[pos:end])
        return "".join(out)

    def render_node(n) -> str:
        inner = render_span(n.tag_end, n.inner_end, n.children).strip()
        if not n.base_cls:
            return inner
        name = div_name(n, gloss_classes)
        if name not in keep:
            dropped[name] = dropped.get(name, 0) + 1
            return _GONE
        if n.base_cls in gloss_classes:
            type_key = gi.parse_attrs(n.attrs_str).get("data-type", "").strip().lower()
            label = gi.commentary_label(type_key, n.attrs_str, gloss_types)
            return f"<b>{label}</b><i>{inner}</i>" if label else f"<i>{inner}</i>"
        return inner

    return render_span(0, len(text), gi.parse_divs(text))


def _action_and_attr_spans(text: str) -> str:
    """`.action` spans -> <i>...</i>; any other {: .cls} span -> just its text."""
    def repl(m: re.Match) -> str:
        content = m.group("bracketed") if m.group("bracketed") is not None else m.group("bare")
        return f"<i>{content}</i>" if m.group("cls") == "action" else content
    return gi.BRACKET_ATTR_SPAN_RE.sub(repl, text)


def render_full_chapter_entry(
    dict_body: str, gloss_types: dict, keep: set[str], dropped: dict[str, int] | None = None,
) -> str:
    """The notes-format chapter_key entry text for a whole chapter (see
    the rules above). `dropped` (optional) is filled with
    {div name: count} for every div left out, for the caller to report."""
    dropped = {} if dropped is None else dropped
    text = gi.TOPIC_OPEN_RE.sub("", dict_body)
    text = gi.TOPIC_CLOSE_RE.sub("", text)
    text = _DROP_BLOCK_RE.sub(_GONE, text)
    text = _action_and_attr_spans(text)
    text = _render_divs(text, gloss_types, keep, dropped)

    text = _JINJA_RE.sub(_GONE, text)
    text = _IMAGE_RE.sub(_GONE, text)
    text = _FOOTNOTE_DEF_RE.sub(_GONE, text)
    text = _FOOTNOTE_REF_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _ATTR_LIST_RE.sub("", text)
    text = _HEADING_RE.sub(lambda m: f"<b>{m.group(1).strip()}</b>", text)

    # Only <b>/<i>/<u>/<br> and bword links survive; every other tag goes
    # (its text stays). Protected spans are swapped out first so the
    # generic strip can't touch them.
    protected: list[str] = []

    def protect(m: re.Match) -> str:
        protected.append(m.group(0))
        return f"\x00{len(protected) - 1}\x00"

    text = _BWORD_LINK_RE.sub(protect, text)
    text = _KEPT_TAG_RE.sub(protect, text)
    text = _ANY_TAG_RE.sub("", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: protected[int(m.group(1))], text)

    # A line that held nothing but removed material goes away entirely
    # (rather than leaving a blank line the source never had); elsewhere
    # the marker just disappears.
    text = _GONE_LINE_RE.sub("", text).replace(_GONE, "")
    text = _EXTRA_BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Shloka key generation
# ---------------------------------------------------------------------------

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# The LAST ॥...॥ span in a shloka's text is its ending marker (spec:
# "found at the end of the shloka's last line, flanked by ॥, ignoring
# spaces") — this matches every ॥...॥ span; callers take the last match.
MARKER_RE = re.compile(r"॥\s*([०-९।.\-\s]+?)\s*॥")

NUMBER_SPLIT_RE = re.compile(r"[।.\-\s]+")


class ShlokaKeyError(ValueError):
    def __init__(self, source: object, message: str):
        self.source = source
        super().__init__(f"{source}: {message}")


def extract_marker_numbers(shloka_text: str, source_for_warning: object = "") -> list[int]:
    """The numbers inside the LAST ॥...॥ marker in `shloka_text`, left to
    right, as ints (Devanagari digits only — the site's own convention).
    Raises ShlokaKeyError if there's no ॥...॥ marker at all."""
    matches = list(MARKER_RE.finditer(shloka_text))
    if not matches:
        raise ShlokaKeyError(source_for_warning, "no ॥...॥ ending marker found in shloka text")
    inner = matches[-1].group(1)
    numbers = []
    for piece in NUMBER_SPLIT_RE.split(inner):
        piece = piece.strip()
        if not piece:
            continue
        numbers.append(int(piece.translate(_DEVANAGARI_DIGITS)))
    if not numbers:
        raise ShlokaKeyError(source_for_warning, f"॥{inner}॥ marker has no digits in it")
    return numbers


def parse_shloka_key_prefix(prefix: str, source_for_warning: object = "") -> tuple[str, list[int]]:
    """"KS,9,99" -> ("KS", [1, 2]) — name, plus one target zero-pad WIDTH
    per number wanted (width = that token's own character count; the
    token's actual digit value is never used, only how many digits long
    it's written)."""
    parts = [p.strip() for p in prefix.split(",")]
    if len(parts) < 2:
        raise ShlokaKeyError(source_for_warning, f'shloka_key_prefix "{prefix}" needs a name AND at least one width, e.g. "KS,99"')
    name, width_tokens = parts[0], parts[1:]
    if not name:
        raise ShlokaKeyError(source_for_warning, f'shloka_key_prefix "{prefix}" has no name before the first comma')
    widths = []
    for tok in width_tokens:
        if not tok.isdigit():
            raise ShlokaKeyError(source_for_warning, f'shloka_key_prefix "{prefix}": "{tok}" is not a plain digit-width token (e.g. "9", "99")')
        widths.append(len(tok))
    return name, widths


def shloka_dict_key(shloka_text: str, prefix: str, source_for_warning: object = "") -> str:
    """The full "e:NAME-w1-w2-..." key for one shloka, per the confirmed
    rule: take exactly as many trailing numbers from the ॥...॥ marker as
    there are width-tokens in the prefix (always ending in the shloka's
    own number, since that's always the LAST number in the marker), then
    pad each — left to right — to its matching width-token's own digit
    count. Fewer marker numbers than requested width-tokens is a hard
    error (there's nothing sensible to do with a missing hierarchy
    level), never a silent fallback."""
    name, widths = parse_shloka_key_prefix(prefix, source_for_warning)
    numbers = extract_marker_numbers(shloka_text, source_for_warning)
    k = len(widths)
    if len(numbers) < k:
        raise ShlokaKeyError(
            source_for_warning,
            f'shloka_key_prefix "{prefix}" wants {k} number(s) but the marker only has {len(numbers)} '
            f"({numbers}) — add the missing hierarchy level to the source, or shorten the prefix",
        )
    taken = numbers[-k:]
    parts = [str(n).zfill(w) for n, w in zip(taken, widths)]
    return f"e:{name}-{'-'.join(parts)}"


# ---------------------------------------------------------------------------
# Shloka-format record body (everything BELOW the "====" line). The
# shloka's own text above "====" is just its stripped <div class="shloka">
# inner content — see render_structural_divs, already used for this by
# generate_dict.py.
# ---------------------------------------------------------------------------

_BLANK_LINE_RE = re.compile(r"\n[ \t]*\n")
_TRAILING_SOFT_BREAK_RE = re.compile(r"[ \t]{2,}\n")


def render_shloka_gloss_text(inner: str) -> str:
    """Shloka-format-only whitespace rule (dict-workflow.md's "Special
    Note"): a record can't contain a literal blank line, so any blank
    line WITHIN one gloss's own content, and any markdown trailing
    double-space soft-break, both become an explicit <br>."""
    text = _BLANK_LINE_RE.sub("\n<br>\n", inner)
    text = _TRAILING_SOFT_BREAK_RE.sub("<br>\n", text)
    return text.strip()


def render_shloka_group(
    group_text: str, gloss_types: dict, source_for_warning: object = "",
) -> tuple[str | None, list[str]]:
    """`group_text` is everything between one shloka div and the next
    shloka div (or end of section) — i.e. exactly the glosses attached
    to that shloka, per the confirmed dict.type: shloka grouping rule
    (this function is never used for dict.type: notes, where a shloka
    gets no special treatment at all — see render_structural_divs).

    Returns (anvaya_text_or_None, [gloss_block, ...]):
      anvaya_text  — the अन्वयः-type gloss's own content, tags stripped,
                     whitespace collapsed to single spaces (for the "++"
                     line) — None if this shloka has no अन्वयः gloss (in
                     which case the caller omits the "++" line entirely).
      gloss_block  — one "<b>{label}</b>\\n<i>{content}</i>" (or just
                     "<i>{content}</i>" with no label) per gloss div
                     found, in document order — caller joins these with
                     "\\n<br>" between them (a separator, per the
                     spec's worked example: no trailing <br> after the
                     last one; the next label follows on the <br>'s
                     own line, not a new one)."""
    text = render_action_spans(group_text, source_for_warning)
    tree = gi.parse_divs(text)
    recognized = gi.recognized_div_classes(gloss_types)

    anvaya: str | None = None
    blocks: list[str] = []
    for node in tree:
        if node.base_cls not in recognized:
            continue  # e.g. a stray "shloka" div here would be a grouping bug — leave alone, don't guess
        attrs = node.attrs_str
        type_key = gi.parse_attrs(attrs).get("data-type", "").strip()
        label = gi.commentary_label(type_key, attrs, gloss_types)
        raw_inner = text[node.tag_end:node.inner_end]
        content = render_shloka_gloss_text(raw_inner)
        blocks.append(f"<b>{label}</b>\n<i>{content}</i>" if label else f"<i>{content}</i>")
        if type_key == "anvaya" and anvaya is None:
            anvaya = re.sub(r"\s+", " ", raw_inner).strip()
            anvaya = re.sub(r"\s*।\s*$", "", anvaya)  # drop a trailing single danda — not meaningful on the "++" line

    return anvaya, blocks


def shloka_record(
    shloka_text: str, skip: list[str], syns: list[str], anvaya: str | None, gloss_blocks: list[str],
) -> str:
    """Assembles one shloka-format record: the shloka text (as given —
    caller passes it already stripped of its <div> wrapper, e.g. via
    render_structural_divs), the "====" delimiter, then the top part
    ("-"/"+"/"++" lines, each omitted entirely when empty) and the
    bottom part (glosses, "\\n<br>"-joined)."""
    lines = [shloka_text.strip(), "===="]
    if skip:
        lines.append(f"- {';'.join(skip)}")
    if syns:
        lines.append(f"+ {';'.join(syns)}")
    if anvaya:
        lines.append(f"++ {anvaya}")
    lines.append("\n<br>".join(gloss_blocks))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Notes-format entry rendering — the spec's own worked example
    raw = (
        "[(ततः प्रविशति मृगानुसारी सशरचापहस्तो राजा रथेन सूतश्च)]{: .action}   \n"
        "**सूतः** – [(राजानं मृगं चावलोक्य)]{: .action} आयुष्मन् ।\n"
        "कृष्णसारे ददच्चक्षुस्त्वयि चाधिज्यकार्मुके ।\n"
        "मृगानुसारिणं साक्षात्पश्यामीव पिनाकिनम् ॥ ६॥\n"
        '<div class="gloss" data-type="notes">\n'
        "अधिज्यकार्मुके = अध्यारोपितधनुषि (ज्याम् अधिगतम् अधिज्यम्, अधिज्यं कार्मुकः यस्य स, तस्मिन्) । \n"
        "</div>"
    )
    gloss_types = {"notes": {"class": "gloss", "css_style": "notes"}}  # no "label" key -> no <b> wrapper
    rendered = render_notes_entry(raw, gloss_types)
    assert "**सूतः**" in rendered  # markdown bold left untouched
    assert "<i>(ततः प्रविशति मृगानुसारी सशरचापहस्तो राजा रथेन सूतश्च)</i>" in rendered
    assert "<i>(राजानं मृगं चावलोक्य)</i>" in rendered
    assert rendered.endswith("<i>अधिज्यकार्मुके = अध्यारोपितधनुषि (ज्याम् अधिगतम् अधिज्यम्, अधिज्यं कार्मुकः यस्य स, तस्मिन्) ।</i>")
    assert "<div" not in rendered and "data-type" not in rendered
    print("notes-entry render OK:")
    print(rendered)
    print()

    # Gloss WITH a label (e.g. "tika" with label_from_attr: data-name)
    gloss_types2 = {"tika": {"class": "gloss", "css_style": "tika", "label_from_attr": "data-name"}}
    raw2 = '<div class="gloss" data-type="tika" data-name="सञ्जीविनी">अपीति ॥ ...</div>'
    rendered2 = render_notes_entry(raw2, gloss_types2)
    assert rendered2 == "<b>सञ्जीविनी</b><i>अपीति ॥ ...</i>", rendered2
    print("labeled gloss render OK:", rendered2)
    print()

    # Shloka key generation — the three confirmed examples
    text = "मृगानुसारिणं ...॥५।९।३॥"
    assert shloka_dict_key(text, "KS5,99") == "e:KS5-03"
    assert shloka_dict_key(text, "KS,9,99") == "e:KS-9-03"
    assert shloka_dict_key(text, "R,9,99,999") == "e:R-5-09-003"
    print("shloka key generation OK: e:KS5-03 / e:KS-9-03 / e:R-5-09-003")

    # Too few numbers for the requested hierarchy depth -> hard error
    try:
        shloka_dict_key("...॥५॥", "KS,9,99", "test.md")
        raise AssertionError("expected ShlokaKeyError")
    except ShlokaKeyError as e:
        assert "only has 1" in str(e), str(e)
        print("under-hierarchy error OK:", e)

    print("\nAll self-tests passed.")

    # --- Shloka-format record — the spec's own worked example ---
    group = (
        '<div class="gloss" data-type="anvaya">\n'
        "त्वदावर्जितवारिसम्भृतम् आसां वीरुधां प्रवालम् अनुबन्धि अपि ? "
        "यत् चिरोज्झितालक्तकपाटलेन ते दन्तवाससा तुलाम् आरोहति ।\n"
        "</div>\n\n"
        '<div class="gloss" data-type="tika" data-name="सञ्जीविनी">\n'
        "अपीति ॥ त्वयावर्जितेन सिक्तेन वारिणा सम्भृतं जनितमासां वीरुधां लतानां प्रवालं "
        "पल्लवमनुबन्ध्यप्यनुस्यूतं किम् । ... तुलां साम्यमारोहति गच्छतीत्यर्थः ।\n"
        "</div>"
    )
    shloka_gloss_types = {
        "anvaya": {"class": "gloss", "css_style": "anvaya", "label": "अन्वयः"},
        "tika": {"class": "gloss", "css_style": "tika", "label_from_attr": "data-name"},
    }
    anvaya, blocks = render_shloka_group(group, shloka_gloss_types, "test-shloka.md")
    assert anvaya == (
        "त्वदावर्जितवारिसम्भृतम् आसां वीरुधां प्रवालम् अनुबन्धि अपि ? "
        "यत् चिरोज्झितालक्तकपाटलेन ते दन्तवाससा तुलाम् आरोहति"
    ), anvaya  # trailing danda dropped on the "++" line specifically
    assert len(blocks) == 2
    assert blocks[0] == "<b>अन्वयः</b>\n<i>त्वदावर्जितवारिसम्भृतम् आसां वीरुधां प्रवालम् अनुबन्धि अपि ? यत् चिरोज्झितालक्तकपाटलेन ते दन्तवाससा तुलाम् आरोहति ।</i>"
    assert blocks[1].startswith("<b>सञ्जीविनी</b>\n<i>अपीति")

    shloka_text = (
        "अपि त्वदावर्जितवारिसम्भृतं प्रवालमासामनुबन्धि वीरुधाम् ।\n"
        "चिरोज्झितालक्तकपाटलेन ते तुलां यदारोहति दन्तवाससा ॥३४॥"
    )
    record = shloka_record(shloka_text, ["all"], ["सिञ्च्", "उक्ष्"], anvaya, blocks)
    expected = (
        "अपि त्वदावर्जितवारिसम्भृतं प्रवालमासामनुबन्धि वीरुधाम् ।\n"
        "चिरोज्झितालक्तकपाटलेन ते तुलां यदारोहति दन्तवाससा ॥३४॥\n"
        "====\n"
        "- all\n"
        "+ सिञ्च्;उक्ष्\n"
        "++ त्वदावर्जितवारिसम्भृतम् आसां वीरुधां प्रवालम् अनुबन्धि अपि ? "
        "यत् चिरोज्झितालक्तकपाटलेन ते दन्तवाससा तुलाम् आरोहति\n"
        "<b>अन्वयः</b>\n"
        "<i>त्वदावर्जितवारिसम्भृतम् आसां वीरुधां प्रवालम् अनुबन्धि अपि ? "
        "यत् चिरोज्झितालक्तकपाटलेन ते दन्तवाससा तुलाम् आरोहति ।</i>\n"
        "<br>\n"
        "<b>सञ्जीविनी</b>\n"
        "<i>अपीति ॥ त्वयावर्जितेन सिक्तेन वारिणा सम्भृतं जनितमासां वीरुधां लतानां प्रवालं "
        "पल्लवमनुबन्ध्यप्यनुस्यूतं किम् । ... तुलां साम्यमारोहति गच्छतीत्यर्थः ।</i>"
    )
    assert record == expected, f"\n--- GOT ---\n{record}\n--- EXPECTED ---\n{expected}"
    print("shloka-format worked example matches EXACTLY:")
    print(record)
    print()

    # No अन्वयः gloss at all -> no "++" line
    anvaya_none, blocks_none = render_shloka_group(
        '<div class="gloss" data-type="tika" data-name="X">y</div>', shloka_gloss_types, "test2.md",
    )
    assert anvaya_none is None
    record2 = shloka_record("shloka text ॥१॥", [], ["a"], anvaya_none, blocks_none)
    assert "++" not in record2
    print("no-anvaya -> no ++ line: OK")

    print("\nAll shloka-format self-tests passed too.")
