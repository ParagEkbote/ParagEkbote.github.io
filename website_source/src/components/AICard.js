export default function AIPageActions({ title, context }) {
  const baseQuery = `
You are an expert AI/ML engineer analyzing the following page.

PAGE TITLE:
${title}

CONTENT:
${context}

Instructions:
- Summarize key ideas
- Identify strengths
- Suggest improvements
- Highlight technical depth
`;

  const openAI = (url) => {
    window.open(url, '_blank');
  };

  return (
    <div
      style={{
        marginTop: '1.5rem',
        marginBottom: '2rem',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '10px'
      }}
    >
      {/* Claude */}
      <button
        onClick={() =>
          openAI(`https://claude.ai/new?q=${encodeURIComponent(baseQuery)}`)
        }
        style={btnStyle('#f4a261')}
      >
        🤖 Ask Claude
      </button>

      {/* ChatGPT */}
      <button
        onClick={() =>
          openAI(`https://chatgpt.com/?q=${encodeURIComponent(baseQuery)}`)
        }
        style={btnStyle('#10a37f')}
      >
        🤖 Ask ChatGPT
      </button>

      {/* HuggingChat */}
      <button
        onClick={() =>
          openAI(`https://huggingface.co/chat?q=${encodeURIComponent(baseQuery)}`)
        }
        style={btnStyle('#ff9d00')}
      >
        🤗 Ask HuggingChat
      </button>
    </div>
  );
}

function btnStyle(color) {
  return {
    background: color,
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    padding: '8px 14px',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer'
  };
}