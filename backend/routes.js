import express from "express";
import { getDB } from "./db.js";

function createPostRoute(collection) {
  return async (req, res) => {
    try {
      const session = req.body;
      if (!session || typeof session !== "object") {
        return res.status(400).json({ message: "Invalid session JSON" });
      }
      const db = getDB();
      const result = await db.collection(collection).insertOne(session);
      console.log(`Inserted session with _id: ${result.insertedId}`);
      res.json({ id: result.insertedId });
    } catch (err) {
      res.status(500).json({ message: err.message });
    }
  };
}

function createGetRoute(collection) {
  return async (req, res) => {
    try {
      const db = getDB();
      const { user, sortBy = "startDate", limit = "50" } = req.query;

      const filter = user ? { user } : {};

      const cursor = db
        .collection(collection)
        .find(filter)
        .sort({ [sortBy]: -1 })
        .limit(parseInt(limit));

      const sessions = await cursor.toArray();
      res.json(sessions);
    } catch (err) {
      res.status(500).json({ message: err.message });
    }
  };
}

const appSessionRouter = express.Router();
appSessionRouter.get("/", createGetRoute("appsessions"));
appSessionRouter.post("/", createPostRoute("appsessions"));

const optitrackSessionRouter = express.Router();
optitrackSessionRouter.get("/", createGetRoute("optitracksessions"));
optitrackSessionRouter.post("/", createPostRoute("optitracksessions"));

export { appSessionRouter, optitrackSessionRouter };
