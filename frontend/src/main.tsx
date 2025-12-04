import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'

// Small enhancement: add header shadow on scroll
function InitInteractions() {
  useEffect(() => {
    const handler = () => {
      const header = document.querySelector('.app-header');
      if (header) {
        if (window.scrollY > 4) header.classList.add('has-shadow');
        else header.classList.remove('has-shadow');
      }
    };
    window.addEventListener('scroll', handler, { passive: true });
    handler();
    return () => window.removeEventListener('scroll', handler);
  }, []);
  return null;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <InitInteractions />
      <App />
    </BrowserRouter>
  </StrictMode>,
)