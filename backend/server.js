const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

let data = [];

app.post("/api/request", (req, res) => {
  data.push(req.body);
  res.json({ ok: true });
});

app.get("/api/requests", (req, res) => {
  res.json(data);
});

app.listen(3000, () => console.log("Server running"));