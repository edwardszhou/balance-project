import express from "express";
import { getDB } from "../db.js";

const router = express.Router();
router.get("/", async (req, res) => {
  try {
    const db = getDB();
    const { user, sortBy = "startDate", limit = "50" } = req.query;

    const filter = user ? { user } : {};

    const cursor = db
      .collection("sessions")
      .find(filter)
      .sort({ [sortBy]: -1 })
      .limit(parseInt(limit));

    const sessions = await cursor.toArray();
    res.json(sessions);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

router.post("/", async (req, res) => {
  try {
    const session = req.body;
    if (!session || typeof session !== "object") {
      return res.status(400).json({ message: "Invalid session JSON" });
    }
    const db = getDB();
    const result = await db.collection("sessions").insertOne(session);
    console.log(`Inserted session with _id: ${result.insertedId}`);
    res.json({ id: result.insertedId });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

export default router;
