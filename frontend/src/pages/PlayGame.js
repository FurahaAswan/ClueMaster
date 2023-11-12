import React, { useState } from 'react'
import { useEffect, useContext, useRef } from 'react'
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';

const PlayGame = () => {

    const { player, roomId } = useContext(StateContext);
    const [guess, setGuess] = useState('')
    const navigate = useNavigate();
    const socketRef = useRef(null);

    useEffect(() => {
        if (!player){
            navigate('/')
        }
    })

    useEffect(() => {
          
        socketRef.current = new WebSocket(`ws://localhost:8000/ws/game/${roomId}/?playerI`)
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
                // Handle guess message
                console.log('Received guess:', data);
            } else if (data.type === 'chat_message') {
            // Handle chat message
            console.log('Received chat message:', data);
            } else if (data.type === 'timer_update') {
            document.getElementById('timer').textContent = data.value
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


    return (
        <div>
            <p id='timer'></p>
            <button onClick={startTimer}>Start</button>
            <input type="text" id="guess" placeholder="Type your message" value={guess} onChange={(e) => setGuess(e.target.value)}/>
            <button id="send_guess" onClick={sendGuess}>Submit Guess</button>
        </div>
    )
}

export default PlayGame