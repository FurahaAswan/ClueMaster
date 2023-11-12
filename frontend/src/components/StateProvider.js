import React, { createContext, useState } from 'react';
import axios from 'axios';

export const StateContext = createContext();

export const StateProvider = ({ children }) => {
  const [player, setPlayer] = useState();
  const [roomId, setRoomId] = useState();
  
  const client = axios.create({
    baseURL: 'http://localhost:8000'
  });


  return (
    <StateContext.Provider value={{ client, player, setPlayer, roomId, setRoomId}}>
      {children}
    </StateContext.Provider>
  );
};

export default StateProvider;