"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/misc";

interface Msg {
  role: "user" | "assistant";
  text: string;
  response?: ChatResponse;
}

const SUGGESTIONS = [
  "What were the key decisions?",
  "List the action items and owners.",
  "What risks or concerns were raised?",
];

export function ChatPanel({ meetingId, onSeek }: { meetingId: number; onSeek: (ms: number) => void }) {
  const [messages, setMessages] = React.useState<Msg[]>([]);
  const [input, setInput] = React.useState("");
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const ask = useMutation({
    mutationFn: (q: string) => api.askMeeting(meetingId, q),
    onSuccess: (res) =>
      setMessages((m) => [...m, { role: "assistant", text: res.answer, response: res }]),
    onError: () =>
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Sorry, I couldn't answer that. Please try again." },
      ]),
  });

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, ask.isPending]);

  const submit = (q: string) => {
    const question = q.trim();
    if (!question || ask.isPending) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    ask.mutate(question);
  };

  return (
    <div className="flex h-full min-h-[420px] flex-col">
      <div className="mb-2 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <h3 className="font-semibold">Ask about this meeting</h3>
      </div>

      <div ref={scrollRef} className="scroll-thin flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Ask a question and get an answer grounded in this transcript.
            </p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => submit(s)}
                className="block w-full rounded-md border border-border px-3 py-2 text-left text-sm hover:border-primary/40 hover:bg-muted"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-primary-foreground"
                  : "max-w-[90%] rounded-2xl rounded-bl-sm bg-muted px-3 py-2 text-sm"
              }
            >
              <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
              {m.response && m.response.sources.length > 0 && (
                <div className="mt-2 space-y-1 border-t border-border/60 pt-2">
                  <p className="text-[11px] font-medium text-muted-foreground">Sources</p>
                  {m.response.sources.map((s) => (
                    <button
                      key={s.segment_id}
                      onClick={() => onSeek(s.start_ms)}
                      className="block w-full truncate text-left text-[11px] text-primary hover:underline"
                    >
                      [{formatTimestamp(s.start_ms)}] {s.speaker ? `${s.speaker}: ` : ""}
                      {s.text}
                    </button>
                  ))}
                </div>
              )}
              {m.response && (
                <span className="mt-1 block text-[10px] uppercase tracking-wide text-muted-foreground">
                  {m.response.generated_by === "llm" ? "AI-generated" : "Extractive"}
                </span>
              )}
            </div>
          </div>
        ))}

        {ask.isPending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Spinner /> Thinking…
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
        className="mt-3 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="h-10 flex-1 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <Button type="submit" size="icon" disabled={!input.trim() || ask.isPending} aria-label="Send">
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
