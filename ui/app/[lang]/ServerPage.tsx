import React from 'react';

// This is a server component that doesn't have the params Promise issue
export default function ServerLangPage({
  lang,
}: {
  lang: string;
}) {
  return (
    <main>
      <h1>Welcome to KAI ({lang})</h1>
      <p>This is the {lang} landing page.</p>
    </main>
  );
} 