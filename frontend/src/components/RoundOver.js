import React from 'react';

const BetweenRounds = ({ word }) => {
  return (
    <div className='overlay'>
      <h1>Round Over</h1>
      <h2>{word}</h2>
    </div>
  );
};

export default BetweenRounds;
