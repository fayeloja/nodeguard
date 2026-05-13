import * as dotenv from "dotenv";
dotenv.config();
import express from "express";
const app = express();
import morgan from "morgan";
import { nanoid } from "nanoid";

let jobs = [
  { id: nanoid(), company: "Company A", position: "Developer" },
  { id: nanoid(), company: "Company B", position: "Designer" },
  { id: nanoid(), company: "Company C", position: "Manager" },
  { id: nanoid(), company: "Company D", position: "Tester" },
  { id: nanoid(), company: "Company E", position: "Developer" },
];

// Conditional logging middleware
if (process.env.NODE_ENV === "development") {
  console.log("Morgan enabled");
  app.use(morgan("dev"));
}

// Middleware to parse JSON bodies
app.use(express.json());

app.get("/", (req, res) => {
  res.send("Hello, Jobify!");
});

app.post("/", (req, res) => {
  // Placeholder for future POST request handling
  console.log(req);
  res.json({ message: "Data received", data: req.body });
});

//GET ALL JOBS
app.get("/api/v1/jobs", (req, res) => {
  res.status(200).json({ jobs });
});

//CREATE A JOBS
app.post("/api/v1/jobs", (req, res) => {
  const { company, position } = req.body;

  if (!company || !position) {
    return res
      .status(400)
      .json({ error: "Please provide company and position" });
  }

  const id = nanoid(10);
  const newJob = { id, company, position };
  jobs.push(newJob);
  res.status(201).json({ newJob });
});

//GET A SINGLE JOB
app.get("/api/v1/jobs/:id", (req, res) => {
  const { id } = req.params;
  const job = jobs.find((job) => job.id === id);

  if (!job) {
    return res.status(404).json({ error: `No job with ${id} found` });
  }

  res.status(200).json({ job });
});

//SERVER LISTENING
const PORT = process.env.PORT || 5100;

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
