import { Router } from 'express';
import { requireAuth } from './auth.js';
import { User, Chat, Message } from './models.js';

const r = Router();
r.use(requireAuth);

r.get('/me', async (req, res) => {
  const u = await User.findById(req.userId);
  if (!u) return res.status(401).json({ error: 'Unauthorized' });
  res.json(u);
});

r.get('/users/search', async (req, res) => {
  const q = String(req.query.q || '').trim();
  if (!q) return res.json([]);
  const rx = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
  res.json(
    await User.find({ _id: { $ne: req.userId }, $or: [{ name: rx }, { phone: rx }, { username: rx }] }).limit(20)
  );
});

r.get('/chats', async (req, res) => {
  const chats = await Chat.find({ members: req.userId })
    .populate('members')
    .populate('lastMessage')
    .sort({ updatedAt: -1 })
    .lean();
  for (const c of chats) {
    c.unread = await Message.countDocuments({
      chat: c._id,
      sender: { $ne: req.userId },
      readBy: { $ne: req.userId },
    });
  }
  res.json(chats);
});

r.post('/chats', async (req, res) => {
  const { userId } = req.body;
  let chat = await Chat.findOne({ members: { $all: [req.userId, userId], $size: 2 } });
  if (!chat) chat = await Chat.create({ members: [req.userId, userId] });
  res.json(await chat.populate('members'));
});

r.get('/chats/:id/messages', async (req, res) => {
  const chat = await Chat.findOne({ _id: req.params.id, members: req.userId });
  if (!chat) return res.status(403).end();
  res.json(await Message.find({ chat: chat._id }).sort({ createdAt: 1 }).limit(300));
});

export default r;
