"use client";

import { useState } from "react";
import { motion } from "motion/react";

import { cn } from "@/lib/cn";

type AnimatedTabsProps = {
  tabs?: string[];
  variant?: "default" | "underline";
  value?: string;
  onValueChange?: (tab: string) => void;
  className?: string;
};

const defaultTabs = ["Home", "Components", "Docs", "Templates"];

const AnimatedTabs = ({
  tabs = defaultTabs,
  variant = "default",
  value,
  onValueChange,
  className,
}: AnimatedTabsProps) => {
  const [uncontrolledTab, setUncontrolledTab] = useState(tabs[0]);
  const activeTab = value ?? uncontrolledTab;

  const selectTab = (tab: string) => {
    if (value === undefined) setUncontrolledTab(tab);
    onValueChange?.(tab);
  };

  if (variant === "underline") {
    return (
      <div className={cn("border-border relative flex items-center border-b", className)}>
        {tabs.map((tab, index) => {
          const isActive = activeTab === tab;

          return (
            <button
              key={index}
              type="button"
              onClick={() => selectTab(tab)}
              className={cn(
                "relative flex h-10 items-center px-4 text-sm font-medium transition-colors duration-200",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="active-tab-underline"
                  className="bg-primary absolute right-0 bottom-0 left-0 h-0.5"
                  initial={false}
                  transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 30,
                  }}
                />
              )}
              <span className="relative z-10">{tab}</span>
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative mx-auto flex w-fit max-w-full flex-wrap items-center justify-center rounded-full border border-neutral-200 bg-neutral-50 p-1",
        className,
      )}
    >
      {tabs.map((tab, index) => {
        const isActive = activeTab === tab;

        return (
          <button
            key={index}
            type="button"
            onClick={() => selectTab(tab)}
            className={cn(
              "relative flex h-8 items-center rounded-full px-3 text-sm font-medium transition-colors duration-200 sm:h-9 sm:px-4",
              isActive
                ? "text-primary-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {isActive && (
              <motion.div
                layoutId="active-tab-background"
                className="bg-primary absolute inset-0 rounded-full"
                initial={false}
                transition={{
                  type: "spring",
                  stiffness: 500,
                  damping: 30,
                }}
              />
            )}
            <span className="relative z-10 whitespace-nowrap">{tab}</span>
          </button>
        );
      })}
    </div>
  );
};

export default AnimatedTabs;
