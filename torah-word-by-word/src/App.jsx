import { useState, useEffect } from 'react';
import NavBar from './components/NavBar';
import ChapterView from './components/ChapterView';
import GematriaChart from './components/GematriaChart';
import Footer from './components/Footer';
import genesisData from './data/genesis.json';

export default function App() {
  const [chapter, setChapter] = useState(1);

  useEffect(() => {
    const hash = window.location.hash;
    const match = hash.match(/chapter[/-]?(\d+)/i);
    if (match) {
      const ch = parseInt(match[1], 10);
      if (ch >= 1 && ch <= genesisData.chapters.length) {
        setChapter(ch);
      }
    }
  }, []);

  const handleChapterChange = (ch) => {
    setChapter(ch);
    window.location.hash = `chapter-${ch}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      <NavBar />
      <main>
        <ChapterView
          data={genesisData}
          chapter={chapter}
          onChapterChange={handleChapterChange}
        />
        <GematriaChart />
      </main>
      <Footer />
    </>
  );
}
