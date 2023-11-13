import React, {useState, useContext, useEffect} from 'react';
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';
import axios from 'axios';
import '../styles/join.css';

const JoinGame = () => {

    const { client, setPlayer, roomId, setRoomId } = useContext(StateContext);
    const [playerName, setPlayerName] = useState('');
    const [urlParams, setUrlParams] = useState(new URLSearchParams(window.location.search));
    useEffect(() => {
        setRoomId(urlParams.get('roomId'));
        setPlayerName(urlParams.get('playerName'));

        if (playerName){
            joinRoom()
        }
      }, []);

    const navigate = useNavigate();

    const joinRoom = () => {
        client.post('/api/'+roomId, {
            name: playerName
        }).then((response) => {
            console.log(response)
            setPlayer(response.data)
            navigate('/play')
        }).catch((error) => {
            console.log(error);
        })
    }

    return (
        <div className='container'>
            <div className='join-container'>
                <h1>Welcome to ClueMaster!</h1>
                <form className='join-options' onSubmit={(e) => {
                    e.preventDefault(); 
                    return navigate('/create?playerName='+playerName);
                }}>
                    <input className='item' id='name' type='text' placeholder='Enter your name' value={playerName} onChange={(e) => setPlayerName(e.target.value)} required/>
                    <button className='item play' onClick={joinRoom}>Play</button>
                    <button className='item create' type='submit'>Create Private Room</button>
                </form>
            </div>
        </div>
    )
}

export default JoinGame