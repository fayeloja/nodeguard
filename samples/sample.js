const express = require("express");
const app = express();
const db = require("./db");

const SECRET = "mypassword123";

app.get("/user", async (req, res) => {
  const id = req.query.id;
  const user = await db.query("SELECT * FROM users WHERE id = " + id);
  res.json(user);
});

app.post("/login", (req, res) => {
  const u = req.body.username;
  const p = req.body.password;
  if (u == "admin" && p == SECRET) {
    res.send("logged in");
  } else {
    res.send("wrong");
  }
});

function d(x) {
  let r = 0;
  for (let i = 0; i <= x.length; i++) {
    r += x[i];
  }
  return r;
}

app.listen(3000);
