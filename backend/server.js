import express from "express";
import { config } from "dotenv";
import { connectDB } from "./db.js";
import sessionRoute from "./routes/sessions.js"

config();

const app = express();
app.use(express.json());

app.get("/test", async (req, res) => {
  res.json({ message: "Testing" });
});
app.use("/sessions", sessionRoute);

const PORT = process.env.PORT || 3000;

async function start() {
  await connectDB();
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

start();
