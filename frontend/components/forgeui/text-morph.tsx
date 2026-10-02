"use client";

import { type ReactNode, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

import { cn } from "@/lib/cn";

type TextMorphProps = {
  words?: readonly string[];
  interval?: number;
  className?: string;
  charClassName?: string;
  prefix?: ReactNode;
  singleLine?: boolean;
};

const defaultWords = ["engineer", "designer"];

export function TextMorph({
  words = defaultWords,
  interval = 2500,
  className,
  charClassName,
  prefix = "20 •",
  singleLine = false,
}: TextMorphProps) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (words.length < 2) return;

    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % words.length);
    }, interval);

    return () => clearInterval(timer);
  }, [words, interval]);

  const tokens = useMemo(() => {
    const text = words[index] ?? "";
    return Array.from(text.matchAll(/\S+/g), (match) => ({
      word: match[0],
      start: match.index ?? 0,
    }));
  }, [index, words]);

  if (!words.length) return null;

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center",
        singleLine ? "w-max max-w-full" : "w-full",
        className,
      )}
    >
      {prefix !== null && prefix !== undefined && prefix !== "" ? <span>{prefix}</span> : null}
      <AnimatePresence mode="popLayout">
        <motion.span
          key={index}
          className={cn(
            "flex justify-center gap-x-[0.38em] py-1",
            singleLine ? "w-max flex-nowrap whitespace-nowrap" : "w-full flex-wrap gap-y-[0.85em]",
          )}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
          transition={{ duration: 0.22 }}
        >
          {tokens.map((token) => (
            <span key={`${index}-${token.start}`} className="inline-flex flex-nowrap">
              {Array.from(token.word).map((char, offset) => {
                const charIndex = token.start + offset;
                return (
                  <motion.span
                    key={`${index}-${charIndex}`}
                    className={charClassName}
                    initial={{ opacity: 0, y: 4, filter: "blur(4px)" }}
                    animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                    exit={{ opacity: 0, y: -4, filter: "blur(4px)" }}
                    transition={{
                      delay: charIndex * 0.008,
                      duration: 0.16,
                    }}
                  >
                    {char}
                  </motion.span>
                );
              })}
            </span>
          ))}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

export default TextMorph;
