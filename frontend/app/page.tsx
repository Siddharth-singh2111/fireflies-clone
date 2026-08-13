"use client";

import * as React from "react";
import { ArrowUpDown, Plus, Search, Tag as TagIcon, Video } from "lucide-react";
import { useMeetings, useTags } from "@/lib/hooks";
import type { SortOption } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { EmptyState, Spinner } from "@/components/ui/misc";
import { MeetingCard } from "@/components/meetings/MeetingCard";
import { useCreateMeetingModal } from "@/components/layout/AppShell";

const SORTS: { value: SortOption; label: string }[] = [
  { value: "recent", label: "Most recent" },
  { value: "oldest", label: "Oldest" },
  { value: "title", label: "Title (A–Z)" },
  { value: "duration", label: "Longest" },
];

const PAGE_SIZE = 12;

export default function DashboardPage() {
  const openCreate = useCreateMeetingModal();
  const [q, setQ] = React.useState("");
  const [debouncedQ, setDebouncedQ] = React.useState("");
  const [tag, setTag] = React.useState("");
  const [sort, setSort] = React.useState<SortOption>("recent");
  const [page, setPage] = React.useState(1);

  React.useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedQ(q.trim());
      setPage(1);
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  const { data: tags } = useTags();
  const { data, isLoading, isFetching } = useMeetings({
    q: debouncedQ || undefined,
    tag: tag || undefined,
    sort,
    page,
    page_size: PAGE_SIZE,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 md:px-6">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Meetings</h1>
          <p className="text-sm text-muted-foreground">
            {data ? `${data.total} meeting${data.total === 1 ? "" : "s"}` : "Loading…"}
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" /> New meeting
        </Button>
      </div>

      {/* Filter bar */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[220px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by title or participant…"
            className="h-10 w-full rounded-md border border-input bg-card pl-9 pr-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        <div className="relative">
          <TagIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <select
            value={tag}
            onChange={(e) => {
              setTag(e.target.value);
              setPage(1);
            }}
            className="h-10 appearance-none rounded-md border border-input bg-card pl-9 pr-8 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">All tags</option>
            {tags?.map((t) => (
              <option key={t.id} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div className="relative">
          <ArrowUpDown className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortOption)}
            className="h-10 appearance-none rounded-md border border-input bg-card pl-9 pr-8 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {isFetching && !isLoading && <Spinner className="text-muted-foreground" />}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-44 animate-pulse rounded-lg border border-border bg-muted/40" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((m) => (
              <MeetingCard key={m.id} meeting={m} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        <EmptyState
          icon={<Video className="h-10 w-10" />}
          title={debouncedQ || tag ? "No meetings match your filters" : "No meetings yet"}
          description={
            debouncedQ || tag
              ? "Try clearing the search or tag filter."
              : "Create your first meeting by pasting or uploading a transcript."
          }
          action={
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" /> New meeting
            </Button>
          }
        />
      )}
    </div>
  );
}
