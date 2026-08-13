"use client";

import * as React from "react";
import Link from "next/link";
import { CheckSquare, Clock, MessageSquareText, MoreVertical, Trash2 } from "lucide-react";
import type { MeetingListItem } from "@/lib/types";
import { formatDuration, relativeDate } from "@/lib/utils";
import { Avatar, Badge } from "@/components/ui/misc";
import { useDeleteMeeting } from "@/lib/hooks";

export function MeetingCard({ meeting }: { meeting: MeetingListItem }) {
  const del = useDeleteMeeting();
  const [menuOpen, setMenuOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const onDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuOpen(false);
    if (confirm(`Delete “${meeting.title}”? This cannot be undone.`)) {
      del.mutate(meeting.id);
    }
  };

  return (
    <Link
      href={`/meetings/${meeting.id}`}
      className="group relative flex flex-col rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-md"
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3 className="line-clamp-2 font-semibold leading-snug group-hover:text-primary">
          {meeting.title}
        </h3>
        <div ref={menuRef} className="relative shrink-0">
          <button
            onClick={(e) => {
              e.preventDefault();
              setMenuOpen((v) => !v);
            }}
            className="rounded p-1 text-muted-foreground opacity-0 hover:bg-muted group-hover:opacity-100"
            aria-label="Meeting options"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-8 z-20 w-36 overflow-hidden rounded-md border border-border bg-card shadow-lg">
              <button
                onClick={onDelete}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-muted"
              >
                <Trash2 className="h-4 w-4" /> Delete
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
        <span>{relativeDate(meeting.meeting_date)}</span>
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" /> {formatDuration(meeting.duration_sec)}
        </span>
        <span className="flex items-center gap-1">
          <MessageSquareText className="h-3 w-3" /> {meeting.segment_count} lines
        </span>
        {meeting.action_item_count > 0 && (
          <span className="flex items-center gap-1">
            <CheckSquare className="h-3 w-3" /> {meeting.action_item_count}
          </span>
        )}
      </div>

      {meeting.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {meeting.tags.map((t) => (
            <Badge key={t.id}>{t.name}</Badge>
          ))}
        </div>
      )}

      <div className="mt-auto flex items-center justify-between pt-1">
        <div className="flex -space-x-2">
          {meeting.participants.slice(0, 4).map((p) => (
            <span key={p.id} className="ring-2 ring-card rounded-full">
              <Avatar name={p.name} size={26} />
            </span>
          ))}
          {meeting.participants.length > 4 && (
            <span className="flex h-[26px] w-[26px] items-center justify-center rounded-full bg-muted text-[10px] font-medium ring-2 ring-card">
              +{meeting.participants.length - 4}
            </span>
          )}
        </div>
        <span className="text-xs font-medium capitalize text-muted-foreground">{meeting.status}</span>
      </div>
    </Link>
  );
}
