import { createBrowserRouter } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Submission from "./pages/Submission";
import Results from "./pages/Results";
import History from "./pages/History";
import Layout from "./components/Layout";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Login />,
  },
  {
    path: "/register",
    element: <Register />,
  },
  {
    path: "/app",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "submit",
        element: <Submission />,
      },
      {
        path: "results/:id",
        element: <Results />,
      },
      {
        path: "history",
        element: <History />,
      },
    ],
  },
]);
