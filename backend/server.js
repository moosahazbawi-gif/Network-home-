const express = require("express");
const cors = require("cors");
const pantherGateway = require("./panther-gateway");

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

// Panther AI integration
app.use(pantherGateway);

app.listen(3000, () => console.log("Network-home server running on :3000"));
