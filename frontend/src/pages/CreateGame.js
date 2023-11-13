// CreateRoomForm.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/create.css'; // Import the styles
import { useNavigate } from 'react-router-dom';

const CreateGame = () => {
  const [formData, setFormData] = useState({
    name: '',
    rounds: 0,
    guess_Time: 0,
    max_players: 0,
  });

  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const [playerName, setPlayerName] = useState();

  const [urlParams, setUrlParams] = useState(new URLSearchParams(window.location.search));
    useEffect(() => {
        setPlayerName(urlParams.get('playerName'));
      }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      // Make a POST request to create a new room
      const response = await axios.post('http://localhost:8000/api/room/create/', formData);

      // Handle the response as needed
      console.log('Room created successfully:', response.data);
      
      navigate(`/?roomId=${response.data.id}&playerName=${playerName}`)

      // Optionally, you can redirect the user or perform other actions after room creation
    } catch (error) {
      console.error('Error creating room:', error);
      // Handle errors as needed
    }
  };

  return (
    <div className='container'>
        <form className='formContainer' onSubmit={handleSubmit}>
        <label className='label'>
            Room Name:
            <input type="text" name="name" value={formData.name} onChange={handleChange} className='inputField' required />
        </label>
        <label className='label'>
            Rounds:
            <input type="number" name="rounds" value={formData.rounds} onChange={handleChange} className='inputField' required />
        </label>
        <label className='label'>
            Guess Time:
            <input type="number" name="guess_time" value={formData.guess_time} onChange={handleChange} className='inputField' required />
        </label>
        <label className='label'>
            Max Players:
            <input type="number" name="max_players" value={formData.max_players} onChange={handleChange} className='inputField' required />
        </label>
        <button type="submit" className='button'>Create Room</button>
        </form>
    </div>
  );
};

export default CreateGame;
