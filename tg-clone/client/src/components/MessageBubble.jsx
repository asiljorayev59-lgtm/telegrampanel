import { Check, CheckCheck } from 'lucide-react';

export default function MessageBubble({ msg, mine }) {
  const read = msg.readBy.length > 1;
  return (
    <div className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] md:max-w-[60%] px-3 py-1.5 rounded-2xl shadow-sm ${
          mine ? 'bg-out rounded-br-md' : 'bg-inc rounded-bl-md'
        }`}
      >
        <span className="whitespace-pre-wrap break-words">{msg.text}</span>
        <span className="float-right ml-3 mt-2 text-[11px] text-sub flex items-center gap-0.5">
          {new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          {mine && (read ? <CheckCheck size={14} className="text-accent" /> : <Check size={14} />)}
        </span>
      </div>
    </div>
  );
}
