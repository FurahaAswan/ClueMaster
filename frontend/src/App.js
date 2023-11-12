import { BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import JoinGame from './pages/JoinGame'
import PlayGame from './pages/PlayGame';

function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<JoinGame />}></Route>
        <Route path='/play' element={<PlayGame />}></Route>
      </Routes>
    </Router>
  );
}

export default App;
