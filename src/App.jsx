import { useState } from "react";
import boards from "./boards.json";

function shuffleArray(array) {
  const copy = [...array];

  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }

  return copy;
}

function buildTilesFromBoard(boardIndex) {
  const board = boards[boardIndex];

  return shuffleArray(
    board.flatMap((category, categoryIndex) =>
      category.words.map((word, wordIndex) => ({
        id: `${boardIndex}-${categoryIndex}-${wordIndex}`,
        word,
        group: `group-${categoryIndex}`,
        bandColor: category.difficulty,
        selected: false,
        solved: false,
        categoryName: category.category_name,
        categoryType: category.category_type,
      }))
    )
  );
}

function HomeScreen({ onPlay }) {
  return (
    <>
      <style>{`
        @keyframes slowRise {
          from {
            opacity: 0;
            transform: translateY(40px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .screen {
          min-height: 100vh;
          width: 100%;
          display: flex;
          justify-content: center;
          align-items: center;
          box-sizing: border-box;
        }

        .landing {
          background: #b6a7f2;
        }

        .landing-content {
          animation: slowRise 1.6s ease-out;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .logo-box {
          width: 150px;
          height: 150px;
          border: 7px solid black;
          border-radius: 22px;
          box-sizing: border-box;
          margin-bottom: 34px;
          overflow: hidden;
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          grid-template-rows: repeat(4, 1fr);
          background-color: #c77ad9;
          position: relative;
        }

        .logo-box::after {
          content: "";
          position: absolute;
          inset: 0;
          background:
            linear-gradient(
              to bottom,
              transparent 24%,
              black 24% 27%,
              transparent 27% 49%,
              black 49% 52%,
              transparent 52% 74%,
              black 74% 77%,
              transparent 77%
            ),
            linear-gradient(
              to right,
              transparent 24%,
              black 24% 27%,
              transparent 27% 49%,
              black 49% 52%,
              transparent 52% 74%,
              black 74% 77%,
              transparent 77%
            );
        }

        .title {
          font-size: 5.5rem;
          font-weight: 900;
          line-height: 1;
          color: black;
          margin: 0 0 26px 0;
          font-family: Georgia, "Times New Roman", serif;
        }

        .play-button {
          width: 360px;
          max-width: 80vw;
          height: 96px;
          border: none;
          border-radius: 999px;
          background: black;
          color: white;
          font-size: 2.2rem;
          font-weight: 700;
          cursor: pointer;
          transition: transform 0.15s ease, opacity 0.15s ease;
        }

        .play-button:hover {
          transform: scale(1.02);
        }

        .play-button:active {
          transform: scale(0.98);
        }

        .blank-page {
          background: #f4f3ee;
        }

        @media (max-width: 700px) {
          .title {
            font-size: 4rem;
          }

          .play-button {
            height: 82px;
            font-size: 1.8rem;
          }

          .logo-box {
            width: 120px;
            height: 120px;
          }
        }
      `}</style>

      <div className="screen landing">
        <div className="landing-content">
          <div className="logo-box">
            <div></div>
            <div></div>
            <div style={{ backgroundColor: "#f6f3f0" }}></div>
            <div></div>

            <div></div>
            <div></div>
            <div></div>
            <div style={{ backgroundColor: "#f6f3f0" }}></div>

            <div></div>
            <div style={{ backgroundColor: "#f6f3f0" }}></div>
            <div></div>
            <div></div>

            <div style={{ backgroundColor: "#f6f3f0" }}></div>
            <div></div>
            <div></div>
            <div></div>
          </div>

          <h1 className="title">Connections</h1>

          <button className="play-button" onClick={onPlay}>
            Play
          </button>

          <div style={{ marginTop: "60px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "2rem",
                fontWeight: "600",
                marginBottom: "10px",
                fontFamily: 'Georgia, "Times New Roman", serif',
                color: "black",
              }}
            >
              Probabilistic Machine Learning
            </div>

            <div
              style={{
                fontSize: "1.2rem",
                maxWidth: "1000px",
                lineHeight: "1.5",
                color: "black",
              }}
            >
              By: Clara Bartusiak, Aayush Kashyap, Noah Obuya, Shashwat Rao, and
              Taran Srikonda
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function BlankScreen() {

  const groupColors = {
    yellow: "#efd86a",
    green: "#9fc35a",
    blue: "#b8c7ee",
    purple: "#b47fc7",
  };
  
  const [tiles, setTiles] = useState(() =>
    buildTilesFromBoard(Math.floor(Math.random() * boards.length))
  );
  const [solvedBands, setSolvedBands] = useState([]);
  const [animatingGroup, setAnimatingGroup] = useState(null);
  const [wrongGuessAnimating, setWrongGuessAnimating] = useState(false);
  const [mistakesRemaining, setMistakesRemaining] = useState(4);
  const selectedCount = tiles.filter((tile) => tile.selected).length;

  function handleTileClick(id) {
    if (animatingGroup || wrongGuessAnimating || mistakesRemaining === 0) return;
    const clickedTile = tiles.find((tile) => tile.id === id);
    const currentSelected = tiles.filter((tile) => tile.selected).length;

    if (!clickedTile || clickedTile.solved) return;
    if (!clickedTile.selected && currentSelected >= 4) return;

    setTiles((prevTiles) =>
      prevTiles.map((tile) =>
        tile.id === id ? { ...tile, selected: !tile.selected } : tile
      )
    );
  }

  function handleSubmit() {
    if (animatingGroup || wrongGuessAnimating || mistakesRemaining === 0) return;
    const selectedTiles = tiles.filter((tile) => tile.selected);
    if (selectedTiles.length !== 4) return;

    const selectedGroup = selectedTiles[0].group;
    const allSameGroup = selectedTiles.every(
      (tile) => tile.group === selectedGroup
    );
    
    if (!allSameGroup) {
      setWrongGuessAnimating(true);
    
      setTimeout(() => {
        setWrongGuessAnimating(false);
    
        setMistakesRemaining((prev) => {
          const next = prev - 1;
    
          if (next <= 0) {
            revealAllGroups();
            return 0;
          }
    
          return next;
        });
      }, 420);
    
      return;
    }

    setAnimatingGroup(selectedGroup);

    setTimeout(() => {
      const solvedCategory = selectedTiles[0];


      
      setSolvedBands((prev) =>
        prev.some((band) => band.group === selectedGroup)
          ? prev
          : [
              ...prev,
              {
                group: selectedGroup,
                bandColor: solvedCategory.bandColor,
                categoryName: solvedCategory.categoryName,
                words: selectedTiles.map((tile) => tile.word),
              },
            ]
      );

      setTiles((prevTiles) =>
        prevTiles.map((tile) =>
          tile.group === selectedGroup
            ? { ...tile, selected: false, solved: true }
            : tile
        )
      );

      setAnimatingGroup(null);
    }, 520);
  }

  function revealAllGroups() {
    const remainingGroups = [];
    const seenGroups = new Set();
  
    tiles.forEach((tile) => {
      if (!tile.solved && !seenGroups.has(tile.group)) {
        seenGroups.add(tile.group);
        remainingGroups.push({
          group: tile.group,
          bandColor: tile.bandColor,
          categoryName: tile.categoryName,
          words: tiles
            .filter((t) => t.group === tile.group)
            .map((t) => t.word),
        });
      }
    });
  
    setSolvedBands((prev) => [
      ...prev,
      ...remainingGroups.filter(
        (group) => !prev.some((band) => band.group === group.group)
      ),
    ]);
  
    setTiles((prevTiles) =>
      prevTiles.map((tile) => ({
        ...tile,
        selected: false,
        solved: true,
      }))
    );
  }

  function handleRegenerate() {
    if (animatingGroup || wrongGuessAnimating) return;
  
    setTiles(buildTilesFromBoard(Math.floor(Math.random() * boards.length)));
    setSolvedBands([]);
    setAnimatingGroup(null);
    setWrongGuessAnimating(false);
    setMistakesRemaining(4);
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        background: "#f5f5f0",
        paddingTop: "36px",
        paddingBottom: "24px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        fontFamily: 'Arial, Helvetica, sans-serif',
      }}
    >
    <style>{`
  @keyframes solveJump {
    0% {
      transform: translateY(0) scale(1);
    }
    18% {
      transform: translateY(-6px) scale(1.01);
    }
    42% {
      transform: translateY(-18px) scale(1.025);
    }
    68% {
      transform: translateY(-12px) scale(1.018);
    }
    100% {
      transform: translateY(-16px) scale(1.02);
    }
  }

  @keyframes wrongShake {
    0% {
      transform: translateX(0);
    }
    12% {
      transform: translateX(-7px);
    }
    24% {
      transform: translateX(7px);
    }
    36% {
      transform: translateX(-6px);
    }
    48% {
      transform: translateX(6px);
    }
    60% {
      transform: translateX(-4px);
    }
    72% {
      transform: translateX(4px);
    }
    84% {
      transform: translateX(-2px);
    }
    100% {
      transform: translateX(0);
    }
  }
`}</style>

      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "center",
          gap: "12px",
          marginBottom: "12px",
          flexWrap: "wrap",
        }}
      >
        <h1
          style={{
            margin: 0,
            fontFamily: 'Georgia, "Times New Roman", serif',
            fontSize: "2.8rem",
            fontWeight: 900,
            lineHeight: 1,
            color: "#111111",
          }}
        >
          Connections
        </h1>

        <div
          style={{
            fontSize: "1.1rem",
            color: "#333333",
            fontWeight: 400,
          }}
        >
          Probabilistic Machine Learning
        </div>
      </div>

      <div
        style={{
          fontSize: "0.95rem",
          color: "#333333",
          marginBottom: "22px",
        }}
      >
        Create four groups of four!
      </div>

      <div
        style={{
          width: "min(92vw, 760px)",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
       {[...solvedBands]
  .sort((a, b) => {
    const order = { yellow: 0, green: 1, blue: 2, purple: 3 };
    return order[a.bandColor] - order[b.bandColor];
  })
  .map((band) => (
  <div
    key={band.group}
    style={{
      minHeight: "96px",
      borderRadius: "16px",
      background: groupColors[band.bandColor],
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      color: "#111111",
      fontFamily: 'Arial, Helvetica, sans-serif',
      padding: "14px 18px",
      boxSizing: "border-box",
      textAlign: "center",
    }}
  >
    <div
      style={{
        fontWeight: 800,
        fontSize: "1.02rem",
        textTransform: "uppercase",
        marginBottom: "6px",
      }}
    >
      {band.categoryName}
    </div>

    <div
      style={{
        fontWeight: 500,
        fontSize: "0.98rem",
        textTransform: "uppercase",
        lineHeight: 1.3,
      }}
    >
      {band.words.join(", ")}
    </div>
  </div>


))}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "10px",
          }}
        >
          {tiles
            .filter((tile) => !tile.solved)
            .map((tile) => {
              const isAnimatingTile =
  animatingGroup === tile.group && tile.selected;

const isWrongAnimatingTile =
  wrongGuessAnimating && tile.selected;
              return (
                <button
                  key={tile.id}
                  onClick={() => handleTileClick(tile.id)}
                  disabled={!!animatingGroup}
                  style={{
                    background: tile.selected ? "#666457" : "#e7e4db",
                    color: tile.selected ? "#ffffff" : "#111111",
                    border: "none",
                    borderRadius: "8px",
                    height: "96px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    textAlign: "center",
                    fontFamily: 'Arial, Helvetica, sans-serif',
                    fontWeight: 800,
                    fontSize: "0.98rem",
                    textTransform: "uppercase",
                    lineHeight: 1.05,
                    padding: "8px",
                    cursor: animatingGroup || wrongGuessAnimating ? "default" : "pointer", animation: isAnimatingTile
  ? "solveJump 520ms cubic-bezier(0.22, 0.8, 0.22, 1) forwards"
  : isWrongAnimatingTile
  ? "wrongShake 420ms ease-in-out"
  : "none",
transition:
  "background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease",
boxShadow: isAnimatingTile
  ? "0 6px 14px rgba(0, 0, 0, 0.08)"
  : isWrongAnimatingTile
  ? "0 4px 10px rgba(0, 0, 0, 0.06)"
  : "none",
                  }}
                >
                  {tile.word}
                </button>
              );
            })}
        </div>
      </div>

      <div
  style={{
    marginTop: "22px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
  }}
