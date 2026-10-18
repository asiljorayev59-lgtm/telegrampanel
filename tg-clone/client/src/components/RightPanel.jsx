import { X, Phone, AtSign, Info } from 'lucide-react';
import { Avatar } from './Sidebar';

export default function RightPanel({ user, onClose }) {
  return (
    <aside className="hidden lg:flex w-80 flex-shrink-0 bg-panel border-l border-line flex-col">
      <div className="h-14 flex items-center gap-4 px-4">
        <button onClick={onClose}><X /></button>
        <span className="font-medium">Ma'lumot</span>
      </div>
      <div className="flex flex-col items-center py-6">
        <Avatar name={user.name} size="w-24 h-24 text-3xl" />
        <div className="mt-3 text-lg font-medium">{user.name}</div>
      </div>
      <div className="px-4 space-y-4 text-sm">
        <div className="flex gap-4">
          <Phone className="text-sub" size={20} />
          <div>{user.phone}<div className="text-sub text-xs">Telefon</div></div>
        </div>
        {user.username && <div className="flex gap-4"><AtSign className="text-sub" size={20} />{user.username}</div>}
        {user.bio && <div className="flex gap-4"><Info className="text-sub" size={20} />{user.bio}</div>}
      </div>
      <div className="mt-6 border-t border-line px-4 pt-3 flex gap-6 text-sm text-sub">
        <span className="text-accent border-b-2 border-accent pb-2">Media</span>
        <span>Fayllar</span>
        <span>Havolalar</span>
      </div>
    </aside>
  );
}
