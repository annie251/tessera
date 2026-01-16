import React from 'react'; 
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import EventsPage from './pages/EventsPage';
import EventDetail from './pages/EventDetail';
import LoginPage from './pages/LoginPage';

function App() {
  return (
    <ChakraProvider>
      <Router>
        
        <Routes>
          <Route path="/events" element={<EventsPage/>}/>
         
          <Route path="/events/:id" element={<EventDetail/>}/>
          <Route path="/" element={<LoginPage/>}/>
        </Routes>
      </Router>
    </ChakraProvider>
  )
}

export default App;

// <Navbar/>
// <Route path="/" element={<Navigate to="/events" replace/>}/>

