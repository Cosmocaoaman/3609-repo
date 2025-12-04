import 'bootstrap/dist/css/bootstrap.min.css'
import './styles/index.css'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './routes/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import OtpPage from './pages/OtpPage'
import ThreadsListPage from './pages/ThreadsListPage'
import ThreadDetailPage from './pages/ThreadDetailPage'
import ThreadCreatePage from './pages/ThreadCreatePage'
// import SearchPage from './pages/SearchPage'
import AdminPanel from './pages/AdminPanel'
import UserProfilePage from './pages/UserProfilePage'
import { BrowsingHistoryPage, LikedPostsPage, ProfileSettingsPage } from './pages/ProfilePlaceholders'
import MyContentPage from './pages/MyContentPage'
import AppHeader from './components/AppHeader'
import { useLocation } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'

function App() {
  const location = useLocation();
  const hideHeader = location.pathname === '/login' || location.pathname === '/otp';
  return (
    <div className="app-layout">
      <ThemeProvider>
        <AuthProvider>
          {!hideHeader && <AppHeader />}
          <main className="app-main">
            <div className="centered-container">
              <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/otp" element={<OtpPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Navigate to="/threads" replace />} />
            <Route path="/threads" element={<ThreadsListPage />} />
            <Route path="/threads/new" element={<ThreadCreatePage />} />
            <Route path="/threads/:id" element={<ThreadDetailPage />} />
            {false && <Route path="/search" element={<div />} />}
          <Route path="/me" element={<UserProfilePage />} />
          <Route path="/me/content" element={<MyContentPage />} />
          <Route path="/profile/history" element={<BrowsingHistoryPage />} />
          <Route path="/profile/likes" element={<LikedPostsPage />} />
          <Route path="/profile/settings" element={<ProfileSettingsPage />} />
            <Route path="/admin" element={<AdminPanel />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>
          </main>
        </AuthProvider>
      </ThemeProvider>
    </div>
  )
}

export default App
