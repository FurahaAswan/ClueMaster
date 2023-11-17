import React, { createContext, useState } from 'react';
import axios from 'axios';

export const StateContext = createContext();

export const StateProvider = ({ children }) => {
  const [player, setPlayer] = useState();
  const [roomId, setRoomId] = useState();
  const [roomName, setRoomName] = useState(''); // Add setter for roomName
  const [rounds, setRounds] = useState(2); // Add setter for rounds
  const [guessTime, setGuessTime] = useState(60); // Add setter for guessTime
  const [maxPlayers, setMaxPlayers] = useState(2); // Add setter for maxPlayers
  const [category, setCategory] = useState('General Knowledge'); // Add setter for category
  const [difficulty, setDifficulty] = useState('easy'); // Add setter for difficulty

  const client = axios.create({
    baseURL: 'http://localhost:8000'
  });

  return (
    <StateContext.Provider value={{ 
      client, 
      player, 
      setPlayer, 
      roomId, 
      setRoomId, 
      roomName, 
      setRoomName, 
      rounds, 
      setRounds, 
      guessTime, 
      setGuessTime, 
      maxPlayers, 
      setMaxPlayers, 
      category, 
      setCategory, 
      difficulty, 
      setDifficulty
    }}>
      {children}
    </StateContext.Provider>
  );
};

export default StateProvider;
