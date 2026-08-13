"use client";

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Spinner } from "@/components/ui/misc";
import type { MeetingDetail } from "@/lib/types";
import { useUpdateMeeting } from "@/lib/hooks";

export function EditMeetingModal({
  meeting,
  open,
  onClose,
}: {
  meeting: MeetingDetail;
  open: boolean;
  onClose: () => void;
}) {
  const update = useUpdateMeeting(meeting.id);
  const [title, setTitle] = React.useState(meeting.title);
  const [description, setDescription] = React.useState(meeting.description ?? "");
  const [participants, setParticipants] = React.useState(
    meeting.participants.map((p) => p.name).join(", "),
  );
  const [tags, setTags] = React.useState(meeting.tags.map((t) => t.name).join(", "));

  // Re-sync when a different meeting is opened.
  React.useEffect(() => {
    setTitle(meeting.title);
    setDescription(meeting.description ?? "");
    setParticipants(meeting.participants.map((p) => p.name).join(", "));
    setTags(meeting.tags.map((t) => t.name).join(", "));
  }, [meeting]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    update.mutate(
      {
        title: title.trim(),
        description: description.trim() || null,
        participants: participants.split(",").map((s) => s.trim()).filter(Boolean).map((name) => ({ name })),
        tags: tags.split(",").map((s) => s.trim()).filter(Boolean),
      },
      { onSuccess: onClose },
    );
  };

  return (
    <Dialog open={open} onClose={onClose} title="Edit meeting">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Title *</label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Participants</label>
          <Input
            value={participants}
            onChange={(e) => setParticipants(e.target.value)}
            placeholder="Comma-separated names"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Tags</label>
          <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="Comma-separated" />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={update.isPending || !title.trim()}>
            {update.isPending && <Spinner className="text-white" />}
            Save changes
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
