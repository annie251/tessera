import React from 'react'; 
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import EventsPage from './pages/EventsPage';
import EventDetail from './pages/EventDetail';
import LoginPage from './pages/LoginPage';

function App() {
  return (
    <ChakraProvider>
      <Router>
        <ConditionalNavBar/>
        <Routes>
          <Route path="/events" element={<EventsPage/>}/>
          
          <Route path="/" element={<Navigate to="/events" replace/>}/>
          <Route path="/events/:id" element={<EventDetail/>}/>
          <Route path="/login" element={<LoginPage/>}/>
        </Routes>
      </Router>
    </ChakraProvider>
  )
}

function ConditionalNavBar() {
  const location = useLocation()

  const showNav = location.pathname.startsWith("/events")

  return showNav? <Navbar/> : null;
}

export default App;



