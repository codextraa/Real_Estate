"use client";

import GlobalErrorModal from "@/components/modals/GlobalErrorModal"; 

export default function Error({ error, reset }) {
  return (
    <GlobalErrorModal error={error} reset={reset} />
  );
}
