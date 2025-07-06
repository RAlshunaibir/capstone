import { useState, createContext, useContext, useEffect } from 'react'
import AuthForm from './components/AuthForm'
import Chat from './components/Chat'
import { API_ENDPOINTS } from './config'
import './App.css'

// Create theme context
const ThemeContext = createContext()

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  )
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('theme')
    return savedTheme || 'dark'
  })
  const [currentUser, setCurrentUser] = useState(null)
  const [showUserMenu, setShowUserMenu] = useState(false)

  // Logout function
  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
    setCurrentUser(null)
    setShowUserMenu(false)
  }

  // Theme toggle function
  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    document.body.className = newTheme
  }

  // Set initial theme
  useEffect(() => {
    document.body.className = theme
  }, [theme])

  // Get current user info from backend
  const getCurrentUserInfo = async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(API_ENDPOINTS.ME, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const userData = await response.json()
        setCurrentUser({
          username: userData.username,
          access_token: token
        })
      } else {
        // Token is invalid, logout
        handleLogout()
      }
    } catch (error) {
      console.error('Error fetching user info:', error)
      handleLogout()
    }
  }

  // Handle successful authentication
  const handleAuthSuccess = (userData) => {
    setIsAuthenticated(true)
    setCurrentUser(userData)
  }

  // Load user info on app start
  useEffect(() => {
    if (isAuthenticated) {
      getCurrentUserInfo()
    }
  }, [isAuthenticated])

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.user-menu-container')) {
        setShowUserMenu(false)
      }
    }

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showUserMenu])

  // Wrapper for Chat to handle auth errors
  const ChatWithAuthCheck = () => (
    <Chat
      onAuthError={() => {
        handleLogout()
      }}
    />
  )

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <div className={`app-wrapper ${theme}`}>
        <div className="topbar">
                  <div className="topbar-content">
          <span>Rakan's Chatbot</span>
          <div className="topbar-actions">
              {isAuthenticated && (
                <button
                  className="theme-toggle-btn"
                  onClick={toggleTheme}
                  title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                >
                  {theme === 'dark' ? '☀️' : '🌙'}
                </button>
              )}
              {isAuthenticated && currentUser && (
                <div className="user-menu-container">
                  <button
                    className="username-btn"
                    onClick={() => setShowUserMenu(!showUserMenu)}
                  >
                    {currentUser.username}
                  </button>
                  {showUserMenu && (
                    <div className="user-dropdown">
                      <button
                        className="logout-btn-red"
                        onClick={handleLogout}
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        {!isAuthenticated ? (
          <AuthForm onAuthSuccess={handleAuthSuccess} />
        ) : (
          <ChatWithAuthCheck />
        )}
      </div>
    </ThemeContext.Provider>
  )
}

export default App
