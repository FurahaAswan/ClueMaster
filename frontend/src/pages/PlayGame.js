import React, { useEffect, useContext, useRef, useState} from 'react'
import { useNavigate } from 'react-router-dom';
import { StateContext } from '../components/StateProvider';
import '../styles/game.css';
import clipboard from 'clipboard-copy';
import axios from 'axios';
import { ring2 } from 'ldrs'
ring2.register()

const PlayGame = ()=> {

    const { 
        client,
        player, 
        roomId, 
        roomName, 
        rounds, 
        guessTime, 
        maxPlayers, 
        category, 
        difficulty 
    } = useContext(StateContext);
    const [timer, setTimer] = useState(guessTime);
    const [guess, setGuess] = useState('')
    const navigate = useNavigate();
    const socketRef = useRef(null);
    const [chatlog, setChatLog] = useState([]);
    const [wordToGuess, setWordToGuess] = useState("");
    const [players, setPlayers] = useState([]);
    const [clues, setClues] = useState([]);
    const [host, setHost] = useState();
    const [gameActive, setGameActive] = useState(false);
    const [formData, setFormData] = useState({
        name: roomName,
        rounds: rounds,
        guess_time: guessTime,
        max_players: maxPlayers,
        category: category, // Add category field
        difficulty: difficulty, // Add difficulty field with default value
      });
    const [timeStamp, setTimeStamp] = useState(0);
    const messagesRef = useRef(null);
    const [loading, setLoading] = useState(true);

   

    // Default values shown

    useEffect(() => {
        console.log('Chat Log updated:', chatlog);
    }, [chatlog]);

    useEffect(() => {

        if (!player || !roomId){
            navigate('/')
        } else{
            console.log('Player', player)

        socketRef.current = new WebSocket(`ws://${window.location.host}/ws/game/${roomId}/${player.id}`)
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

        }
        
    }, []);

        function handleWebSocketMessage(data) {
            console.log('handle')
            // Handle different types of messages here
            if (data.type === 'loading_state'){
                console.log('Loading state', data.loading_state);
                setLoading(data.loading_state);
            }else if(data.type === 'guess'){
                console.log('Received guess:', data);
                setChatLog(prevChatLog => [...prevChatLog, data]);
                messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
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
                setHost(data.host); // Ensure that 'host' is not null
                setTimer(data.unix_time);
                setTimeStamp(data.expiration_timestamp);
                setGameActive(data.game_active);
                setLoading(data.loading_state);
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
        
        function sendGuess(e) {
            e.preventDefault();
            if (socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({
                    'type': 'guess',
                    'text': guess,
                    'player': player.id,
                    'time': new Date().getTime() / 1000
                }));
            }
            setGuess('');
        }
        

        function copyInviteLink() {
            clipboard(window.location.host+`?roomId=${roomId}`);
        }

        const generateOptions = (min, max, interval) => {
            const options = [];
            for (let i = min; i <= max; i += interval) {
              options.push(<option key={i} value={i}>{i}</option>);
            }
            return options;
        };

        const handleChange = (e) => {
            setFormData({ ...formData, [e.target.name]: e.target.value });
        };

        const handleSubmit = async (e) => {
            try {
                e.preventDefault();
                console.log('Form Data', formData)
                const response = await client.put(`api/room/update/${roomId}`, formData);
                console.log('Room Updated successfully:', response.data);
                startRound();
            } catch (error) {
              console.error('Error creating room:', error);
            }
        };
    
        // Assuming timestamp is the Unix timestamp received from the server
        const calculateTimeLeft = () => {
            const now = new Date().getTime() / 1000;
            const timeLeft = Math.max(0, Math.floor((timeStamp - now))); // in seconds
            return timeLeft;
        };
        
        // Use useEffect to update the timer every second
        useEffect(() => {
            const interval = gameActive && setInterval(() => {
              const timeLeft = calculateTimeLeft();
              // Update your UI with the remaining time
              setTimer(timeLeft)
            }, 1000);
          
            return () => clearInterval(interval);
          }, [timeStamp, gameActive]);
        

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
                    loading ? 
                        <l-ring-2
                        size="40"
                        stroke="5"
                        stroke-length="0.25"
                        bg-opacity="0.1"
                        speed="0.8" 
                        color="black" 
                        ></l-ring-2>
                    :
                    clues.map((clue, index) => (
                        <h1 key={index} className='clue'>{index+1}. {clue}</h1>
                    ))
                }
                {
                    !loading &&
                    <div className={host && player && host.id === player.id ? 'options' : 'hide'}>
                    {!gameActive && 
                        <div className='update-container'>
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
                              <option value="enthusiast">Enthusiast</option>
                              <option value="expert">Expert</option>
                            </select>
                          </label>
                          <button className='link' type='button' onClick={copyInviteLink}>Click to get Invite Link</button>
                          <button className='start' type='submit'>Start</button>
                        </form>
                      </div>
                    }
                </div>
                }
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
                <div ref={messagesRef} className='messages'>
                {
                    chatlog.map((message, index) => (
                        <div key={index} className={index % 2 === 0 ? 'chat-message' : 'chat-message alt'}>
                            {message.type === 'host_update' ? 
                                <p className='host'>message.host.name + ' is the room host'</p> 
                            : message.type === 'player_join' ? 
                                <p className='join'> {message.name} joined the room!</p> 
                            : message.type === 'guess' ? 
                                <p><span className='name'>{message.player_name}:</span> <span style={message.is_correct ? {color: '#4caf50', fontWeight: 'bold'} : {}}>{message.text}</span></p>
                            : message.type === 'player_leave' ? 
                                <p className='leave'>{message.name} left the room</p>
                            :
                                <p>Unknown Message</p>
                            }
                        </div>
                    ))
                }
                </div>
                <form onSubmit={sendGuess} className='user-input'>
                    <input type="text" id="guess" placeholder="Type your guess here" value={guess} onChange={(e) => setGuess(e.target.value)} required/>
                </form>
            </div>
        </div>
    )
};

export default PlayGame