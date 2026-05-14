// Import required modules
const express = require("express");
const app = express();
const db = require("./db");
const bcrypt = require("bcrypt");
const dotenv = require("dotenv");

// Load environment variables
dotenv.config();

// Define a secure secret
const SECRET = process.env.SECRET;

// Use express.json middleware to parse JSON bodies
app.use(express.json());

// Define a function to calculate the sum of an array
/**
 * Calculates the sum of an array of numbers.
 * @param {number[]} arr - The input array.
 * @returns {number} The sum of the array.
 */
function calculateSum(arr) {
  // Check if the input array is null or undefined
  if (arr === null || arr === undefined) {
    throw new Error("Input array is null or undefined");
  }

  let sum = 0;
  // Iterate over the array using a for loop
  for (let i = 0; i < arr.length; i++) {
    // Add each element to the sum
    sum += arr[i];
  }
  return sum;
}

// Define a route handler for the /user endpoint
app.get("/user", async (req, res) => {
  try {
    // Get the id query parameter
    const id = req.query.id;

    // Check if the id parameter is valid
    if (id === null || id === undefined) {
      res.status(400).json({ error: "Invalid id parameter" });
      return;
    }

    // Use a parameterized query to prevent SQL injection
    const user = await db.query("SELECT * FROM users WHERE id = $1", [id]);

    // Check if the user exists
    if (user.length === 0) {
      res.status(404).json({ error: "User not found" });
      return;
    }

    // Return the user data
    res.json(user);
  } catch (error) {
    // Handle any errors that occur during the database query
    console.error(error);
    res.status(500).json({ error: "Internal server error" });
  }
});

// Define a route handler for the /login endpoint
app.post("/login", async (req, res) => {
  try {
    // Get the username and password from the request body
    const username = req.body.username;
    const password = req.body.password;

    // Check if the username and password are valid
    if (username === null || username === undefined || password === null || password === undefined) {
      res.status(400).json({ error: "Invalid username or password" });
      return;
    }

    // Hash the password for secure comparison
    const hashedPassword = await bcrypt.hash(password, 10);

    // Compare the hashed password with the stored secret
    const isValid = await bcrypt.compare(password, SECRET);

    // Check if the credentials are valid
    if (username === "admin" && isValid) {
      res.send("logged in");
    } else {
      res.send("wrong");
    }
  } catch (error) {
    // Handle any errors that occur during the login process
    console.error(error);
    res.status(500).json({ error: "Internal server error" });
  }
});

// Start the server
const port = 3000;
app.listen(port, () => {
  console.log(`Server started on port ${port}`);
});