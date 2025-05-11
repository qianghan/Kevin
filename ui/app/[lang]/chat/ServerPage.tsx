import React from 'react';

// This is a server component that doesn't have the params Promise issue
export default function ServerChatPage({
  lang,
}: {
  lang: string;
}) {
  return (
    <main>
      <h1>Chat Page ({lang})</h1>
      <p>This is the chat page for language: {lang}.</p>
    </main>
  );
} 