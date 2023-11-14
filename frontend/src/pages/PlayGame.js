import React, { useEffect, useContext, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';
import '../styles/game.css';
import clipboard from 'clipboard-copy';

const PlayGame = () => {

    const { player, roomId } = useContext(StateContext);
    const [timer, setTimer] = useState(0);
    const [guess, setGuess] = useState('')
    const navigate = useNavigate();
    const socketRef = useRef(null);
    const [chatlog, setChatLog] = useState([]);
    const [wordToGuess, setWordToGuess] = useState("");
    const [players, setPlayers] = useState([]);
    const [clues, setClues] = useState([]);

    useEffect(() => {
        if (!player){
            navigate('/')
        }
    }, [player])

    useEffect(() => {
        console.log('Chat Log updated:', chatlog);
    }, [chatlog]);

    useEffect(() => {
        socketRef.current = new WebSocket(`ws://localhost:8000/ws/game/${roomId}/${player.id}`)
        const socket = socketRef.current

        console.log('chatSocket: ', socket)
        
        socket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        socket.onopen = function (event) {
            console.log('WebSocket connection opened:', event);
        };
        
        socket.onclose = function (event) {
            console.log('WebSocket connection closed:', event);
            navigate('/');
        };

        // Clean up the WebSocket connection when the component unmounts
        return () => {
            if (socket.readyState === 1) { // <-- This is important
                socket.close();
            }
        }
        
    }, [roomId, player.id]);

        function handleWebSocketMessage(data) {
            console.log('handle')
            // Handle different types of messages here
            if (data.type === 'guess') {
                console.log('Received guess:', data);
                setChatLog(prevChatLog => [...prevChatLog, data]);
            } else if (data.type === 'timer_update') {
                setTimer(data.value)
            } else if (data.type === 'player_join') {
                console.log('Player joined:', data);
                setChatLog(prevChatLog => [...prevChatLog, data]);
            } else if (data.type === 'host_update') {
                console.log('host_update',data);
                setChatLog(prevChatLog => [...prevChatLog, data]);
            } else if (data.type === 'game_state'){
                console.log('game_state', data)
                setPlayers(data.players)
                setClues(data.clues)
                setWordToGuess(data.word_to_guess);
            } else if (data.type === 'player_leave') {
                setChatLog(prevChatLog => [...prevChatLog, data]);
            }
        }

        function startRound() {
            if (socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({
                    'type': 'start_game'
                }));
            }
        }
        
        function sendGuess() {
            if (socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({
                    'type': 'guess',
                    'text': guess,
                    'player': player.id
                }));
            }
        }
        

        let handleKeyDown = (e) => {
            if (e.key === 'Enter') {
                sendGuess();
                setGuess('');
            }
        }

        function copyInviteLink() {
            clipboard(window.location.host+`?roomId=${roomId}`);
        }

    return (
        <div className='game-container'>
            <div className='header'>
                <div className='left'>
                    <h1 className='timer'>{timer}</h1>
                    <h1 className='round-number'>Round #</h1>
                </div>
                <div className='middle'>
                    <h1>{wordToGuess}</h1>
                </div>
            </div>
            <div className='clue-board'>
                {
                    clues.map((clue, index) => (
                        <h1 key={index} className='clue'>{index+1}. {clue}</h1>
                    ))
                }
                <button onClick={startRound}>Start</button>
                <button onClick={copyInviteLink}>Click to get Invite Link</button>
            </div>
            <div className='scoreboard'>
                {
                    players.map((activePlayer, index) => (
                        <div className='player' key={index}>
                            <h1>{activePlayer.id === player.id ? activePlayer.player_name+' (You)' : activePlayer.player_name}</h1>
                            <h1 className='score'>{activePlayer.score}</h1>
                        </div>
                    ))
                }
            </div>
            <div className='player-chat'>
                {
                    chatlog.map((message, index) => (
                        <div key={index} className={index % 2 === 0 ? 'chat-message' : 'chat-message alt'}>
                            {message.type === 'host_update' ? 
                                <p className='host'>message.host.name + ' is the room host'</p> 
                            : message.type === 'player_join' ? 
                                <p className='join'> {message.name} joined the room!</p> 
                            : message.type === 'guess' ? 
                                <p><span className='name'>{message.player_name}:</span> {message.text}</p>
                            : message.type === 'player_leave' ? 
                                <p className='leave'>{message.name} left the room</p>
                            :
                                <p>Unknown Message</p>
                            }
                        </div>
                    ))
                }
                <div className='user-input'>
                    <input type="text" id="guess" placeholder="Type your guess here" value={guess} onChange={(e) => setGuess(e.target.value)} onKeyDown={handleKeyDown}/>
                </div>
            </div>
        </div>
    )
}

export default PlayGame