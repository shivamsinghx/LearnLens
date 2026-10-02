"use client";

import { useLayoutEffect, useRef } from "react";

import { cn } from "@/lib/cn";

const SPACING = 22;
const RADIUS = 1.05;
const AMPLITUDE = 5.5;
const WAVE_LENGTH = 140;
const SPEED = 1.35;
const DOT_ALPHA = 0.14;

/** Soft dotted grid with a traveling sinusoidal wave. */
export function WavyDotGrid({ className }: { className?: string }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useLayoutEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let raf = 0;
    let cssW = 0;
    let cssH = 0;
    let dpr = 1;
    let alive = true;

    const resize = () => {
      const nextW = Math.max(1, Math.round(wrap.clientWidth || wrap.getBoundingClientRect().width || 1));
      const nextH = Math.max(1, Math.round(wrap.clientHeight || wrap.getBoundingClientRect().height || 1));
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      cssW = nextW;
      cssH = nextH;
      if (canvas.width !== Math.round(cssW * dpr)) canvas.width = Math.round(cssW * dpr);
      if (canvas.height !== Math.round(cssH * dpr)) canvas.height = Math.round(cssH * dpr);
      wrap.dataset.cw = String(cssW);
      wrap.dataset.ch = String(cssH);
    };

    const paint = (timeMs: number) => {
      if (!alive || cssW < 2 || cssH < 2) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, cssW, cssH);
      ctx.fillStyle = `rgba(0, 0, 0, ${DOT_ALPHA})`;

      const t = reduceMotion.matches ? 0 : (timeMs / 1000) * SPEED;
      const cols = Math.ceil(cssW / SPACING) + 2;
      const rows = Math.ceil(cssH / SPACING) + 2;

      for (let row = 0; row < rows; row += 1) {
        for (let col = 0; col < cols; col += 1) {
          const x = col * SPACING + 2;
          const baseY = row * SPACING + 2;
          const y =
            baseY +
            Math.sin((x / WAVE_LENGTH) * Math.PI * 2 + t) * AMPLITUDE +
            Math.sin(row * 0.45 + t * 0.65) * (AMPLITUDE * 0.25);
          ctx.beginPath();
          ctx.arc(x, y, RADIUS, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    };

    const tick = (now: number) => {
      paint(now);
      if (alive && !reduceMotion.matches) raf = requestAnimationFrame(tick);
    };

    const kick = () => {
      resize();
      paint(performance.now());
      cancelAnimationFrame(raf);
      if (!reduceMotion.matches) raf = requestAnimationFrame(tick);
    };

    kick();
    const boot = window.setTimeout(kick, 80);
    const observer = new ResizeObserver(kick);
    observer.observe(wrap);
    reduceMotion.addEventListener("change", kick);

    return () => {
      alive = false;
      window.clearTimeout(boot);
      cancelAnimationFrame(raf);
      observer.disconnect();
      reduceMotion.removeEventListener("change", kick);
    };
  }, []);

  return (
    <div
      ref={wrapRef}
      aria-hidden
      data-wavy="sine"
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]",
        className,
      )}
    >
      <canvas ref={canvasRef} className="absolute inset-0 block h-full w-full" data-wavy-canvas="1" />
    </div>
  );
}
