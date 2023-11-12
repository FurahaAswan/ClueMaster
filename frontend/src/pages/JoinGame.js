import React, {useState, useContext, useEffect} from 'react';
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';
import axios from 'axios';

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
        <div>
            <input id='name' type='text' placeholder='Please enter your name' value={name} onChange={(e) => setName(e.target.value)}/>
            <button onClick={joinRoom}>Play</button>
            <button onClick={createRoom}>Create Private Room</button>
        </div>
    )
}

export default JoinGame