// WinnersScreen.js
import React from 'react';

const GameOver = ({ winners }) => {
  return (
    <div className='overlay'>
      <h1>Game Over</h1>
      {winners.map((winner, index) => (
        <h2 key={index}>{index+1}.  {winner.player_name} {winner.score}</h2>
      ))}
    </div>
  );
};

export default GameOver;
