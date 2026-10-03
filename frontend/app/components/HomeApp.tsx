"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  createStudyDocument,
  revokeStudyDocument,
  type StudyDocument,
} from "@/app/lib/study-document";

import { DocumentWorkspace } from "./DocumentWorkspace";
import { LandingPage } from "./LandingPage";

const PROCESSING_STEPS = [
  "Uploading...",
  "Reading document...",
  "Preparing your study material...",
] as const;

function wait(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export function HomeApp() {
  const [documents, setDocuments] = useState<readonly StudyDocument[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [processingLabel, setProcessingLabel] = useState<string | null>(null);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const pendingFilesRef = useRef<File[]>([]);
  const documentsRef = useRef(documents);
  documentsRef.current = documents;

  useEffect(() => {
    return () => {
      for (const doc of documentsRef.current) revokeStudyDocument(doc);
    };
  }, []);

  const replaceDocuments = useCallback((next: readonly StudyDocument[]) => {
    setDocuments((prev) => {
      const keep = new Set(next.map((doc) => doc.objectUrl));
      for (const doc of prev) {
        if (!keep.has(doc.objectUrl)) revokeStudyDocument(doc);
      }
      return next;
    });
  }, []);

  const handleFilesChange = useCallback(
    (files: File[]) => {
      pendingFilesRef.current = files;
      // Preview in Your Documents without opening the workspace yet.
      const next = files.map(createStudyDocument);
      replaceDocuments(next);
      setActiveDocumentId(next[0]?.id ?? null);
      setWorkspaceOpen(false);
    },
    [replaceDocuments],
  );

  const handleProceed = useCallback(async () => {
    if (pendingFilesRef.current.length === 0 && documents.length === 0) return;

    for (const step of PROCESSING_STEPS) {
      setProcessingLabel(step);
      await wait(650);
    }

    // Ensure docs exist from pending files if list was cleared somehow.
    if (documents.length === 0 && pendingFilesRef.current.length > 0) {
      const next = pendingFilesRef.current.map(createStudyDocument);
      replaceDocuments(next);
      setActiveDocumentId(next[0]?.id ?? null);
    }

    setProcessingLabel(null);
    setWorkspaceOpen(true);
  }, [documents.length, replaceDocuments]);

  const handleClearAll = useCallback(() => {
    pendingFilesRef.current = [];
    replaceDocuments([]);
    setActiveDocumentId(null);
    setProcessingLabel(null);
    setWorkspaceOpen(false);
  }, [replaceDocuments]);

  const handleAddFiles = useCallback(
    (files: File[]) => {
      if (files.length === 0) return;
      const incoming = files.map(createStudyDocument);
      setDocuments((prev) => {
        const byId = new Map(prev.map((doc) => [doc.id, doc]));
        for (const doc of incoming) {
          const existing = byId.get(doc.id);
          if (existing) revokeStudyDocument(doc);
          else byId.set(doc.id, doc);
        }
        return Array.from(byId.values());
      });
      setActiveDocumentId((current) => current ?? incoming[0]?.id ?? null);
    },
    [],
  );

  if (workspaceOpen && documents.length > 0 && processingLabel == null) {
    return (
      <DocumentWorkspace
        documents={documents}
        activeDocumentId={activeDocumentId}
        onSelectDocument={setActiveDocumentId}
        onAddFiles={handleAddFiles}
        onGoHome={() => setWorkspaceOpen(false)}
      />
    );
  }

  return (
    <LandingPage
      documents={documents}
      processingLabel={processingLabel}
      onFilesChange={handleFilesChange}
      onProceed={() => {
        void handleProceed();
      }}
      onClearAll={handleClearAll}
      onOpenDocument={(id) => {
        setActiveDocumentId(id);
        setWorkspaceOpen(true);
      }}
    />
  );
}
