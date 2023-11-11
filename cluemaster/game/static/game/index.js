const roomName = window.location.pathname;  // Replace with your dynamic room ID
const socket = new WebSocket(`ws://${window.location.host}/ws/game${roomName}/`);

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
    }
}