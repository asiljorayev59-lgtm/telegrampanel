import mongoose from 'mongoose';
const { Schema, model } = mongoose;

export const User = model('User', new Schema({
  phone: { type: String, unique: true, required: true },
  name: { type: String, required: true },
  username: String,
  bio: String,
  lastSeen: { type: Date, default: Date.now },
}, { timestamps: true }));

export const Chat = model('Chat', new Schema({
  members: [{ type: Schema.Types.ObjectId, ref: 'User' }],
  lastMessage: { type: Schema.Types.ObjectId, ref: 'Message' },
}, { timestamps: true }));

export const Message = model('Message', new Schema({
  chat: { type: Schema.Types.ObjectId, ref: 'Chat', index: true },
  sender: { type: Schema.Types.ObjectId, ref: 'User' },
  text: String,
  fileUrl: String,
  readBy: [{ type: Schema.Types.ObjectId, ref: 'User' }],
}, { timestamps: true }));
