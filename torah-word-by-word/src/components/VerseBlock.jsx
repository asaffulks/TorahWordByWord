import React from 'react';
import WordCard from './WordCard';

const styles = {
  container: {
    marginBottom: 24,
    borderRadius: 8,
    overflow: 'hidden',
    border: '1px solid var(--card-border)',
    background: 'var(--card-bg)',
  },
  header: {
    background: 'var(--amber-bg)',
    borderBottom: '1px solid var(--amber-border)',
    padding: '8px 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  ref: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 14,
    fontWeight: 700,
    color: 'var(--amber-text)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  translation: {
    fontSize: 13,
    color: 'var(--ink-light)',
    fontStyle: 'italic',
    flex: 1,
    textAlign: 'right',
    minWidth: 200,
  },
  wordGrid: {
    display: 'flex',
    flexWrap: 'wrap',
    direction: 'rtl',
    justifyContent: 'flex-start',
    gap: 8,
    padding: '12px 16px',
  },
  footer: {
    background: 'var(--parchment-deep)',
    borderTop: '1px solid var(--divider)',
    padding: '8px 16px',
  },
  footerTop: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  gemLabel: {
    fontSize: 12,
    color: 'var(--ink-faint)',
  },
  gemPill: {
    background: 'var(--blue-bg)',
    color: 'var(--blue-text)',
    border: '1px solid var(--blue-border)',
    borderRadius: 12,
    padding: '2px 12px',
    fontSize: 13,
    fontWeight: 600,
  },
  gemNote: {
    fontSize: 11,
    color: 'var(--ink-faint)',
    fontStyle: 'italic',
    marginLeft: 8,
  },
  rashi: {
    marginTop: 8,
    paddingTop: 8,
    borderTop: '1px dashed var(--divider)',
    fontSize: 12,
    color: 'var(--ink-light)',
    fontStyle: 'italic',
    lineHeight: 1.5,
  },
  rashiLabel: {
    fontStyle: 'normal',
    fontWeight: 600,
    color: 'var(--ink)',
    marginRight: 4,
  },
};

export default function VerseBlock({ verse }) {
  return (
    <div style={styles.container}>
      {/* Section header */}
      <div style={styles.header}>
        <span style={styles.ref}>{verse.ref}</span>
        <span style={styles.translation}>{verse.translation}</span>
      </div>

      {/* Word card grid — RTL */}
      <div style={styles.wordGrid}>
        {verse.words.map((word, i) => (
          <WordCard key={i} word={word} />
        ))}
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        <div style={styles.footerTop}>
          <span style={styles.gemLabel}>Verse total:</span>
          <span style={styles.gemPill}>{verse.total_gematria}</span>
          {verse.gem_note && (
            <span style={styles.gemNote}>{verse.gem_note}</span>
          )}
        </div>
        {verse.rashi && (
          <div style={styles.rashi}>
            <span style={styles.rashiLabel}>Rashi:</span>
            {verse.rashi}
          </div>
        )}
        {verse.ramban && (
          <div style={styles.rashi}>
            <span style={styles.rashiLabel}>Ramban:</span>
            {verse.ramban}
          </div>
        )}
        {verse.ibn_ezra && (
          <div style={styles.rashi}>
            <span style={styles.rashiLabel}>Ibn Ezra:</span>
            {verse.ibn_ezra}
          </div>
        )}
        {verse.sforno && (
          <div style={styles.rashi}>
            <span style={styles.rashiLabel}>Sforno:</span>
            {verse.sforno}
          </div>
        )}
        {verse.or_hachaim && (
          <div style={styles.rashi}>
            <span style={styles.rashiLabel}>Or HaChaim:</span>
            {verse.or_hachaim}
          </div>
        )}
      </div>
    </div>
  );
}
