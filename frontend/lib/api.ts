// Thin typed fetch wrapper around the backend. One place owns the base URL,
// error shaping, and JSON handling, so components never touch fetch directly.

import type {
  ActionItem,
  ChatResponse,
  GlobalSearchResult,
  MeetingDetail,
  MeetingFilters,
  PaginatedMeetings,
  Speaker,
  Summary,
  Tag,
  User,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function toQuery(params: Record<string, unknown>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

export const api = {
  baseUrl: BASE_URL,

  getMe: () => request<User>("/api/me"),
  getTags: () => request<Tag[]>("/api/tags"),

  listMeetings: (filters: MeetingFilters = {}) =>
    request<PaginatedMeetings>(`/api/meetings${toQuery(filters as Record<string, unknown>)}`),

  getMeeting: (id: number) => request<MeetingDetail>(`/api/meetings/${id}`),

  createMeeting: (body: unknown) =>
    request<MeetingDetail>("/api/meetings", { method: "POST", body: JSON.stringify(body) }),

  uploadMeeting: (form: FormData) =>
    request<MeetingDetail>("/api/meetings/upload", { method: "POST", body: form }),

  updateMeeting: (id: number, body: unknown) =>
    request<MeetingDetail>(`/api/meetings/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  deleteMeeting: (id: number) =>
    request<void>(`/api/meetings/${id}`, { method: "DELETE" }),

  regenerateSummary: (id: number) =>
    request<Summary>(`/api/meetings/${id}/regenerate-summary`, { method: "POST" }),

  createActionItem: (meetingId: number, body: unknown) =>
    request<ActionItem>(`/api/meetings/${meetingId}/action-items`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateActionItem: (meetingId: number, itemId: number, body: unknown) =>
    request<ActionItem>(`/api/meetings/${meetingId}/action-items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteActionItem: (meetingId: number, itemId: number) =>
    request<void>(`/api/meetings/${meetingId}/action-items/${itemId}`, { method: "DELETE" }),

  renameSpeaker: (meetingId: number, speakerId: number, display_name: string) =>
    request<Speaker>(`/api/meetings/${meetingId}/speakers/${speakerId}`, {
      method: "PATCH",
      body: JSON.stringify({ display_name }),
    }),

  globalSearch: (q: string) =>
    request<GlobalSearchResult>(`/api/search${toQuery({ q })}`),

  askMeeting: (meetingId: number, question: string) =>
    request<ChatResponse>(`/api/meetings/${meetingId}/chat`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  exportUrl: (meetingId: number, format: "md" | "txt") =>
    `${BASE_URL}/api/meetings/${meetingId}/export?format=${format}`,
};
