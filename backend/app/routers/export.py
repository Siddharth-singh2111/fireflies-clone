"""Export a meeting's transcript + summary as Markdown or plain text (bonus).

PDF export is handled on the frontend via the browser's print engine (a styled
print view), which avoids a heavy server-side PDF dependency and always matches
what the user sees. Markdown/TXT are produced here as downloadable files.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session, selectinload

from app import models
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api/meetings/{meeting_id}/export", tags=["export"])


def _fmt_ts(ms: int) -> str:
    total = ms // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _render(m: models.Meeting, markdown: bool) -> str:
    lines: list[str] = []
    h1 = f"# {m.title}" if markdown else m.title.upper()
    lines.append(h1)
    lines.append("")
    lines.append(f"Date: {m.meeting_date:%Y-%m-%d %H:%M}")
    lines.append(f"Duration: {_fmt_ts(m.duration_sec * 1000)}")
    if m.participants:
        lines.append("Participants: " + ", ".join(p.name for p in m.participants))
    lines.append("")

    if m.summary and m.summary.overview:
        lines.append("## Summary" if markdown else "SUMMARY")
        lines.append(m.summary.overview)
        lines.append("")

    if m.action_items:
        lines.append("## Action Items" if markdown else "ACTION ITEMS")
        for a in m.action_items:
            check = "[x]" if a.is_completed else "[ ]"
            who = f" (@{a.assignee})" if a.assignee else ""
            prefix = f"- {check} " if markdown else f"  {check} "
            lines.append(f"{prefix}{a.text}{who}")
        lines.append("")

    if m.topics:
        lines.append("## Topics" if markdown else "TOPICS")
        for t in sorted(m.topics, key=lambda x: x.seq):
            prefix = "- " if markdown else "  - "
            lines.append(f"{prefix}[{_fmt_ts(t.start_ms)}] {t.title}")
        lines.append("")

    lines.append("## Transcript" if markdown else "TRANSCRIPT")
    for seg in sorted(m.segments, key=lambda x: x.seq):
        who = seg.speaker.display_name if seg.speaker else "Speaker"
        ts = _fmt_ts(seg.start_ms)
        if markdown:
            lines.append(f"**[{ts}] {who}:** {seg.text}")
        else:
            lines.append(f"[{ts}] {who}: {seg.text}")
    return "\n".join(lines)


@router.get("", response_class=PlainTextResponse)
def export_meeting(
    meeting_id: int,
    format: str = Query("md", pattern="^(md|txt)$"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    m = (
        db.query(models.Meeting)
        .options(
            selectinload(models.Meeting.participants),
            selectinload(models.Meeting.segments).selectinload(models.TranscriptSegment.speaker),
            selectinload(models.Meeting.action_items),
            selectinload(models.Meeting.topics),
            selectinload(models.Meeting.summary),
        )
        .filter(models.Meeting.id == meeting_id, models.Meeting.user_id == user.id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    body = _render(m, markdown=(format == "md"))
    media = "text/markdown" if format == "md" else "text/plain"
    safe = "".join(c if c.isalnum() else "_" for c in m.title)[:50] or "meeting"
    return PlainTextResponse(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{safe}.{format}"'},
    )
