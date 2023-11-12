import React, { useEffect, useContext, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';
import '../styles/game.css';

const PlayGame = () => {

    const { player, roomId } = useContext(StateContext);
    const [timer, setTimer] = useState(0);
    const [guess, setGuess] = useState('')
    const navigate = useNavigate();
    const socketRef = useRef(null);

    useEffect(() => {
        if (!player){
            navigate('/')
        }
    }, [player])

    useEffect(() => {
          
        socketRef.current = new WebSocket(`ws://localhost:8000/ws/game/${roomId}/`)
        const socket = socketRef.current

        console.log('chatSocket: ', socket)
        
        socket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        socket.onopen = function (event) {
            console.log('WebSocket connection opened:', event);

            socket.send(JSON.stringify({type: 'join_room', id: player.id}))
        };
        
        socket.onclose = function (event) {
            console.log('WebSocket connection closed:', event);
        };

        // Clean up the WebSocket connection when the component unmounts
        return () => {
            socket.close();
        };
        
    }, []);

        function handleWebSocketMessage(data) {
            // Handle different types of messages here
            if (data.type === 'guess') {
                console.log('Received guess:', data);
            } else if (data.type === 'timer_update') {
                setTimer(data.value)
            } else if (data.type === 'player_join') {
                console.log('Player joined:', data);
            }
        }

        function startTimer(){
            socketRef.current.send(JSON.stringify({
                'type': 'start_timer'
            }));
        }

        function sendGuess(){
            socketRef.current.send(JSON.stringify({
                'type': 'guess',
                'text': guess,
                'player': player.id
            }));
        }

        let handleKeyDown = (e) => {
            if (e.key === 'Enter') {
                sendGuess();
                setGuess('');
            }
        }

        


    return (
        <div className='game-container'>
            <div className='header'>
                <div className='left'>
                    <h1 className='timer'>{timer}</h1>
                    <h1 className='round-number'>Round #</h1>
                </div>
                <div className='middle'>
                    <h1>_ _ _ _</h1>
                </div>
                <div className='right'></div>
            </div>
            <div className='clue-board'></div>
            <div className='scoreboard'>
                <div className='player'></div>
            </div>
            <div className='player-chat'>
                <div className='user-input'>
                    <input type="text" id="guess" placeholder="Type your guess here" value={guess} onChange={(e) => setGuess(e.target.value)} onKeyDown={handleKeyDown}/>
                </div>
            </div>
        </div>
    )
}

export default PlayGame