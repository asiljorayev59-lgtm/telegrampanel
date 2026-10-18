import jwt from 'jsonwebtoken';
import { Router } from 'express';
import { User } from './models.js';

const codes = new Map(); // phone -> { code, exp }

export const sign = (u) =>
  jwt.sign({ id: u._id }, process.env.JWT_SECRET, { expiresIn: '30d' });

export const requireAuth = (req, res, next) => {
  try {
    const t = (req.headers.authorization || '').replace('Bearer ', '');
    req.userId = jwt.verify(t, process.env.JWT_SECRET).id;
    next();
  } catch {
    res.status(401).json({ error: 'Unauthorized' });
  }
};

const r = Router();

r.post('/request-code', (req, res) => {
  const phone = String(req.body.phone || '').replace(/\D/g, '');
  if (phone.length < 9) return res.status(400).json({ error: "Telefon raqam noto'g'ri" });
  const code = String(Math.floor(10000 + Math.random() * 90000));
  codes.set(phone, { code, exp: Date.now() + 5 * 60_000 });
  console.log(`[DEV SMS] ${phone} -> kod: ${code}`);
  res.json({ ok: true, devCode: process.env.NODE_ENV !== 'production' ? code : undefined });
});

r.post('/verify', async (req, res) => {
  const phone = String(req.body.phone || '').replace(/\D/g, '');
  const rec = codes.get(phone);
  if (!rec || rec.exp < Date.now() || rec.code !== String(req.body.code))
    return res.status(400).json({ error: "Kod noto'g'ri yoki eskirgan" });
  codes.delete(phone);
  let user = await User.findOne({ phone });
  if (!user) user = await User.create({ phone, name: req.body.name?.trim() || `User ${phone.slice(-4)}` });
  res.json({ token: sign(user), user });
});

export default r;
