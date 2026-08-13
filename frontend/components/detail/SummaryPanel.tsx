"use client";

import { RefreshCw, Sparkles } from "lucide-react";
import type { Summary } from "@/lib/types";
import { Badge, Spinner } from "@/components/ui/misc";
import { Button } from "@/components/ui/button";
import { useRegenerateSummary } from "@/lib/hooks";

const SENTIMENT_STYLES: Record<string, string> = {
  Positive: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  Negative: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  Neutral: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
};

export function SummaryPanel({ meetingId, summary }: { meetingId: number; summary?: Summary | null }) {
  const regen = useRegenerateSummary(meetingId);
  const keywords = summary?.keywords?.split(",").map((k) => k.trim()).filter(Boolean) ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h3 className="font-semibold">AI Summary</h3>
          {summary && (
            <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
              {summary.generated_by}
            </span>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={() => regen.mutate()} disabled={regen.isPending}>
          {regen.isPending ? <Spinner /> : <RefreshCw className="h-3.5 w-3.5" />}
          Regenerate
        </Button>
      </div>

      {summary?.overview ? (
        <p className="text-sm leading-relaxed text-foreground/90">{summary.overview}</p>
      ) : (
        <p className="text-sm text-muted-foreground">
          No summary yet. Click “Regenerate” to create one from the transcript.
        </p>
      )}

      {summary?.sentiment && (
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">Sentiment</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              SENTIMENT_STYLES[summary.sentiment] ?? SENTIMENT_STYLES.Neutral
            }`}
          >
            {summary.sentiment}
          </span>
        </div>
      )}

      {keywords.length > 0 && (
        <div>
          <span className="mb-1.5 block text-xs font-medium text-muted-foreground">Keywords</span>
          <div className="flex flex-wrap gap-1.5">
            {keywords.map((k) => (
              <Badge key={k}>{k}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
