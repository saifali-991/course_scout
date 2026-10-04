import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App.jsx';
import Discover from './pages/Discover.jsx';
import Categories from './pages/Categories.jsx';
import Saved from './pages/Saved.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          <Route path="/" element={<Discover />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/saved" element={<Saved />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
