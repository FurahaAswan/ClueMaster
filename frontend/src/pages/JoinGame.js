import React, {useState, useContext, useEffect} from 'react';
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';
import '../styles/join.css';
import '../styles/create.css';

const JoinGame = () => {

    const { 
        client, 
        setPlayer, 
        roomId, 
        setRoomId, 
        roomName,
        setRoomName, 
        rounds, 
        guessTime, 
        maxPlayers, 
        category, 
        difficulty,
        setRounds,
        setGuessTime,
        setMaxPlayers,
        setCategory,
        setDifficulty,
    } = useContext(StateContext);
    const [playerName, setPlayerName] = useState('');
    const [formData, setFormData] = useState({
        rounds: parseInt(rounds),
        guess_time: guessTime,
        max_players: maxPlayers,
        category: category, // Add category field
        difficulty: difficulty, // Add difficulty field with default value
      });

      
    useEffect(() => {
        // This effect will run when roomId is updated
        if (!roomId) {
            const urlParams= new URLSearchParams(window.location.search);
            setRoomId(urlParams.get('roomId'))
        }
        if (roomId && playerName) {
            joinRoom();
        }
    }, [roomId]);

    const navigate = useNavigate();

    const joinRoom = () => {
        console.log('Join Room');
        client.post('/api/'+roomId, {
            name: playerName
        }).then((response) => {
            console.log(response);
            setPlayer(response.data);
            console.log('Player', response.data);
            console.log('Navigating to Play')
            navigate('/play')
        }).catch((error) => {
            console.log(error);
        })
    }

    const createRoom = async () => {
        try {
            const response = await client.post('api/room/create/', formData);
            console.log('Room created successfully:', response.data);
            setRounds(response.data.rounds);
            setGuessTime(response.data.guess_time);
            setMaxPlayers(response.data.max_players);
            setCategory(response.data.category);
            setDifficulty(response.data.difficulty);
            setRoomName(response.data.name);
            setRoomId(response.data.id);
    
            // Now that setRoomId has completed, call joinRoom
            joinRoom();
        } catch (error) {
            console.log(error);
        }
    }
    

    return (
        <div className='container'>
            <div className='join-container'>
                <h1>Welcome to ClueMaster!</h1>
                <form className='join-options' onSubmit={(e) => {
                    e.preventDefault();
                    createRoom(); 
                }}>
                    <input className='item' id='name' type='text' placeholder='Enter your name' value={playerName} onChange={(e) => setPlayerName(e.target.value)} required/>
                    <button className='item play' type='button' onClick={joinRoom}>Play</button>
                    <button className='item create' type='submit'>Create Private Room</button>
                </form>
            </div>
        </div>
    )
}

export default JoinGame