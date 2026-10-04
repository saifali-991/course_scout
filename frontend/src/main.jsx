import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App.jsx';
import Discover from './pages/Discover.jsx';
import Categories from './pages/Categories.jsx';
import Saved from './pages/Saved.jsx';
import AdminRedirect from './pages/AdminRedirect.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          <Route path="/" element={<Discover />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/saved" element={<Saved />} />
          {/* Django admin lives on the API origin — this route hands the
              browser over (see pages/AdminRedirect.jsx). Without it, /admin
              on the static host matched nothing and rendered a blank page. */}
          <Route path="/admin" element={<AdminRedirect />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
