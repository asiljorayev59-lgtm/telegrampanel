import 'dotenv/config';
import express from 'express';
import http from 'http';
import cors from 'cors';
import mongoose from 'mongoose';
import jwt from 'jsonwebtoken';
import { Server } from 'socket.io';
import authRoutes from './auth.js';
import routes from './routes.js';
import { Chat, Message, User } from './models.js';

const app = express();
app.use(cors({ origin: true }));
app.use(express.json({ limit: '1mb' }));
app.use('/api/auth', authRoutes);
app.use('/api', routes);
app.get('/health', (_, res) => res.send('ok'));

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: true } });

io.use((socket, next) => {
  try {
    socket.userId = jwt.verify(socket.handshake.auth.token, process.env.JWT_SECRET).id;
    next();
  } catch {
    next(new Error('unauthorized'));
  }
});

const online = new Set();

io.on('connection', (socket) => {
  const uid = socket.userId;
  socket.join(`user:${uid}`);
  online.add(uid);
  io.emit('presence', { userId: uid, online: true });

  socket.on('message:send', async ({ chatId, text }, ack) => {
    const chat = await Chat.findOne({ _id: chatId, members: uid });
    if (!chat || !text?.trim()) return;
    const msg = await Message.create({ chat: chatId, sender: uid, text: text.trim(), readBy: [uid] });
    chat.lastMessage = msg._id;
    await chat.save();
    chat.members.forEach((m) => io.to(`user:${m}`).emit('message:new', msg));
    ack?.(msg);
  });

  socket.on('message:read', async ({ chatId }) => {
    const chat = await Chat.findOne({ _id: chatId, members: uid });
    if (!chat) return;
    await Message.updateMany({ chat: chatId, readBy: { $ne: uid } }, { $addToSet: { readBy: uid } });
    chat.members.forEach((m) => io.to(`user:${m}`).emit('message:read', { chatId, userId: uid }));
  });

  socket.on('typing', ({ chatId, to }) => io.to(`user:${to}`).emit('typing', { chatId, userId: uid }));

  socket.on('disconnect', async () => {
    online.delete(uid);
    await User.findByIdAndUpdate(uid, { lastSeen: new Date() });
    io.emit('presence', { userId: uid, online: false });
  });
});

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => server.listen(process.env.PORT, () => console.log('Server ishga tushdi: http://localhost:' + process.env.PORT)))
  .catch((e) => { console.error('MongoDB xatosi:', e.message); process.exit(1); });
