WIP_EXCLUDE = "05_ai-mlops/"

WIP_ADMONITION = """\
!!! warning "Work in Progress"
    This section is under active development and subject to change.

"""


def on_page_markdown(markdown, *, page, config, files):
    if page.file.src_path.startswith(WIP_EXCLUDE):
        return markdown
    return WIP_ADMONITION + markdown


def on_page_context(context, *, page, config, nav):
    if not page.file.src_path.startswith(WIP_EXCLUDE):
        page.meta.setdefault("status", "wip")
    return context
