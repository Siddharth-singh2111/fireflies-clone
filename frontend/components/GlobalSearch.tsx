"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, CornerDownLeft } from "lucide-react";
import { api } from "@/lib/api";
import { formatTimestamp, highlightParts } from "@/lib/utils";
import { Spinner } from "@/components/ui/misc";

/** Global transcript search with a debounced dropdown of matching lines. */
export function GlobalSearch() {
  const router = useRouter();
  const [q, setQ] = React.useState("");
  const [debounced, setDebounced] = React.useState("");
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);

  React.useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const { data, isFetching } = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => api.globalSearch(debounced),
    enabled: debounced.length >= 2,
  });

  const go = (meetingId: number, startMs: number) => {
    setOpen(false);
    setQ("");
    router.push(`/meetings/${meetingId}?t=${startMs}`);
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Search across all transcripts…"
          className="h-10 w-full rounded-md border border-input bg-muted/50 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>

      {open && debounced.length >= 2 && (
        <div className="absolute z-40 mt-2 max-h-96 w-full overflow-y-auto rounded-lg border border-border bg-card shadow-xl scroll-thin animate-fade-in">
          {isFetching && (
            <div className="flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground">
              <Spinner /> Searching…
            </div>
          )}
          {!isFetching && data && data.hits.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-muted-foreground">
              No matches for “{debounced}”.
            </div>
          )}
          {data?.hits.map((hit) => (
            <button
              key={hit.segment_id}
              onClick={() => go(hit.meeting_id, hit.start_ms)}
              className="flex w-full flex-col gap-0.5 border-b border-border px-4 py-3 text-left last:border-0 hover:bg-muted"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-primary">{hit.meeting_title}</span>
                <span className="text-[11px] text-muted-foreground">
                  {hit.speaker ? `${hit.speaker} · ` : ""}
                  {formatTimestamp(hit.start_ms)}
                </span>
              </div>
              <p className="text-sm text-foreground/90">
                {highlightParts(hit.snippet, debounced).map((p, i) =>
                  p.hit ? (
                    <mark key={i} className="hl">
                      {p.text}
                    </mark>
                  ) : (
                    <span key={i}>{p.text}</span>
                  ),
                )}
              </p>
            </button>
          ))}
          {data && data.hits.length > 0 && (
            <div className="flex items-center gap-1 px-4 py-2 text-[11px] text-muted-foreground">
              <CornerDownLeft className="h-3 w-3" /> Click a result to jump to that moment
            </div>
          )}
        </div>
      )}
    </div>
  );
}
