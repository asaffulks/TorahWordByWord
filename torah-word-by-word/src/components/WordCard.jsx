import React from 'react';

const styles = {
  card: {
    background: 'var(--card-bg)',
    border: '1px solid var(--card-border)',
    borderRadius: 6,
    padding: '8px 6px',
    minWidth: 80,
    maxWidth: 140,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 3,
    cursor: 'default',
    transition: 'transform 0.15s, background 0.15s, border-color 0.15s',
    flex: '0 0 auto',
  },
  cardHover: {
    transform: 'translateY(-2px)',
    background: 'var(--card-hover)',
    borderColor: 'var(--amber-border)',
    boxShadow: '0 4px 12px rgba(44,24,16,0.08)',
  },
  hebrew: {
    fontFamily: "'SBL Hebrew', 'Noto Serif Hebrew', 'EB Garamond', serif",
    fontSize: 22,
    direction: 'rtl',
    color: 'var(--ink)',
    textAlign: 'center',
    lineHeight: 1.3,
  },
  transliteration: {
    fontSize: 11,
    fontStyle: 'italic',
    color: 'var(--ink-faint)',
    textAlign: 'center',
    lineHeight: 1.2,
  },
  rootBadge: {
    background: 'var(--amber-bg)',
    color: 'var(--amber-text)',
    border: '1px solid var(--amber-border)',
    borderRadius: 10,
    padding: '1px 8px',
    fontSize: 11,
    fontFamily: "'SBL Hebrew', 'Noto Serif Hebrew', serif",
    direction: 'rtl',
    lineHeight: 1.4,
  },
  rootHidden: {
    visibility: 'hidden',
  },
  divider: {
    width: '80%',
    height: 1,
    background: 'var(--divider)',
    margin: '2px 0',
  },
  english: {
    fontSize: 12,
    color: 'var(--ink)',
    fontWeight: 500,
    textAlign: 'center',
    lineHeight: 1.3,
    minHeight: 16,
  },
  gemBadge: {
    background: 'var(--blue-bg)',
    color: 'var(--blue-text)',
    border: '1px solid var(--blue-border)',
    borderRadius: 10,
    padding: '1px 8px',
    fontSize: 10,
    lineHeight: 1.4,
  },
};

export default function WordCard({ word }) {
  const [hovered, setHovered] = React.useState(false);

  return (
    <div
      style={{
        ...styles.card,
        ...(hovered ? styles.cardHover : {}),
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={styles.hebrew}>{word.heb}</div>
      <div style={styles.transliteration}>{word.tr}</div>
      <div style={{
        ...styles.rootBadge,
        ...(word.root ? {} : styles.rootHidden),
      }}>
        {word.root || '\u00A0'}
      </div>
      <div style={styles.divider} />
      <div style={styles.english}>{word.eng || '\u00A0'}</div>
      <div style={styles.gemBadge}>{word.gem}</div>
    </div>
  );
}
