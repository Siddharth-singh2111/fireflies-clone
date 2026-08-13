"use client";

import * as React from "react";
import { Pause, Play, RotateCcw, RotateCw, Volume2 } from "lucide-react";
import { formatTimestamp } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface PlayerHandle {
  seek: (ms: number) => void;
  play: () => void;
  toggle: () => void;
}

interface MediaPlayerProps {
  audioUrl?: string | null;
  /** Timeline length in ms — taken from the transcript so the seek bar always
   *  matches the transcript timestamps, regardless of the sample audio length. */
  durationMs: number;
  onPosition: (ms: number) => void;
}

/**
 * The virtual clock (not the <audio> element) is the source of truth for the
 * playhead. That guarantees the transcript highlight always lines up with the
 * transcript's own timestamps, and that click-to-seek works even if the sample
 * audio fails to load (e.g. offline). The <audio> element is mirrored on a
 * best-effort basis so the user also hears sound.
 */
export const MediaPlayer = React.forwardRef<PlayerHandle, MediaPlayerProps>(
  ({ audioUrl, durationMs, onPosition }, ref) => {
    const audioRef = React.useRef<HTMLAudioElement | null>(null);
    const intervalRef = React.useRef<ReturnType<typeof setInterval> | null>(null);
    const lastTsRef = React.useRef<number>(0);
    const posRef = React.useRef<number>(0);

    const TICK_MS = 100;

    const [position, setPosition] = React.useState(0);
    const [playing, setPlaying] = React.useState(false);
    const [speed, setSpeed] = React.useState(1);
    // Mirror speed into a ref so the running interval reads the latest value
    // without needing to be torn down and recreated on every speed change.
    const speedRef = React.useRef(speed);
    React.useEffect(() => {
      speedRef.current = speed;
    }, [speed]);

    const total = Math.max(durationMs, 1000);

    const setPos = React.useCallback(
      (ms: number) => {
        const clamped = Math.min(Math.max(ms, 0), total);
        posRef.current = clamped;
        setPosition(clamped);
        onPosition(clamped);
      },
      [total, onPosition],
    );

    const stopLoop = () => {
      if (intervalRef.current != null) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };

    // A wall-clock-based interval (not requestAnimationFrame) so the playhead
    // keeps advancing even when the tab is backgrounded, and stays accurate
    // regardless of interval jitter by measuring real elapsed time each tick.
    const tick = React.useCallback(() => {
      const now = performance.now();
      const delta = (now - lastTsRef.current) * speedRef.current;
      lastTsRef.current = now;
      const next = posRef.current + delta;
      if (next >= total) {
        setPos(total);
        setPlaying(false);
        stopLoop();
        return;
      }
      setPos(next);
    }, [total, setPos]);

    const play = React.useCallback(() => {
      if (posRef.current >= total) setPos(0);
      setPlaying(true);
      lastTsRef.current = performance.now();
      stopLoop();
      intervalRef.current = setInterval(tick, TICK_MS);
      audioRef.current?.play().catch(() => {});
    }, [tick, total, setPos]);

    const pause = React.useCallback(() => {
      setPlaying(false);
      stopLoop();
      audioRef.current?.pause();
    }, []);

    const toggle = React.useCallback(() => {
      if (playing) pause();
      else play();
    }, [playing, play, pause]);

    const seek = React.useCallback(
      (ms: number) => {
        setPos(ms);
        if (audioRef.current) {
          try {
            audioRef.current.currentTime = ms / 1000;
          } catch {
            /* audio not ready */
          }
        }
      },
      [setPos],
    );

    React.useImperativeHandle(ref, () => ({ seek, play, toggle }), [seek, play, toggle]);

    React.useEffect(() => () => stopLoop(), []);

    React.useEffect(() => {
      if (audioRef.current) audioRef.current.playbackRate = speed;
    }, [speed]);

    return (
      <div className="rounded-lg border border-border bg-card p-4">
        {audioUrl && (
          // Hidden native element just for audio output; UI is fully custom.
          <audio ref={audioRef} src={audioUrl} preload="none" className="hidden" />
        )}

        <div className="flex items-center gap-3">
          <Button size="icon" onClick={toggle} aria-label={playing ? "Pause" : "Play"}>
            {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>

          <Button variant="ghost" size="icon" onClick={() => seek(position - 10000)} aria-label="Back 10s">
            <RotateCcw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => seek(position + 10000)} aria-label="Forward 10s">
            <RotateCw className="h-4 w-4" />
          </Button>

          <span className="ml-1 font-mono text-xs tabular-nums text-muted-foreground">
            {formatTimestamp(position)} / {formatTimestamp(total)}
          </span>

          <div className="ml-auto flex items-center gap-2">
            <Volume2 className="h-4 w-4 text-muted-foreground" />
            <select
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="h-7 rounded border border-input bg-background px-1 text-xs"
              aria-label="Playback speed"
            >
              {[0.5, 1, 1.25, 1.5, 2].map((s) => (
                <option key={s} value={s}>
                  {s}×
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Seek bar */}
        <input
          type="range"
          min={0}
          max={total}
          value={position}
          onChange={(e) => seek(Number(e.target.value))}
          className="mt-3 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary"
          aria-label="Seek"
          style={{
            background: `linear-gradient(to right, hsl(var(--primary)) ${(position / total) * 100}%, hsl(var(--muted)) ${(position / total) * 100}%)`,
          }}
        />
        {!audioUrl && (
          <p className="mt-2 text-[11px] text-muted-foreground">
            No media attached — the timeline is driven by the transcript for click-to-seek.
          </p>
        )}
      </div>
    );
  },
);
MediaPlayer.displayName = "MediaPlayer";
