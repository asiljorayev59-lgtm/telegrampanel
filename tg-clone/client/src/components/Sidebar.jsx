import { useEffect, useState } from 'react';
import { Search, Moon, Sun, Check, CheckCheck, LogOut } from 'lucide-react';
import { api } from '../api';

const time = (d) => new Date(d).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export const Avatar = ({ name, size = 'w-12 h-12' }) => (
  <div className={`${size} rounded-full bg-accent text-white grid place-items-center font-medium flex-shrink-0`}>
    {name?.[0]?.toUpperCase()}
  </div>
);

export default function Sidebar({ me, chats, activeId, onOpen, onStart, theme, toggleTheme, onLogout }) {
  const [q, setQ] = useState('');
  const [found, setFound] = useState([]);

  useEffect(() => {
    if (!q) return setFound([]);
    const t = setTimeout(() => api(`/users/search?q=${encodeURIComponent(q)}`).then(setFound).catch(() => {}), 300);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <aside className="w-full bg-panel flex flex-col border-r border-line">
      <div className="flex items-center gap-1 p-3">
        <div className="flex-1 flex items-center gap-2 bg-hover rounded-full px-4 py-2">
          <Search size={18} className="text-sub" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Qidirish"
            className="bg-transparent outline-none flex-1 text-sm"
          />
        </div>
        <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-hover text-sub" title="Mavzu">
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <button onClick={onLogout} className="p-2 rounded-full hover:bg-hover text-sub" title="Chiqish">
          <LogOut size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {q ? (
          found.length === 0 ? (
            <p className="text-center text-sub text-sm mt-6">Hech narsa topilmadi</p>
          ) : (
            found.map((u) => (
              <button
                key={u._id}
                onClick={() => { onStart(u._id); setQ(''); }}
                className="w-full flex items-center gap-3 px-3 py-2 hover:bg-hover text-left"
              >
                <Avatar name={u.name} />
                <div>
                  <div className="font-medium">{u.name}</div>
                  <div className="text-sm text-sub">{u.phone}</div>
                </div>
              </button>
            ))
          )
        ) : (
          chats.map((c) => {
            const other = c.members.find((m) => m._id !== me._id);
            const last = c.lastMessage;
            const mine = last?.sender === me._id;
            const read = last?.readBy?.length > 1;
            const isActive = activeId === c._id;
            return (
              <button
                key={c._id}
                onClick={() => onOpen(c)}
                className={`w-full flex items-center gap-3 px-3 py-2 text-left ${isActive ? 'bg-accent text-white' : 'hover:bg-hover'}`}
              >
                <Avatar name={other?.name} />
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between">
                    <span className="font-medium truncate">{other?.name}</span>
                    <span className={`text-xs flex items-center gap-1 ${isActive ? 'text-white/80' : 'text-sub'}`}>
                      {mine && (read ? <CheckCheck size={14} /> : <Check size={14} />)}
                      {last && time(last.createdAt)}
                    </span>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className={`text-sm truncate ${isActive ? 'text-white/80' : 'text-sub'}`}>{last?.text}</span>
                    {c.unread > 0 && (
                      <span className="bg-accent text-white text-xs rounded-full min-w-5 h-5 px-1.5 grid place-items-center">
                        {c.unread}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
