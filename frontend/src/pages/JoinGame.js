import React, {useState, useContext, useEffect} from 'react';
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';
import axios from 'axios';
import '../styles/join.css';

const JoinGame = () => {

    const { client, setPlayer, roomId, setRoomId } = useContext(StateContext);
    const [urlParams, setUrlParams] = useState(new URLSearchParams(window.location.search));
    useEffect(() => {
        setRoomId(urlParams.get('roomId'));
      }, []);
      
    const [name, setName] = useState('');

    const navigate = useNavigate();

    const joinRoom = () => {
        client.post('/api/'+roomId, {
            name: name
        }).then((response) => {
            console.log(response)
            setPlayer(response.data)
            navigate('/play')
        }).catch((error) => {
            console.log(error);
        })
    }

    const createRoom = () => {
        console.log('createRoom');
    }

    return (
        <div className='container'>
            <div className='join-container'>
                <h1>Welcome to ClueMaster!</h1>
                <div className='join-options'>
                    <input className='item' id='name' type='text' placeholder='Enter your name' value={name} onChange={(e) => setName(e.target.value)}/>
                    <button className='item play' onClick={joinRoom}>Play</button>
                    <button className='item create' onClick={() => {return navigate('/create')}}>Create Private Room</button>
                </div>
            </div>
        </div>
    )
}

export default JoinGame