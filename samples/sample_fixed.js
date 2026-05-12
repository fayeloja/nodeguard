// Import required modules
const express = require("express");
const app = express();
const db = require("./db");

// Store sensitive data as environment variables
const SECRET = process.env.SECRET;

// Use a secure method to parse JSON bodies
app.use(express.json());

// Define a function to calculate the sum of an array
/**
 * Calculates the sum of an array.
 * @param {number[]} array - The array to calculate the sum of.
 * @returns {number} The sum of the array.
 */
function calculateSum(array) {
  let result = 0;
  // Loop through the array, avoiding out-of-bounds access
  for (let i = 0; i < array.length; i++) {
    result += array[i];
  }
  return result;
}

// Define a function to query the database securely
/**
 * Queries the database for a user by ID.
 * @param {number} id - The ID of the user to query.
 * @returns {Promise<object>} A promise resolving to the user object.
 */
async function getUserById(id) {
  try {
    // Use a parameterized query to prevent SQL injection
    const user = await db.query("SELECT * FROM users WHERE id = $1", [id]);
    return user;
  } catch (error) {
    // Handle database query errors
    console.error("Error querying database:", error);
    throw error;
  }
}

// Define a function to authenticate a user
/**
 * Authenticates a user with the given username and password.
 * @param {string} username - The username to authenticate.
 * @param {string} password - The password to authenticate.
 * @returns {boolean} Whether the authentication was successful.
 */
function authenticateUser(username, password) {
  // Use a secure method to compare the password
  return username === "admin" && password === SECRET;
}

// Define the /user endpoint
app.get("/user", async (req, res) => {
  try {
    // Get the user ID from the query parameter
    const id = req.query.id;
    // Validate the user ID
    if (!id || isNaN(id)) {
      res.status(400).send("Invalid user ID");
      return;
    }
    // Query the database for the user
    const user = await getUserById(id);
    // Return the user object, excluding sensitive information
    res.json({ id: user.id, username: user.username });
  } catch (error) {
    // Handle errors
    console.error("Error handling /user request:", error);
    res.status(500).send("Internal Server Error");
  }
});

// Define the /login endpoint
app.post("/login", async (req, res) => {
  try {
    // Get the username and password from the request body
    const { username, password } = req.body;
    // Validate the username and password
    if (!username || !password) {
      res.status(400).send("Invalid username or password");
      return;
    }
    // Authenticate the user
    if (authenticateUser(username, password)) {
      res.send("logged in");
    } else {
      res.send("wrong");
    }
  } catch (error) {
    // Handle errors
    console.error("Error handling /login request:", error);
    res.status(500).send("Internal Server Error");
  }
});

// Start the server
const port = 3000;
app.listen(port, () => {
  console.log(`Server started on port ${port}`);
});