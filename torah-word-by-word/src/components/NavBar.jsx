import React from 'react';

const styles = {
  nav: {
    position: 'sticky',
    top: 0,
    zIndex: 100,
    background: '#2C1810',
    color: '#FAF6F0',
    padding: '0 24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: 56,
    fontFamily: "'EB Garamond', serif",
    boxShadow: '0 2px 8px rgba(44,24,16,0.3)',
  },
  left: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  title: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 20,
    fontWeight: 700,
    color: '#FAF6F0',
    letterSpacing: '0.02em',
  },
  heTitle: {
    fontFamily: "'SBL Hebrew', 'Noto Serif Hebrew', serif",
    fontSize: 18,
    color: '#B8860B',
    direction: 'rtl',
  },
  tagline: {
    fontSize: 13,
    color: '#8A7A6A',
    fontStyle: 'italic',
    marginLeft: 8,
  },
  right: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  link: {
    color: '#D8CFBF',
    textDecoration: 'none',
    fontSize: 14,
    cursor: 'pointer',
    transition: 'color 0.2s',
  },
  supportBtn: {
    background: '#B8860B',
    color: '#FAF6F0',
    border: 'none',
    borderRadius: 20,
    padding: '6px 18px',
    fontFamily: "'EB Garamond', serif",
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'background 0.2s',
  },
};

export default function NavBar() {
  return (
    <nav style={styles.nav}>
      <div style={styles.left}>
        <span style={styles.title}>Torah: Word by Word</span>
        <span style={styles.heTitle}>תּוֹרָה</span>
        <span className="nav-tagline" style={styles.tagline}>
          The Hebrew Bible, one word at a time
        </span>
      </div>
      <div style={styles.right}>
        <a className="nav-link" style={styles.link} href="#gematria-chart">Gematria</a>
        <a className="nav-link" style={styles.link} href="https://theforumpress.com" target="_blank" rel="noopener noreferrer">The Forum Press</a>
        <button
          style={styles.supportBtn}
          onMouseOver={e => e.target.style.background = '#9A7209'}
          onMouseOut={e => e.target.style.background = '#B8860B'}
        >
          Support
        </button>
      </div>
    </nav>
  );
}
