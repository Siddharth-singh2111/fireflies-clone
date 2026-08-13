"use client";

// React Query hooks: one hook per server interaction. Mutations invalidate the
// relevant queries so the UI stays consistent without manual cache juggling.

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { toast } from "sonner";

import { api, ApiError } from "./api";
import type { MeetingFilters } from "./types";

export const keys = {
  me: ["me"] as const,
  tags: ["tags"] as const,
  meetings: (f: MeetingFilters) => ["meetings", f] as const,
  meeting: (id: number) => ["meeting", id] as const,
  search: (q: string) => ["search", q] as const,
};

function errMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  return "Something went wrong";
}

export function useMe() {
  return useQuery({ queryKey: keys.me, queryFn: api.getMe });
}

export function useTags() {
  return useQuery({ queryKey: keys.tags, queryFn: api.getTags });
}

export function useMeetings(filters: MeetingFilters) {
  return useQuery({
    queryKey: keys.meetings(filters),
    queryFn: () => api.listMeetings(filters),
  });
}

export function useMeeting(id: number) {
  return useQuery({
    queryKey: keys.meeting(id),
    queryFn: () => api.getMeeting(id),
    enabled: Number.isFinite(id) && id > 0,
  });
}

export function useCreateMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => api.createMeeting(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meetings"] });
      toast.success("Meeting created");
    },
    onError: (e) => toast.error(errMessage(e)),
  });
}

export function useUploadMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) => api.uploadMeeting(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meetings"] });
      toast.success("Transcript uploaded");
    },
    onError: (e) => toast.error(errMessage(e)),
  });
}

export function useUpdateMeeting(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => api.updateMeeting(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.meeting(id) });
      qc.invalidateQueries({ queryKey: ["meetings"] });
      toast.success("Meeting updated");
    },
    onError: (e) => toast.error(errMessage(e)),
  });
}

export function useDeleteMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteMeeting(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meetings"] });
      toast.success("Meeting deleted");
    },
    onError: (e) => toast.error(errMessage(e)),
  });
}

export function useRegenerateSummary(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.regenerateSummary(id),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: keys.meeting(id) });
      toast.success(
        data.generated_by === "llm" ? "Summary regenerated with AI" : "Summary regenerated",
      );
    },
    onError: (e) => toast.error(errMessage(e)),
  });
}

export function useActionItemMutations(meetingId: number) {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: keys.meeting(meetingId) });

  const create = useMutation({
    mutationFn: (body: unknown) => api.createActionItem(meetingId, body),
    onSuccess: () => {
      invalidate();
      toast.success("Action item added");
    },
    onError: (e) => toast.error(errMessage(e)),
  });

  const update = useMutation({
    mutationFn: ({ itemId, body }: { itemId: number; body: unknown }) =>
      api.updateActionItem(meetingId, itemId, body),
    onSuccess: () => invalidate(),
    onError: (e) => toast.error(errMessage(e)),
  });

  const remove = useMutation({
    mutationFn: (itemId: number) => api.deleteActionItem(meetingId, itemId),
    onSuccess: () => {
      invalidate();
      toast.success("Action item removed");
    },
    onError: (e) => toast.error(errMessage(e)),
  });

  return { create, update, remove };
}

export function useRenameSpeaker(meetingId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ speakerId, name }: { speakerId: number; name: string }) =>
      api.renameSpeaker(meetingId, speakerId, name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.meeting(meetingId) });
      toast.success("Speaker renamed");
    },
    onError: (e) => toast.error(errMessage(e)),
  });
}
