const path = require("path");
const express = require("express");
const packageJson = require("./package.json");

const app = express();
const PORT = 3000;

app.get("/api/hello", (_req, res) => {
  res.json({ message: "Hello, World!" });
});

app.get("/api/status", (_req, res) => {
  res.json({ version: packageJson.version });
});

app.use(express.static(path.join(__dirname, "public")));

app.listen(PORT, () => {
  console.log(`Server listening on http://127.0.0.1:${PORT}`);
});
