import { useEffect, useRef, useState } from 'react';
import { api, connectSocket } from './api';
import AuthPage from './components/AuthPage';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import RightPanel from './components/RightPanel';

export default function App() {
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(!!localStorage.getItem('token'));
  const [chats, setChats] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [typing, setTyping] = useState(false);
  const [showRight, setShowRight] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const socket = useRef(null);
  const activeRef = useRef(null);
  const typingTimer = useRef(null);
  activeRef.current = active;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const loadChats = () => api('/chats').then(setChats).catch(() => {});

  useEffect(() => {
    if (!localStorage.getItem('token')) return;
    api('/me')
      .then(setMe)
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!me) return;
    loadChats();
    const s = (socket.current = connectSocket());

    s.on('message:new', (msg) => {
      if (activeRef.current?._id === msg.chat) {
        setMessages((m) => (m.some((x) => x._id === msg._id) ? m : [...m, msg]));
        if (msg.sender !== me._id) s.emit('message:read', { chatId: msg.chat });
      }
      loadChats();
    });

    s.on('message:read', ({ chatId, userId }) => {
      if (activeRef.current?._id === chatId)
        setMessages((ms) =>
          ms.map((m) => (m.readBy.includes(userId) ? m : { ...m, readBy: [...m.readBy, userId] }))
        );
      loadChats();
    });

    s.on('typing', ({ chatId }) => {
      if (activeRef.current?._id !== chatId) return;
      setTyping(true);
      clearTimeout(typingTimer.current);
      typingTimer.current = setTimeout(() => setTyping(false), 2000);
    });

    return () => s.disconnect();
  }, [me]);

  const openChat = async (chat) => {
    setActive(chat);
    setTyping(false);
    setMessages(await api(`/chats/${chat._id}/messages`));
    socket.current.emit('message:read', { chatId: chat._id });
    loadChats();
  };

  const send = (text) => socket.current.emit('message:send', { chatId: active._id, text });

  const startChat = async (userId) => {
    const chat = await api('/chats', { method: 'POST', body: { userId } });
    await loadChats();
    openChat(chat);
  };

  if (loading) return <div className="h-full grid place-items-center text-sub">Yuklanmoqda...</div>;
  if (!me) return <AuthPage onAuth={setMe} />;

  const other = active?.members.find((m) => m._id !== me._id);

  return (
    <div className="h-full flex overflow-hidden">
      <div className={`${active ? 'hidden md:flex' : 'flex'} w-full md:w-[22rem] flex-shrink-0`}>
        <Sidebar
          me={me}
          chats={chats}
          activeId={active?._id}
          onOpen={openChat}
          onStart={startChat}
          theme={theme}
          toggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          onLogout={() => { localStorage.removeItem('token'); socket.current?.disconnect(); setMe(null); setActive(null); }}
        />
      </div>

      <div className={`${active ? 'flex' : 'hidden md:flex'} flex-1 min-w-0`}>
        {active ? (
          <ChatWindow
            me={me}
            other={other}
            messages={messages}
            typing={typing}
            onSend={send}
            onBack={() => setActive(null)}
            onProfile={() => setShowRight(!showRight)}
            onTyping={() => socket.current.emit('typing', { chatId: active._id, to: other._id })}
          />
        ) : (
          <div className="flex-1 grid place-items-center text-sub">
            <span className="bg-panel/60 px-4 py-1 rounded-full text-sm">Suhbatni boshlash uchun chatni tanlang</span>
          </div>
        )}
      </div>

      {showRight && active && <RightPanel user={other} onClose={() => setShowRight(false)} />}
    </div>
  );
}
