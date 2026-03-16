import React from 'react';

const LETTERS = [
  { he: 'א', name: 'Alef', val: 1 },
  { he: 'ב', name: 'Bet', val: 2 },
  { he: 'ג', name: 'Gimel', val: 3 },
  { he: 'ד', name: 'Dalet', val: 4 },
  { he: 'ה', name: 'He', val: 5 },
  { he: 'ו', name: 'Vav', val: 6 },
  { he: 'ז', name: 'Zayin', val: 7 },
  { he: 'ח', name: 'Chet', val: 8 },
  { he: 'ט', name: 'Tet', val: 9 },
  { he: 'י', name: 'Yod', val: 10 },
  { he: 'כ', name: 'Kaf', val: 20 },
  { he: 'ל', name: 'Lamed', val: 30 },
  { he: 'מ', name: 'Mem', val: 40 },
  { he: 'נ', name: 'Nun', val: 50 },
  { he: 'ס', name: 'Samekh', val: 60 },
  { he: 'ע', name: 'Ayin', val: 70 },
  { he: 'פ', name: 'Pe', val: 80 },
  { he: 'צ', name: 'Tsadi', val: 90 },
  { he: 'ק', name: 'Qof', val: 100 },
  { he: 'ר', name: 'Resh', val: 200 },
  { he: 'ש', name: 'Shin', val: 300 },
  { he: 'ת', name: 'Tav', val: 400 },
];

const styles = {
  section: {
    background: 'var(--amber-bg)',
    padding: '32px 16px',
    marginTop: 48,
  },
  container: {
    maxWidth: 960,
    margin: '0 auto',
  },
  title: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 22,
    fontWeight: 600,
    color: 'var(--amber-text)',
    textAlign: 'center',
    marginBottom: 20,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(11, 1fr)',
    gap: 8,
  },
  cell: {
    background: 'var(--card-bg)',
    border: '1px solid var(--amber-border)',
    borderRadius: 6,
    padding: '8px 4px',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 2,
  },
  he: {
    fontFamily: "'SBL Hebrew', 'Noto Serif Hebrew', serif",
    fontSize: 24,
    color: 'var(--ink)',
  },
  name: {
    fontSize: 10,
    color: 'var(--ink-faint)',
  },
  val: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--blue-text)',
  },
};

export default function GematriaChart() {
  const row1 = LETTERS.slice(0, 11);
  const row2 = LETTERS.slice(11, 22);

  return (
    <section id="gematria-chart" style={styles.section}>
      <div style={styles.container}>
        <h2 style={styles.title}>Gematria Reference — Mispar Hechrachi</h2>
        <div style={styles.grid}>
          {row1.map(l => (
            <div key={l.he} style={styles.cell}>
              <span style={styles.he}>{l.he}</span>
              <span style={styles.name}>{l.name}</span>
              <span style={styles.val}>{l.val}</span>
            </div>
          ))}
          {row2.map(l => (
            <div key={l.he} style={styles.cell}>
              <span style={styles.he}>{l.he}</span>
              <span style={styles.name}>{l.name}</span>
              <span style={styles.val}>{l.val}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
