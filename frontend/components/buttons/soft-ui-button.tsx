/*
 * Opensource UI — https://opensourceui.in/components/soft-ui-button
 * Copyright (c) 2026 Bidyut Kundu
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
"use client";

import {
  forwardRef,
  type ComponentPropsWithoutRef,
  type ReactNode,
} from "react";

import { cn } from "@/lib/cn";

export type SoftUiButtonSize = "sm" | "md" | "lg";
export type SoftUiButtonTone = "neutral" | "green" | "blue";

export type SoftUiButtonProps = Readonly<
  {
    children: ReactNode;
    size?: SoftUiButtonSize;
    tone?: SoftUiButtonTone;
  } & ComponentPropsWithoutRef<"button">
>;

const SIZE: Record<SoftUiButtonSize, string> = {
  sm: "h-9 gap-1.5 rounded-xl px-3.5 text-xs",
  md: "h-10 gap-2 rounded-xl px-4 text-sm",
  lg: "h-12 gap-2 rounded-2xl px-5 text-sm",
};

const TONE: Record<SoftUiButtonTone, string> = {
  neutral: "bg-neutral-100 text-neutral-800 hover:text-neutral-900",
  green:
    "bg-[#e7f6ec] text-[#1f6b3a] hover:bg-[#dcf3e4] hover:text-[#185730]",
  blue: "bg-[#e8f3fc] text-[#1a5f9a] hover:bg-[#dceefb] hover:text-[#154e80]",
};

// Soft UI / neumorphic — even light + dark shadows, no hard bevel rim.
// SoftUiButton — universal soft-UI button; pass any children.
export const SoftUiButton = forwardRef<HTMLButtonElement, SoftUiButtonProps>(
  (
    {
      className,
      children,
      size = "md",
      tone = "neutral",
      type = "button",
      disabled,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled}
        data-slot="soft-ui-button"
        data-size={size}
        data-tone={tone}
        className={cn(
          "inline-flex cursor-pointer items-center justify-center font-sans font-semibold outline-none select-none",
          "shadow-[6px_6px_14px_rgba(0,0,0,0.08),-6px_-6px_14px_rgba(255,255,255,0.9)]",
          "transition-[box-shadow,background-color,color] duration-200 ease-[cubic-bezier(0.32,0.72,0,1)] motion-reduce:transition-none",
          "active:shadow-[inset_4px_4px_10px_rgba(0,0,0,0.08),inset_-4px_-4px_10px_rgba(255,255,255,0.85)]",
          "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-neutral-900",
          "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-40",
          TONE[tone],
          SIZE[size],
          className,
        )}
        {...props}
      >
        {children}
      </button>
    );
  },
);

SoftUiButton.displayName = "SoftUiButton";
