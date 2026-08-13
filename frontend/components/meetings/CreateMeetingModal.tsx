"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { FileText, FileUp, FormInput } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Spinner } from "@/components/ui/misc";
import { cn } from "@/lib/utils";
import { useCreateMeeting, useUploadMeeting } from "@/lib/hooks";

type Mode = "paste" | "upload" | "form";

const TABS: { id: Mode; label: string; icon: React.ElementType }[] = [
  { id: "paste", label: "Paste transcript", icon: FileText },
  { id: "upload", label: "Upload file", icon: FileUp },
  { id: "form", label: "Blank meeting", icon: FormInput },
];

const SAMPLE = `[00:00:01] Alex: Welcome everyone, let's review the launch plan.
[00:00:07] Jordan: I'll finalize the landing page copy by Thursday.
[00:00:14] Alex: Great. We need to schedule the press outreach as well.
[00:00:20] Jordan: I can draft the press list and share it tomorrow.`;

function parseParticipants(raw: string) {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((name) => ({ name }));
}

function parseTags(raw: string) {
  return raw.split(",").map((s) => s.trim()).filter(Boolean);
}

export function CreateMeetingModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const create = useCreateMeeting();
  const upload = useUploadMeeting();

  const [mode, setMode] = React.useState<Mode>("paste");
  const [title, setTitle] = React.useState("");
  const [participants, setParticipants] = React.useState("");
  const [tags, setTags] = React.useState("");
  const [transcript, setTranscript] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);

  const busy = create.isPending || upload.isPending;

  const reset = () => {
    setTitle("");
    setParticipants("");
    setTags("");
    setTranscript("");
    setFile(null);
    setMode("paste");
  };

  const close = () => {
    if (!busy) {
      reset();
      onClose();
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      let created;
      if (mode === "upload") {
        if (!file) return;
        const form = new FormData();
        form.append("file", file);
        form.append("title", title.trim());
        if (participants.trim())
          form.append("participants", JSON.stringify(parseParticipants(participants)));
        if (tags.trim()) form.append("tags", tags.trim());
        created = await upload.mutateAsync(form);
      } else {
        created = await create.mutateAsync({
          title: title.trim(),
          participants: parseParticipants(participants),
          tags: parseTags(tags),
          transcript_text: mode === "paste" ? transcript : null,
          transcript_format: "auto",
          generate_summary: true,
        });
      }
      reset();
      onClose();
      router.push(`/meetings/${created.id}`);
    } catch {
      /* toast handled in hook */
    }
  };

  return (
    <Dialog open={open} onClose={close} title="New meeting" className="max-w-xl">
      <div className="mb-4 flex gap-1 rounded-lg bg-muted p-1">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setMode(t.id)}
              className={cn(
                "flex flex-1 items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium transition-colors",
                mode === t.id ? "bg-card shadow-sm" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className="h-3.5 w-3.5" /> {t.label}
            </button>
          );
        })}
      </div>

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Title *</label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Q3 Roadmap Planning"
            autoFocus
          />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">Participants</label>
            <Input
              value={participants}
              onChange={(e) => setParticipants(e.target.value)}
              placeholder="Priya, Daniel (comma-separated)"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Tags</label>
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Product, Planning"
            />
          </div>
        </div>

        {mode === "paste" && (
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="text-sm font-medium">Transcript</label>
              <button
                type="button"
                onClick={() => setTranscript(SAMPLE)}
                className="text-xs text-primary hover:underline"
              >
                Insert sample
              </button>
            </div>
            <Textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              rows={8}
              placeholder={"Speaker: text, one line each. Timestamps like [00:01:23] are optional.\nSupports plain text, WebVTT, or JSON."}
              className="font-mono text-xs"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              A summary, action items, and topics are generated automatically.
            </p>
          </div>
        )}

        {mode === "upload" && (
          <div>
            <label className="mb-1 block text-sm font-medium">Transcript file (.txt / .vtt / .json)</label>
            <input
              type="file"
              accept=".txt,.vtt,.json"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:opacity-90"
            />
            {file && <p className="mt-1 text-xs text-muted-foreground">{file.name}</p>}
          </div>
        )}

        {mode === "form" && (
          <p className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
            Creates an empty meeting. You can add a transcript and details later from the
            meeting page.
          </p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={close} disabled={busy}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={busy || !title.trim() || (mode === "upload" && !file) || (mode === "paste" && !transcript.trim())}
          >
            {busy && <Spinner className="text-white" />}
            Create meeting
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
