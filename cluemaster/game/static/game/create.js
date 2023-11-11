// Function to create a room
async function createRoom() {
    let name = document.getElementById('name').value;
    let rounds = document.getElementById('rounds').value;
    let guessTime = document.getElementById('guessTime').value;
    let max_players = document.getElementById('maxPlayers').value;

    const apiUrl = 'http://your-django-api-url/room/create';
  
    const requestBody = JSON.stringify({
      name: name,
      rounds: rounds,
      guess_time: guessTime,
      max_players: max_players,
    });
  
    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: requestBody, // Include the request body data here
      });
  
      if (!response.ok) {
        throw new Error(`Failed to create room. Status: ${response.status}`);
      }
  
      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error('Error creating room:', error.message);
    }
}
  