"use client";

import * as React from "react";
import { ChevronDown, ChevronUp, MessageSquarePlus, Search, X } from "lucide-react";
import type { Segment, Speaker } from "@/lib/types";
import { cn, formatTimestamp, highlightParts } from "@/lib/utils";
import { Avatar } from "@/components/ui/misc";

interface TranscriptPanelProps {
  segments: Segment[];
  speakers: Speaker[];
  currentMs: number;
  onSeek: (ms: number) => void;
  onComment?: (segment: Segment) => void;
}

export function TranscriptPanel({
  segments,
  speakers,
  currentMs,
  onSeek,
  onComment,
}: TranscriptPanelProps) {
  const [search, setSearch] = React.useState("");
  const [matchIndex, setMatchIndex] = React.useState(0);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const lineRefs = React.useRef<Record<number, HTMLDivElement | null>>({});
  const userScrolledRef = React.useRef(false);

  const speakerById = React.useMemo(() => {
    const map = new Map<number, Speaker>();
    for (const s of speakers) map.set(s.id, s);
    return map;
  }, [speakers]);

  // Which segment is "active" for the current playhead position.
  const activeId = React.useMemo(() => {
    let active: number | null = null;
    for (const seg of segments) {
      if (currentMs >= seg.start_ms && currentMs < seg.end_ms) return seg.id;
      if (seg.start_ms <= currentMs) active = seg.id;
    }
    return active;
  }, [segments, currentMs]);

  // Segments containing the search term (for match navigation).
  const matchIds = React.useMemo(() => {
    if (search.trim().length < 1) return [];
    const term = search.toLowerCase();
    return segments.filter((s) => s.text.toLowerCase().includes(term)).map((s) => s.id);
  }, [segments, search]);

  React.useEffect(() => setMatchIndex(0), [search]);

  // Auto-scroll the active line into view (unless the user is scrolling).
  React.useEffect(() => {
    if (activeId == null || userScrolledRef.current) return;
    lineRefs.current[activeId]?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [activeId]);

  const jumpToMatch = (index: number) => {
    if (matchIds.length === 0) return;
    const wrapped = (index + matchIds.length) % matchIds.length;
    setMatchIndex(wrapped);
    lineRefs.current[matchIds[wrapped]]?.scrollIntoView({ block: "center", behavior: "smooth" });
  };

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card">
      {/* Search header */}
      <div className="flex items-center gap-2 border-b border-border p-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") jumpToMatch(matchIndex + (e.shiftKey ? -1 : 1));
            }}
            placeholder="Search within transcript…"
            className="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        {search && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <span className="tabular-nums">
              {matchIds.length ? `${matchIndex + 1}/${matchIds.length}` : "0"}
            </span>
            <button
              onClick={() => jumpToMatch(matchIndex - 1)}
              disabled={!matchIds.length}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
              aria-label="Previous match"
            >
              <ChevronUp className="h-4 w-4" />
            </button>
            <button
              onClick={() => jumpToMatch(matchIndex + 1)}
              disabled={!matchIds.length}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
              aria-label="Next match"
            >
              <ChevronDown className="h-4 w-4" />
            </button>
            <button onClick={() => setSearch("")} className="rounded p-1 hover:bg-muted" aria-label="Clear">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Lines */}
      <div
        ref={containerRef}
        onWheel={() => (userScrolledRef.current = true)}
        className="scroll-thin flex-1 overflow-y-auto p-2"
        onMouseLeave={() => (userScrolledRef.current = false)}
      >
        {segments.map((seg) => {
          const speaker = seg.speaker_id != null ? speakerById.get(seg.speaker_id) : undefined;
          const name = speaker?.display_name ?? "Speaker";
          const isActive = seg.id === activeId;
          const isMatch = matchIds[matchIndex] === seg.id;

          return (
            <div
              key={seg.id}
              ref={(el) => {
                lineRefs.current[seg.id] = el;
              }}
              onClick={() => onSeek(seg.start_ms)}
              className={cn(
                "group flex cursor-pointer gap-3 rounded-md px-2 py-2 transition-colors",
                isActive ? "bg-accent" : "hover:bg-muted",
                isMatch && "ring-2 ring-primary/50",
              )}
            >
              <div className="pt-0.5">
                <Avatar name={name} size={30} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-0.5 flex items-center gap-2">
                  <span
                    className="text-sm font-semibold"
                    style={{ color: speaker?.color ?? undefined }}
                  >
                    {name}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSeek(seg.start_ms);
                    }}
                    className={cn(
                      "font-mono text-[11px] tabular-nums text-muted-foreground hover:text-primary",
                    )}
                  >
                    {formatTimestamp(seg.start_ms)}
                  </button>
                  {onComment && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onComment(seg);
                      }}
                      className="ml-auto rounded p-1 text-muted-foreground opacity-0 hover:bg-background hover:text-primary group-hover:opacity-100"
                      aria-label="Add comment"
                    >
                      <MessageSquarePlus className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <p className={cn("text-sm leading-relaxed", isActive ? "text-foreground" : "text-foreground/85")}>
                  {highlightParts(seg.text, search).map((p, i) =>
                    p.hit ? (
                      <mark key={i} className="hl">
                        {p.text}
                      </mark>
                    ) : (
                      <span key={i}>{p.text}</span>
                    ),
                  )}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
