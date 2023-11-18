import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/create.css';
import { useNavigate } from 'react-router-dom';

const CreateGame = () => {
  const [formData, setFormData] = useState({
    name: '',
    rounds: 2,
    guess_time: 60,
    max_players: 2,
    category: '', // Add category field
    difficulty: 'easy', // Add difficulty field with default value
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
      console.log('Form Data', formData)
      const response = await client.post('/api/room/create/', formData);
      console.log('Room created successfully:', response.data);
      navigate(`/?roomId=${response.data.id}&playerName=${playerName}`);
    } catch (error) {
      console.error('Error creating room:', error);
    }
  };

  const generateOptions = (min, max, interval) => {
    const options = [];
    for (let i = min; i <= max; i += interval) {
      options.push(<option key={i} value={i}>{i}</option>);
    }
    return options;
  };

  return (
    <div className='create-container'>
      <form className='form-container' onSubmit={handleSubmit}>
        <label className='label'>
          Room Name:
          <input type="text" name="name" value={formData.name} onChange={handleChange} className='input-field' required />
        </label>
        <label className='label'>
          Rounds:
          <select name="rounds" value={formData.rounds} onChange={handleChange} className='input-field' required>
            {generateOptions(2,10,1)}
          </select>
        </label>
        <label className='label'>
          Guess Time:
          <select name="guess_time" value={formData.guess_time} onChange={handleChange} className='input-field' required>
            {generateOptions(60,200,10)}
          </select>
        </label>
        <label className='label'>
          Max Players:
          <select name="max_players" value={formData.max_players} onChange={handleChange} className='input-field' required>
            {generateOptions(2,20,1)}
          </select>
        </label>
        {/* Add category field */}
        <label className='label'>
          Category:
          <input type="text" name="category" value={formData.category} onChange={handleChange} className='input-field' required />
        </label>
        {/* Add difficulty field */}
        <label className='label'>
          Difficulty:
          <select name="difficulty" value={formData.difficulty} onChange={handleChange} className='input-field' required>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>
        <button type="submit" className='button'>Create Room</button>
      </form>
    </div>
  );
};

export default CreateGame;
