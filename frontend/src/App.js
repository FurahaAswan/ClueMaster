import { BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import JoinGame from './pages/JoinGame'
import PlayGame from './pages/PlayGame';
import CreateGame from './pages/CreateGame';

function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<JoinGame />}></Route>
        <Route path='/play' element={<PlayGame />}></Route>
        <Route path='/create' element={<CreateGame />}></Route>
      </Routes>
    </Router>
  );
}

export default App;
