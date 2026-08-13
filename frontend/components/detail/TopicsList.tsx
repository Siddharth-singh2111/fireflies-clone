"use client";

import { ListTree, Play } from "lucide-react";
import type { Topic } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";

export function TopicsList({ topics, onSeek }: { topics: Topic[]; onSeek: (ms: number) => void }) {
  if (topics.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border p-4 text-center text-sm text-muted-foreground">
        No topics detected.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="mb-2 flex items-center gap-2">
        <ListTree className="h-4 w-4 text-primary" />
        <h3 className="font-semibold">Topics & Chapters</h3>
      </div>
      {topics.map((t) => (
        <button
          key={t.id}
          onClick={() => onSeek(t.start_ms)}
          className="group flex w-full items-center gap-3 rounded-md border border-transparent px-2 py-2 text-left hover:border-border hover:bg-muted"
        >
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground group-hover:bg-primary group-hover:text-primary-foreground">
            <Play className="h-3 w-3" />
          </span>
          <span className="min-w-0 flex-1 truncate text-sm font-medium">{t.title}</span>
          <span className="font-mono text-xs tabular-nums text-muted-foreground">
            {formatTimestamp(t.start_ms)}
          </span>
        </button>
      ))}
    </div>
  );
}
