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

export interface FrostMeshBackgroundProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

const FrostMeshBackground = forwardRef<
  HTMLDivElement,
  FrostMeshBackgroundProps
>(({ children, className, ...props }, ref) => {
  return (
    <div
      ref={ref}
      data-slot="frost-mesh-background"
      className={cn("relative isolate overflow-hidden bg-[#FAFCFD]", className)}
      {...props}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(135deg,#FAFCFD_0%,#F2F8FA_50%,#EAF4F6_100%)]"
      />

      <div
        aria-hidden="true"
        className="pointer-events-none absolute -inset-8 -z-10 blur-2xl"
      >
        <div className="absolute -top-[18%] -left-[12%] h-[52%] w-[52%] rounded-full bg-[#A5F3FC] opacity-35" />
        <div className="absolute top-[10%] -right-[14%] h-[48%] w-[48%] rounded-full bg-[#6EE7B7] opacity-28" />
        <div className="absolute -bottom-[20%] left-[24%] h-[46%] w-[46%] rounded-full bg-[#99F6E4] opacity-22" />
      </div>

      {children}
    </div>
  );
});

FrostMeshBackground.displayName = "FrostMeshBackground";

export { FrostMeshBackground };

