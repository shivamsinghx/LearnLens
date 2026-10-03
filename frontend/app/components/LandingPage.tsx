"use client";

import FolderFloat from "@/components/FolderFloat";
import { TextMorph } from "@/components/forgeui/text-morph";
import { LineShadowText } from "@/components/ui/line-shadow-text";

import type { StudyDocument } from "@/app/lib/study-document";

import { QuickActions } from "./QuickActions";
import { RotatingHeadline } from "./RotatingHeadline";
import { StudyMaterials } from "./StudyMaterials";

const INTRO = [
  "LearnLens will help you understand the study material you upload. Later, questions and review stay tied to those documents.",
] as const;

const FOLDER_ITEMS = [
  "Ask a Question",
  "Summarize",
  "Generate Quiz",
  "Study Insights",
  "Learn",
  "Develop",
] as const;

/** Locked empty-state landing — keep visual structure identical to the pre-upload page. */
export function LandingPage({
  documents,
  processingLabel,
  onFilesChange,
  onProceed,
  onClearAll,
  onOpenDocument,
}: {
  documents: readonly StudyDocument[];
  processingLabel?: string | null;
  onFilesChange: (files: File[]) => void;
  onProceed: () => void;
  onClearAll: () => void;
  onOpenDocument?: (id: string) => void;
}) {
  return (
    <main id="content" className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 sm:px-6 lg:px-8">
      <section aria-labelledby="brand-heading" className="px-2 pt-16 pb-6 sm:pt-24">
        <h1 id="brand-heading" aria-label="LearnLens" className="brand-title text-center text-black/95">
          Learn
          <LineShadowText className="italic" shadowColor="black">
            Lens
          </LineShadowText>
        </h1>
        <div className="mt-8 sm:mt-10">
          <RotatingHeadline />
        </div>
        <p className="mx-auto mt-10 w-full overflow-x-auto text-center">
          <TextMorph
            words={INTRO}
            prefix=""
            singleLine
            className="font-sans text-[clamp(0.7rem,1.35vw,1.05rem)] font-medium tracking-[-0.03em] text-black/80"
          />
        </p>
        <div className="mt-36 flex items-end justify-center gap-28 sm:mt-44 sm:gap-36 md:gap-44">
          <div className="flex w-[200px] shrink-0 justify-center sm:w-[220px]">
            <FolderFloat
              items={[...FOLDER_ITEMS]}
              label=""
              sublabel=""
              trigger="hover-clickaway"
              closeOnSelect={false}
              closeOnLeave={false}
              physics
              drift={0.5}
              folderColor="#2f8df2"
              frontColor="#3aa2ff"
              paperColor="#ffffff"
              itemColor="#f5f5f5"
              itemTextColor="#18181b"
              labelColor="#ffffff"
              width={200}
              height={148}
              radius={14}
              spread={220}
              lift={34}
              tilt={8}
              flapAngle={34}
              restAngle={16}
              openDuration={520}
              stagger={45}
              bounce={0.3}
            />
          </div>

          <div
            className="flex w-[180px] shrink-0 items-end justify-center sm:w-[200px]"
            aria-hidden
          >
            <img
              src="/books.gif"
              alt=""
              width={200}
              height={160}
              draggable={false}
              className="block h-auto w-[150px] select-none sm:w-[170px]"
            />
          </div>
        </div>
      </section>

      <div className="mt-28 sm:mt-36">
        <StudyMaterials
          documents={documents}
          processingLabel={processingLabel}
          onFilesChange={onFilesChange}
          onProceed={onProceed}
          onClearAll={onClearAll}
          onOpenDocument={onOpenDocument}
        />
      </div>

      <div className="mt-14">
        <QuickActions />
      </div>
    </main>
  );
}
