import React from 'react';

const styles = {
  footer: {
    background: '#2C1810',
    color: '#8A7A6A',
    padding: '32px 16px',
    textAlign: 'center',
    fontFamily: "'EB Garamond', serif",
  },
  title: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 18,
    fontWeight: 600,
    color: '#FAF6F0',
    marginBottom: 4,
  },
  publisher: {
    fontSize: 14,
    color: '#B8860B',
    marginBottom: 12,
  },
  credits: {
    fontSize: 12,
    color: '#8A7A6A',
    lineHeight: 1.6,
    maxWidth: 600,
    margin: '0 auto',
  },
};

export default function Footer() {
  return (
    <footer style={styles.footer}>
      <div style={styles.title}>Torah: Word by Word</div>
      <div style={styles.publisher}>Published by The Forum Press</div>
      <div style={{fontSize: 12, color: '#D8CFBF', marginBottom: 12}}>Compiled by Asaf Fulks</div>
      <div style={styles.credits}>
        Hebrew text follows the Westminster Leningrad Codex &middot;
        Gematria: Mispar Hechrachi &middot;
        Commentary: Rashi &amp; Ramban
      </div>
    </footer>
  );
}
