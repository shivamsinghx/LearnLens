/*
 * Opensource UI — https://opensourceui.in/
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
import { forwardRef, type HTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface DarkTealDepthBackgroundProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

const DarkTealDepthBackground = forwardRef<
  HTMLDivElement,
  DarkTealDepthBackgroundProps
>(({ children, className, ...props }, ref) => {
  return (
    <div
      ref={ref}
      data-slot="dark-teal-depth-background"
      className={cn("relative isolate overflow-hidden bg-[#061014]", className)}
      {...props}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(160deg,#0A1820_0%,#061014_45%,#030A0D_100%)]"
      />

      <div
        aria-hidden="true"
        className="pointer-events-none absolute -inset-8 -z-10 blur-3xl"
      >
        <div className="absolute top-[4%] -left-[10%] h-[66%] w-[66%] rounded-full bg-[#0D9488] opacity-22" />
        <div className="absolute top-[20%] -right-[12%] h-[58%] w-[58%] rounded-full bg-[#0891B2] opacity-18" />
        <div className="absolute bottom-[-20%] left-[20%] h-[62%] w-[62%] rounded-full bg-[#14B8A6] opacity-14" />
        <div className="absolute right-[6%] bottom-[2%] h-[48%] w-[48%] rounded-full bg-[#22D3EE] opacity-12" />
      </div>

      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 [background-image:radial-gradient(circle_at_80%_20%,rgba(45,212,191,0.08)_0%,transparent_42%)]"
      />

      {children}
    </div>
  );
});

DarkTealDepthBackground.displayName = "DarkTealDepthBackground";

export { DarkTealDepthBackground };

