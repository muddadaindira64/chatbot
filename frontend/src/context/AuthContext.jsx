import { createContext, useContext, useState, useEffect } from 'react';
import axios from '../api/axios';

const AuthContext = createContext(null);
const ACCESS_TOKEN_KEY = 'access_token';
const LEGACY_TOKEN_KEY = 'token';
const USER_STORAGE_KEY = 'user';

const getStoredToken = () => {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY);
};

const storeToken = (token) => {
  if (!token) return;
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
  localStorage.setItem(LEGACY_TOKEN_KEY, token);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const getErrorMessage = (error, fallbackMessage) => {
    const responseData = error.response?.data;

    if (!responseData) {
      return error.message || fallbackMessage;
    }

    if (typeof responseData === 'string') {
      return responseData;
    }

    if (typeof responseData.detail === 'string') {
      return responseData.detail;
    }

    if (Array.isArray(responseData.detail)) {
      return responseData.detail
        .map((item) => item?.msg || item?.message || JSON.stringify(item))
        .join(', ');
    }

    if (typeof responseData.message === 'string') {
      return responseData.message;
    }

    return fallbackMessage;
  };

  useEffect(() => {
    const restoreSession = async () => {
      const token = getStoredToken();
      const storedUser = localStorage.getItem(USER_STORAGE_KEY);

      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch {
          localStorage.removeItem(USER_STORAGE_KEY);
        }
      }

      try {
        const response = await axios.get('/auth/me');
        const currentUser = response.data;
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(currentUser));
        setUser(currentUser);
      } catch (error) {
        if (error.response?.status === 401) {
          localStorage.removeItem(ACCESS_TOKEN_KEY);
          localStorage.removeItem(LEGACY_TOKEN_KEY);
          localStorage.removeItem(USER_STORAGE_KEY);
          setUser(null);
        } else {
          console.error('Session restore failed:', error);
        }
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post('/auth/login', {
        email,
        password,
      });

      const accessToken = response.data?.access_token || response.data?.token;

      if (!accessToken) {
        throw new Error('Missing access token from server');
      }

      storeToken(accessToken);

      const userResponse = await axios.get('/auth/me');
      const userData = userResponse.data;
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
      setUser(userData);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        message: getErrorMessage(error, 'Login failed'),
      };
    }
  };

  const register = async (username, email, password) => {
    try {
      const response = await axios.post('/auth/register', {
        username,
        email,
        password,
      });

      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        message: getErrorMessage(error, 'Registration failed'),
      };
    }
  };

  const logout = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

