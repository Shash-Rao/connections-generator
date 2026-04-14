import { useState } from "react";

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
          background:
            linear-gradient(to right, #c77ad9 0 42%, #f6f3f0 42% 58%, #c77ad9 58% 100%),
            linear-gradient(to right, #c77ad9 0 74%, #f6f3f0 74% 100%),
            linear-gradient(to right, #c77ad9 0 24%, #f6f3f0 24% 46%, #c77ad9 46% 100%),
            linear-gradient(to right, #f6f3f0 0 22%, #c77ad9 22% 100%);
          background-size: 100% 25%, 100% 25%, 100% 25%, 100% 25%;
          background-position: 0 0, 0 25%, 0 50%, 0 75%;
          background-repeat: no-repeat;
          margin-bottom: 34px;
          box-sizing: border-box;
        }

        .title {
          font-size: 5.5rem;
          font-weight: 900;
          line-height: 1;
          color: black;
          margin: 0 0 26px 0;
          font-family: Georgia, "Times New Roman", serif;
        }

        .subtitle {
          font-size: 2.1rem;
          color: black;
          margin: 0 0 42px 0;
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
          background: #f7f3e8;
        }

        @media (max-width: 700px) {
          .title {
            font-size: 4rem;
          }

          .subtitle {
            font-size: 1.6rem;
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
          <div className="logo-box" />
          <h1 className="title">Connections</h1>
          <p className="subtitle">Subscribe for unlimited play.</p>
          <button className="play-button" onClick={onPlay}>
            Play
          </button>
        </div>
      </div>
    </>
  );
}

function BlankScreen() {
  return <div className="screen blank-page" />;
}

export default function App() {
  const [started, setStarted] = useState(false);

  return started ? (
    <BlankScreen />
  ) : (
    <HomeScreen onPlay={() => setStarted(true)} />
  );
}