>
  <div
    style={{
      fontSize: "1rem",
      color: "#333333",
      fontWeight: 500,
    }}
  >
    Mistakes remaining
  </div>

  <div
    style={{
      display: "flex",
      gap: "10px",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "16px",
    }}
  >
    {[0, 1, 2, 3].map((index) => (
      <div
        key={index}
        style={{
          width: "12px",
          height: "12px",
          borderRadius: "999px",
          background: index < mistakesRemaining ? "#555555" : "#d8d8d8",
          transition: "background 0.2s ease",
        }}
      />
    ))}
  </div>
</div>

<div
  style={{
    marginTop: "18px",
    display: "flex",
    justifyContent: "center",
    gap: "14px",
  }}
>
  <button
    onClick={handleRegenerate}
    style={{
      padding: "16px 36px",
      borderRadius: "999px",
      fontSize: "1.1rem",
      fontWeight: 600,
      border: "2px solid #111111",
      background: "#f5f5f0",
      color: "#111111",
      cursor: animatingGroup || wrongGuessAnimating ? "default" : "pointer",
      transition: "all 0.15s ease",
    }}
  >
    Regenerate
  </button>

  <button
    onClick={handleSubmit}
    style={{
      padding: "16px 36px",
      borderRadius: "999px",
      fontSize: "1.1rem",
      fontWeight: 600,
      border:
        selectedCount === 4 ? "2px solid #111111" : "2px solid #a6a6a6",
      background: selectedCount === 4 ? "#111111" : "#f1f1f1",
      color: selectedCount === 4 ? "#ffffff" : "#9a9a9a",
      cursor:
        selectedCount === 4 && mistakesRemaining > 0 && !wrongGuessAnimating
          ? "pointer"
          : "default",
      transition: "all 0.15s ease",
    }}
  >
    Submit
  </button>
  </div>
    </div>
  );
}

export default function App() {
  const [started, setStarted] = useState(false);

  return started ? (
    <BlankScreen />
  ) : (
    <HomeScreen onPlay={() => setStarted(true)} />
  );
}