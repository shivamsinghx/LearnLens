"use client";

import { useEffect, useState } from "react";

const WORDS = [
  { label: "notes", background: "#E6F3FE", dot: "#2383E2" },
  { label: "PDFs", background: "#FDECC8", dot: "#D9730D" },
  { label: "lectures", background: "#E8DEEE", dot: "#9065B0" },
  { label: "ideas", background: "#D0F4D8", dot: "#1AAE39" },
] as const;

const ROTATE_MS = 2400;

export function RotatingHeadline() {
  const [index, setIndex] = useState(0);
  const word = WORDS[index];

  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (motion.matches) return;

    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % WORDS.length);
    }, ROTATE_MS);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <p className="relative text-center text-[clamp(2rem,4.6vw,4.75rem)] leading-[1.02] font-semibold tracking-[-0.045em] text-black/95">
      <span className="block">Turn your</span>
      <span className="mt-[0.08em] flex flex-nowrap items-center justify-center gap-x-[0.22em] whitespace-nowrap">
        <span
          className="inline-flex items-center justify-center gap-[0.2em] rounded-full py-[0.12em] pr-[0.5em] pl-[0.4em] transition-colors duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none"
          style={{ backgroundColor: word.background }}
        >
          <span
            aria-hidden="true"
            className="size-[0.22em] shrink-0 rounded-full transition-colors duration-500 motion-reduce:transition-none"
            style={{ backgroundColor: word.dot }}
          />
          <span className="inline-grid items-center text-[0.78em] leading-none font-medium tracking-[-0.03em]">
            <span aria-hidden="true" className="invisible col-start-1 row-start-1 px-[0.08em] whitespace-nowrap">
              {word.label}
            </span>
            <span
              key={word.label}
              aria-live="polite"
              className="word-in col-start-1 row-start-1 px-[0.08em] whitespace-nowrap"
            >
              {word.label}
            </span>
          </span>
        </span>
        <span>into knowledge.</span>
      </span>
    </p>
  );
}
