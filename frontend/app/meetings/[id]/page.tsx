"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  CheckSquare,
  Clock,
  Download,
  FileText,
  ListTree,
  MessageCircleQuestion,
  Pencil,
  Sparkles,
  Trash2,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { useDeleteMeeting, useMeeting } from "@/lib/hooks";
import { cn, formatDuration, relativeDate } from "@/lib/utils";
import { Avatar, Badge, Spinner } from "@/components/ui/misc";
import { Button } from "@/components/ui/button";
import { MediaPlayer, type PlayerHandle } from "@/components/detail/MediaPlayer";
import { TranscriptPanel } from "@/components/detail/TranscriptPanel";
import { SummaryPanel } from "@/components/detail/SummaryPanel";
import { ActionItems } from "@/components/detail/ActionItems";
import { TopicsList } from "@/components/detail/TopicsList";
import { ChatPanel } from "@/components/detail/ChatPanel";
import { EditMeetingModal } from "@/components/meetings/EditMeetingModal";

type Tab = "summary" | "actions" | "topics" | "chat";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "summary", label: "Summary", icon: Sparkles },
  { id: "actions", label: "Actions", icon: CheckSquare },
  { id: "topics", label: "Topics", icon: ListTree },
  { id: "chat", label: "Ask AI", icon: MessageCircleQuestion },
];

export default function MeetingDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const id = Number(params.id);

  const { data: meeting, isLoading, isError } = useMeeting(id);
  const del = useDeleteMeeting();

  const playerRef = React.useRef<PlayerHandle>(null);
  const [currentMs, setCurrentMs] = React.useState(0);
  const [tab, setTab] = React.useState<Tab>("summary");
  const [editOpen, setEditOpen] = React.useState(false);
  const [exportOpen, setExportOpen] = React.useState(false);

  const durationMs = React.useMemo(() => {
    if (!meeting) return 0;
    const fromSegments = meeting.segments.reduce((max, s) => Math.max(max, s.end_ms), 0);
    return Math.max(fromSegments, meeting.duration_sec * 1000);
  }, [meeting]);

  const seekTo = React.useCallback((ms: number) => {
    playerRef.current?.seek(ms);
  }, []);

  // Honour ?t=<ms> deep links from global search once the meeting is loaded.
  const appliedDeepLink = React.useRef(false);
  React.useEffect(() => {
    if (!meeting || appliedDeepLink.current) return;
    const t = searchParams.get("t");
    if (t) {
      appliedDeepLink.current = true;
      const ms = Number(t);
      // Defer so the player has mounted.
      setTimeout(() => seekTo(ms), 100);
    }
  }, [meeting, searchParams, seekTo]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="h-6 w-6 text-primary" />
      </div>
    );
  }

  if (isError || !meeting) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <h2 className="text-lg font-semibold">Meeting not found</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          It may have been deleted or the link is incorrect.
        </p>
        <Link href="/" className="mt-4 inline-block">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4" /> Back to meetings
          </Button>
        </Link>
      </div>
    );
  }

  const onDelete = () => {
    if (confirm(`Delete “${meeting.title}”? This cannot be undone.`)) {
      del.mutate(meeting.id, { onSuccess: () => router.push("/") });
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-5 md:px-6">
      {/* Header */}
      <div className="no-print mb-4">
        <Link
          href="/"
          className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> All meetings
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-xl font-bold tracking-tight md:text-2xl">{meeting.title}</h1>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
              <span>{relativeDate(meeting.meeting_date)}</span>
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" /> {formatDuration(meeting.duration_sec)}
              </span>
              <span className="flex items-center gap-1">
                <Users className="h-3.5 w-3.5" /> {meeting.participants.length} participants
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <div className="relative">
              <Button variant="outline" size="sm" onClick={() => setExportOpen((v) => !v)}>
                <Download className="h-4 w-4" /> Export
              </Button>
              {exportOpen && (
                <div
                  className="absolute right-0 top-10 z-20 w-40 overflow-hidden rounded-md border border-border bg-card shadow-lg"
                  onMouseLeave={() => setExportOpen(false)}
                >
                  <a
                    href={api.exportUrl(meeting.id, "md")}
                    className="block px-3 py-2 text-sm hover:bg-muted"
                  >
                    Markdown (.md)
                  </a>
                  <a
                    href={api.exportUrl(meeting.id, "txt")}
                    className="block px-3 py-2 text-sm hover:bg-muted"
                  >
                    Plain text (.txt)
                  </a>
                  <button
                    onClick={() => {
                      setExportOpen(false);
                      window.print();
                    }}
                    className="block w-full px-3 py-2 text-left text-sm hover:bg-muted"
                  >
                    Print / PDF
                  </button>
                </div>
              )}
            </div>
            <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
              <Pencil className="h-4 w-4" /> Edit
            </Button>
            <Button variant="ghost" size="icon" onClick={onDelete} aria-label="Delete meeting">
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>
          </div>
        </div>

        {/* Participants + tags */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {meeting.participants.map((p) => (
            <span key={p.id} className="flex items-center gap-1.5 rounded-full bg-muted py-0.5 pl-0.5 pr-2.5">
              <Avatar name={p.name} size={22} />
              <span className="text-xs font-medium">{p.name}</span>
            </span>
          ))}
          {meeting.tags.map((t) => (
            <Badge key={t.id}>{t.name}</Badge>
          ))}
        </div>
      </div>

      {/* Player */}
      <div className="no-print mb-4">
        <MediaPlayer
          audioUrl={meeting.audio_url}
          durationMs={durationMs}
          onPosition={setCurrentMs}
        />
      </div>

      {/* Main two-column layout */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        {/* Transcript */}
        <div className="lg:col-span-3">
          <div className="mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            <h2 className="font-semibold">Transcript</h2>
            <span className="text-xs text-muted-foreground">({meeting.segments.length} lines)</span>
          </div>
          <div className="h-[calc(100vh-320px)] min-h-[400px]">
            <TranscriptPanel
              segments={meeting.segments}
              speakers={meeting.speakers}
              currentMs={currentMs}
              onSeek={seekTo}
            />
          </div>
        </div>

        {/* Right panel */}
        <div className="lg:col-span-2">
          <div className="no-print mb-2 flex gap-1 rounded-lg bg-muted p-1">
            {TABS.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium transition-colors",
                    tab === t.id ? "bg-card shadow-sm" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  <Icon className="h-3.5 w-3.5" /> {t.label}
                </button>
              );
            })}
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            {tab === "summary" && <SummaryPanel meetingId={meeting.id} summary={meeting.summary} />}
            {tab === "actions" && <ActionItems meetingId={meeting.id} items={meeting.action_items} />}
            {tab === "topics" && <TopicsList topics={meeting.topics} onSeek={seekTo} />}
            {tab === "chat" && <ChatPanel meetingId={meeting.id} onSeek={seekTo} />}
          </div>
        </div>
      </div>

      <EditMeetingModal meeting={meeting} open={editOpen} onClose={() => setEditOpen(false)} />
    </div>
  );
}
