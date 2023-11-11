const urlParams = new URLSearchParams(window.location.search);
const room_id = urlParams.get('roomId');  // Replace with your dynamic room ID
  
// Function to get a room
async function getRoom(room_id) {
    try {
      const apiUrl = `http://${window.location.host}/api/${room_id}`;
  
      const response = await fetch(apiUrl, {
        method: 'GET',
      });
  
      // Check if the response is successful
      if (!response.ok) {
        console.error(`Failed to get room. Status: ${response.status}`);
        throw new Error(`Failed to get room. Status: ${response.status}`);
      }
  
      const data = await response.json();
      console.log('Data:', data);
  
      const socket = new WebSocket(`ws://${window.location.host}/ws/game/${data.id}/`);

      socket.onopen = function (event) {
          console.log('WebSocket connection opened:', event);
      };
  
      socket.onmessage = function (event) {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
      };
  
      socket.onclose = function (event) {
          console.log('WebSocket connection closed:', event);
      };
  
      function sendWebSocketMessage(type, text) {
          const data = {
              type,
              text,
          };
          socket.send(JSON.stringify(data));
      }
  
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
          }
      }
  
      function startTimer(){
          socket.send(JSON.stringify({
              'type': 'start_timer'
          }));
      }

      document.getElementById('start').addEventListener('click', startTimer)
      document.getElementById('send_guess').addEventListener('click', function() {
        sendWebSocketMessage('guess', document.getElementById('guess').value);
      });
    } catch (error) {
      console.error('Error getting room:', error.message);
    }
  }

getRoom(room_id)

