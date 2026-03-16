import React from 'react';
import VerseBlock from './VerseBlock';

const PARASHOT = [
  { name: 'Bereshit', he: '\u05D1\u05B0\u05BC\u05E8\u05B5\u05D0\u05E9\u05C1\u05B4\u05D9\u05EA', start: [1,1], end: [6,8] },
  { name: 'Noach', he: '\u05E0\u05B9\u05D7\u05B7', start: [6,9], end: [11,32] },
  { name: 'Lech Lecha', he: '\u05DC\u05B6\u05DA\u05BE\u05DC\u05B0\u05DA\u05B8', start: [12,1], end: [17,27] },
  { name: 'Vayera', he: '\u05D5\u05B7\u05D9\u05B5\u05BC\u05E8\u05B8\u05D0', start: [18,1], end: [22,24] },
  { name: 'Chayei Sarah', he: '\u05D7\u05B7\u05D9\u05B5\u05BC\u05D9 \u05E9\u05B8\u05C2\u05E8\u05B8\u05D4', start: [23,1], end: [25,18] },
  { name: 'Toldot', he: '\u05EA\u05BC\u05D5\u05B9\u05DC\u05B0\u05D3\u05B9\u05EA', start: [25,19], end: [28,9] },
  { name: 'Vayetze', he: '\u05D5\u05B7\u05D9\u05B5\u05BC\u05E6\u05B5\u05D0', start: [28,10], end: [32,3] },
  { name: 'Vayishlach', he: '\u05D5\u05B7\u05D9\u05B4\u05E9\u05C1\u05B0\u05DC\u05B7\u05D7', start: [32,4], end: [36,43] },
  { name: 'Vayeshev', he: '\u05D5\u05B7\u05D9\u05B5\u05BC\u05E9\u05C1\u05B6\u05D1', start: [37,1], end: [40,23] },
  { name: 'Miketz', he: '\u05DE\u05B4\u05E7\u05B5\u05BC\u05E5', start: [41,1], end: [44,17] },
  { name: 'Vayigash', he: '\u05D5\u05B7\u05D9\u05B4\u05BC\u05D2\u05B7\u05BC\u05E9\u05C1', start: [44,18], end: [47,27] },
  { name: 'Vayechi', he: '\u05D5\u05B7\u05D9\u05B0\u05D7\u05B4\u05D9', start: [47,28], end: [50,26] },
];

function getParasha(chapter) {
  for (const p of PARASHOT) {
    if (chapter >= p.start[0] && chapter <= p.end[0]) return p;
  }
  return PARASHOT[0];
}

const styles = {
  container: {
    maxWidth: 960,
    margin: '0 auto',
    padding: '24px 16px',
  },
  chapterHeader: {
    textAlign: 'center',
    marginBottom: 24,
  },
  heBookName: {
    fontFamily: "'SBL Hebrew', 'Noto Serif Hebrew', serif",
    fontSize: 28,
    color: 'var(--ink)',
    direction: 'rtl',
    display: 'block',
    marginBottom: 4,
  },
  chapterTitle: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 22,
    color: 'var(--ink-light)',
    fontWeight: 600,
  },
  parashaLabel: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 15,
    color: 'var(--accent-gold)',
    fontStyle: 'italic',
    display: 'block',
    marginBottom: 2,
  },
  parashaHe: {
    fontFamily: "'SBL Hebrew', 'Noto Serif Hebrew', serif",
    fontSize: 14,
    color: 'var(--accent-gold)',
    direction: 'rtl',
    marginLeft: 8,
  },
  chapterNav: {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 4,
    marginBottom: 32,
    padding: '12px 0',
    borderBottom: '1px solid var(--divider)',
    borderTop: '1px solid var(--divider)',
  },
  chapterBtn: {
    width: 36,
    height: 36,
    border: '1px solid var(--card-border)',
    borderRadius: 6,
    background: 'var(--card-bg)',
    color: 'var(--ink)',
    fontFamily: "'EB Garamond', serif",
    fontSize: 14,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.15s',
  },
  chapterBtnActive: {
    background: 'var(--ink)',
    color: 'var(--parchment)',
    borderColor: 'var(--ink)',
    fontWeight: 700,
  },
};

export default function ChapterView({ data, chapter, onChapterChange }) {
  const totalChapters = data.chapters.length;
  const chapterData = data.chapters.find(c => c.chapter === chapter);
  const parasha = getParasha(chapter);

  if (!chapterData) {
    return <div style={styles.container}>Chapter not found.</div>;
  }

  return (
    <div style={styles.container}>
      {/* Chapter header */}
      <div style={styles.chapterHeader}>
        <span style={styles.parashaLabel}>
          Parashat {parasha.name}
          <span style={styles.parashaHe}>{parasha.he}</span>
        </span>
        <span style={styles.heBookName}>{data.he_name}</span>
        <h1 style={styles.chapterTitle}>
          Bereshit &middot; Genesis Chapter {chapter}
        </h1>
      </div>

      {/* Chapter navigation */}
      <div style={styles.chapterNav}>
        {Array.from({ length: totalChapters }, (_, i) => i + 1).map(n => (
          <button
            key={n}
            style={{
              ...styles.chapterBtn,
              ...(n === chapter ? styles.chapterBtnActive : {}),
            }}
            onClick={() => onChapterChange(n)}
            onMouseOver={e => {
              if (n !== chapter) {
                e.target.style.background = 'var(--parchment-deep)';
              }
            }}
            onMouseOut={e => {
              if (n !== chapter) {
                e.target.style.background = 'var(--card-bg)';
              }
            }}
          >
            {n}
          </button>
        ))}
      </div>

      {/* Verse blocks */}
      {chapterData.verses.map(verse => (
        <VerseBlock key={verse.verse} verse={verse} />
      ))}
    </div>
  );
}
