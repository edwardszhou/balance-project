import express from "express";
import { config } from "dotenv";
import { connectDB } from "./db.js";
import { appSessionRouter, optitrackSessionRouter } from "./routes.js";

config();

const app = express();
app.use(express.json({ limit: "50mb" }));

app.get("/test", async (req, res) => {
  res.json({ message: "Status: Healthy" });
});
app.use("/app-sessions", appSessionRouter);
app.use("/optitrack-sessions", optitrackSessionRouter);

const PORT = process.env.PORT || 3000;

async function start() {
  await connectDB();
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

start();
