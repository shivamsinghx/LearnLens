"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from "react";

/**
 * Notion-style product pill — smooth width morph + color/text crossfade.
 */
const WORDS = [
  { label: "notes", background: "#E6F3FE", dot: "#097FE8" },
  { label: "PDFs", background: "#FDECC8", dot: "#D9730D" },
  { label: "lectures", background: "#EADBFA", dot: "#9849E8" },
  { label: "ideas", background: "#D0F4D8", dot: "#1AAE39" },
] as const;

const ROTATE_MS = 2800;
const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];
const DURATION = 0.55;

export function RotatingHeadline() {
  const [index, setIndex] = useState(0);
  const [widths, setWidths] = useState<number[]>([]);
  const [reduceMotion, setReduceMotion] = useState(false);
  const measureRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const word = WORDS[index];
  const labelWidth = widths[index];

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduceMotion(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useLayoutEffect(() => {
    const measure = () => {
      setWidths(
        WORDS.map((_, i) => {
          const el = measureRefs.current[i];
          return el ? Math.ceil(el.getBoundingClientRect().width) : 0;
        }),
      );
    };
    measure();
    void document.fonts?.ready.then(measure);
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  useEffect(() => {
    if (reduceMotion) return;
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % WORDS.length);
    }, ROTATE_MS);
    return () => window.clearInterval(timer);
  }, [reduceMotion]);

  const pillStyle = {
    background: word.background,
    "--color-dot": word.dot,
  } as CSSProperties;

  return (
    <p className="relative text-center text-[clamp(2rem,4.6vw,4.75rem)] leading-[1.02] font-semibold tracking-[-0.045em] text-black/95">
      <span
        aria-hidden
        className="pointer-events-none absolute top-0 left-0 -z-10 text-[0.75em] leading-[1.21] font-semibold tracking-[-0.0278em] opacity-0"
      >
        {WORDS.map((item, i) => (
          <span
            key={item.label}
            ref={(el) => {
              measureRefs.current[i] = el;
            }}
            className="absolute whitespace-nowrap"
          >
            {item.label}
          </span>
        ))}
      </span>

      <span className="block">Turn your</span>
      <span className="mt-[0.08em] flex flex-nowrap items-center justify-center gap-x-[0.22em] whitespace-nowrap">
        <motion.span
          aria-live="polite"
          className="notion-product-pill inline-flex items-baseline rounded-full text-[0.75em] leading-[1.21] font-semibold tracking-[-0.0278em]"
          style={pillStyle}
          animate={reduceMotion ? undefined : { backgroundColor: word.background }}
          transition={{ duration: DURATION, ease: EASE }}
        >
          <motion.span
            aria-hidden
            className="notion-product-pill__dot"
            animate={reduceMotion ? undefined : { backgroundColor: word.dot }}
            transition={{ duration: DURATION, ease: EASE }}
          />
          <motion.span
            className="notion-product-pill__label relative inline-block overflow-hidden whitespace-nowrap align-baseline"
            initial={false}
            animate={{
              width: labelWidth && labelWidth > 0 ? labelWidth : "auto",
            }}
            transition={reduceMotion ? { duration: 0 } : { duration: DURATION, ease: EASE }}
          >
            {/* Height lock so absolute text doesn't collapse the line */}
            <span className="invisible inline-block whitespace-nowrap" aria-hidden>
              {word.label}
            </span>
            <AnimatePresence initial={false}>
              <motion.span
                key={word.label}
                className="absolute top-0 left-0 inline-block whitespace-nowrap"
                initial={
                  reduceMotion ? false : { opacity: 0, y: "40%", filter: "blur(3px)" }
                }
                animate={{ opacity: 1, y: "0%", filter: "blur(0px)" }}
                exit={
                  reduceMotion
                    ? undefined
                    : { opacity: 0, y: "-35%", filter: "blur(3px)" }
                }
                transition={{ duration: DURATION, ease: EASE }}
              >
                {word.label}
              </motion.span>
            </AnimatePresence>
          </motion.span>
        </motion.span>
        <span>into knowledge.</span>
      </span>
    </p>
  );
}
