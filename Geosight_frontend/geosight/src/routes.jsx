import { createBrowserRouter, Navigate } from 'react-router-dom';
import App from './App';
import Home from './pages/Home';
import LiveDemo from './pages/LiveDemo';
import ModelInsights from './pages/ModelInsights';
import About from './pages/About';
import Team from './pages/Team';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: 'demo', element: <LiveDemo /> },
      { path: 'insights', element: <ModelInsights /> },
      { path: 'about', element: <About /> },
      { path: 'team', element: <Team /> },
      // Map-based analysis lives on the Live Demo page; keep old links working
      { path: 'map', element: <Navigate to="/demo" replace /> },
      { path: 'map-selector', element: <Navigate to="/demo" replace /> },
      { path: '*', element: <Navigate to="/" replace /> }
    ]
  }
]);
