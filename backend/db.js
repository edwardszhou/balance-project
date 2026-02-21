import { MongoClient } from "mongodb";
import { config } from "dotenv";
import { UUID } from "bson";

config();
const client = new MongoClient(process.env.MONGO_DSN, {
  // pkFactory: { createPk: () => new UUID().toBinary() }
});

let db;

export async function connectDB() {
  await client.connect();
  db = client.db(process.env.DB_NAME);
  console.log("MongoDB connected");
}

export function getDB() {
  return db;
}
