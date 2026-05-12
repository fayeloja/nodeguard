// src/modules/auth/auth.service.js

const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const authRepository = require("./auth.repository");
const { ConflictError, UnauthorizedError } = require("../../shared/errors");

const SALT_ROUNDS = 12;

exports.register = async ({
  business_name,
  first_name,
  last_name,
  email,
  password,
  phone,
}) => {
  // 1. Check if email already exists
  const existingUser = await authRepository.findByEmail(email);

  if (existingUser) {
    throw new ConflictError("An account with this email already exists");
  }

  // 2. Hash password
  const password_hash = await bcrypt.hash(password, SALT_ROUNDS);

  // 3. Create user and organization
  const newAccount = await authRepository.createUser({
    business_name,
    first_name,
    last_name,
    email,
    phone,
    password_hash,
  });

  return newAccount;
};

exports.login = async ({ email, password }) => {
  // 1. Find user — use a vague error to avoid user-enumeration attacks
  const user = await authRepository.findByEmail(email);

  if (!user || !user.is_active) {
    throw new UnauthorizedError("Invalid email or password");
  }

  // 2. Validate password
  const isPasswordValid = await bcrypt.compare(password, user.password_hash);

  if (!isPasswordValid) {
    throw new UnauthorizedError("Invalid email or password");
  }

  // 3. Generate JWT
  const token = jwt.sign(
    { 
      user_id: user.id, 
      org_id: user.org_id, 
      role: user.role, 
      email: user.email 
    },
    process.env.JWT_SECRET,
    { expiresIn: "15m" }, // Access token: 15 min per AGENTS.md
  );

  return {
    token,
    user: {
      id: user.id,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
    },
    organization: {
      id: user.org_id,
      business_name: user.business_name,
    }
  };
};
