// Mirror of the backend Pydantic schemas — the shared API contract.

export interface User {
  id: number;
  name: string;
  email: string;
  avatar_url?: string | null;
}

export interface Participant {
  id: number;
  name: string;
  email?: string | null;
}

export interface Speaker {
  id: number;
  label: string;
  display_name: string;
  color?: string | null;
}

export interface Segment {
  id: number;
  seq: number;
  start_ms: number;
  end_ms: number;
  text: string;
  speaker_id?: number | null;
}

export interface Summary {
  id: number;
  overview: string;
  keywords?: string | null;
  sentiment?: string | null;
  generated_by: string;
}

export interface ActionItem {
  id: number;
  text: string;
  assignee?: string | null;
  is_completed: boolean;
  due_date?: string | null;
}

export interface Topic {
  id: number;
  seq: number;
  title: string;
  start_ms: number;
}

export interface Tag {
  id: number;
  name: string;
}

export interface MeetingListItem {
  id: number;
  title: string;
  meeting_date: string;
  duration_sec: number;
  status: string;
  participants: Participant[];
  tags: Tag[];
  action_item_count: number;
  segment_count: number;
}

export interface MeetingDetail {
  id: number;
  title: string;
  description?: string | null;
  meeting_date: string;
  duration_sec: number;
  audio_url?: string | null;
  status: string;
  participants: Participant[];
  speakers: Speaker[];
  segments: Segment[];
  summary?: Summary | null;
  action_items: ActionItem[];
  topics: Topic[];
  tags: Tag[];
}

export interface PaginatedMeetings {
  items: MeetingListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchHit {
  meeting_id: number;
  meeting_title: string;
  segment_id: number;
  start_ms: number;
  snippet: string;
  speaker?: string | null;
}

export interface GlobalSearchResult {
  query: string;
  hits: SearchHit[];
  total: number;
}

export interface ChatSource {
  segment_id: number;
  start_ms: number;
  text: string;
  speaker?: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  generated_by: string;
}

export type SortOption = "recent" | "oldest" | "title" | "duration";

export interface MeetingFilters {
  q?: string;
  participant?: string;
  tag?: string;
  sort?: SortOption;
  page?: number;
  page_size?: number;
}
