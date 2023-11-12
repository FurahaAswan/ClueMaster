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
                setWordToGuess(data.word_to_guess);
                setClues(data.clues);
            } else if (data.type === 'player_list'){
                console.log('player-list',data)
                setPlayers(data.players);
            }
        }

        function startTimer() {
            if (socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({
                    'type': 'start_timer'
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
                <div className='right'></div>
            </div>
            <div className='clue-board'>
                {
                    clues.map((clue, index) => (
                        <h1 key={index} className='clue'>{index+1}. {clue}</h1>
                    ))
                }
            </div>
            <div className='scoreboard'>
                {
                    players.map((activePlayer, index) => (
                        <div className='player' key={index}>
                            <h2>{activePlayer.id === player.id ? activePlayer.player_name+' (You)' : activePlayer.player_name}</h2>
                            <h2 className='score'>{activePlayer.score}</h2>
                        </div>
                    ))
                }
            </div>
            <div className='player-chat'>
                {
                    chatlog.map((message, index) => (
                        <div key={index} className={index % 2 === 0 ? 'player-guess' : 'player-guess alt'}>
                            <p><span className='name'>{message.player_name}:</span> {message.text}</p>
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