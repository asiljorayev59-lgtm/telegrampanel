import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, Paperclip, Send, MoreVertical } from 'lucide-react';
import MessageBubble from './MessageBubble';
import { Avatar } from './Sidebar';

export default function ChatWindow({ me, other, messages, typing, onSend, onBack, onProfile, onTyping }) {
  const [text, setText] = useState('');
  const end = useRef(null);

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const submit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text);
    setText('');
  };

  return (
    <section className="flex-1 flex flex-col min-w-0">
      <header className="h-14 bg-panel flex items-center gap-3 px-3 border-b border-line">
        <button onClick={onBack} className="md:hidden p-1"><ArrowLeft /></button>
        <button onClick={onProfile} className="flex items-center gap-3 flex-1 text-left">
          <Avatar name={other.name} size="w-10 h-10" />
          <div>
            <div className="font-medium leading-tight">{other.name}</div>
            <div className="text-xs text-sub">
              {typing
                ? 'yozmoqda...'
                : `oxirgi marta ${new Date(other.lastSeen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
            </div>
          </div>
        </button>
        <MoreVertical className="text-sub" />
      </header>

      <div className="flex-1 overflow-y-auto p-4 space-y-1.5">
        {messages.map((m) => (
          <MessageBubble key={m._id} msg={m} mine={m.sender === me._id} />
        ))}
        <div ref={end} />
      </div>

      <form onSubmit={submit} className="p-3 flex items-end gap-2">
        <div className="flex-1 flex items-center gap-2 bg-panel rounded-2xl px-3 py-2 shadow-sm">
          <button type="button" className="text-sub hover:text-accent"><Paperclip size={22} /></button>
          <input
            value={text}
            onChange={(e) => { setText(e.target.value); onTyping(); }}
            placeholder="Xabar"
            className="flex-1 bg-transparent outline-none"
          />
        </div>
        <button className="w-12 h-12 rounded-full bg-accent text-white grid place-items-center shadow">
          <Send size={20} />
        </button>
      </form>
    </section>
  );
}
