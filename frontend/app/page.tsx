import FolderFloat from "@/components/FolderFloat";
import { TextMorph } from "@/components/forgeui/text-morph";
import { LineShadowText } from "@/components/ui/line-shadow-text";

import { QuickActions } from "./components/QuickActions";
import { RotatingHeadline } from "./components/RotatingHeadline";
import { StudyMaterials } from "./components/StudyMaterials";

const INTRO = [
  "LearnLens will help you understand the study material you upload. Later, questions and review stay tied to those documents.",
] as const;

const FOLDER_ITEMS = ["Ask a Question", "Summarize", "Generate Quiz", "Study Insights"] as const;

export default function Home() {
  return (
    <main id="content" className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 sm:px-6 lg:px-8">
      <section aria-labelledby="brand-heading" className="px-2 pt-16 pb-6 sm:pt-24">
        <h1 id="brand-heading" aria-label="LearnLens" className="brand-title text-center text-black/95">
          Learn<LineShadowText className="italic" shadowColor="black">
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
        <div className="mt-28 flex justify-center sm:mt-36">
          <FolderFloat
            items={[...FOLDER_ITEMS]}
            label=""
            sublabel=""
            animateOnMount
            trigger="hover"
            closeOnSelect
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
            spread={180}
            lift={26}
            tilt={8}
            flapAngle={34}
            restAngle={16}
            openDuration={520}
            stagger={45}
            bounce={0.3}
          />
        </div>
      </section>

      <div className="mt-28 sm:mt-36">
        <StudyMaterials />
      </div>

      <div className="mt-14">
        <QuickActions />
      </div>
    </main>
  );
}
