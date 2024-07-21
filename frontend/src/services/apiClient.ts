import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api", // todo replace with API base URL
  headers: {
    "Content-Type": "application/json",
  },
});

export default apiClient;
