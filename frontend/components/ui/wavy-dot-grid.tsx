"use client";

import { useEffect, useId, useState } from "react";

import { cn } from "@/lib/cn";

/** Soft dotted grid with SVG wave distortion — gentle, not aggressive. */
export function WavyDotGrid({ className }: { className?: string }) {
  const reactId = useId().replace(/:/g, "");
  const patternId = `learnlens-dots-${reactId}`;
  const filterId = `learnlens-wave-${reactId}`;
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduceMotion(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]",
        className,
      )}
    >
      <svg className="absolute inset-0 h-full w-full" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id={patternId} width="22" height="22" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="rgba(0,0,0,0.16)" />
          </pattern>

          <filter id={filterId} x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence
              type="turbulence"
              baseFrequency="0.015 0.025"
              numOctaves="2"
              seed="3"
              result="noise"
            >
              {!reduceMotion ? (
                <animate
                  attributeName="baseFrequency"
                  dur="8s"
                  values="0.015 0.025;0.028 0.016;0.018 0.03;0.015 0.025"
                  repeatCount="indefinite"
                />
              ) : null}
            </feTurbulence>
            <feDisplacementMap
              in="SourceGraphic"
              in2="noise"
              scale={reduceMotion ? "0" : "14"}
              xChannelSelector="R"
              yChannelSelector="G"
            />
          </filter>
        </defs>

        <rect
          width="100%"
          height="100%"
          fill={`url(#${patternId})`}
          filter={`url(#${filterId})`}
          opacity={reduceMotion ? 0.4 : 0.55}
        >
          {!reduceMotion ? (
            <animate
              attributeName="opacity"
              dur="10s"
              values="0.45;0.6;0.5;0.45"
              repeatCount="indefinite"
            />
          ) : null}
        </rect>
      </svg>
    </div>
  );
}
