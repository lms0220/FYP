import { Outlet, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import ChatBot from "./ChatBot";
import Navigation from "./Navigation";

export default function Layout() {
  const navigate = useNavigate();

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch("http://localhost:5000/me", {
          credentials: "include",
        });

        if (!response.ok) {
          navigate("/", { replace: true });
        }

      } catch (error) {
        console.error(error);
        navigate("/", { replace: true });
      }
    };

    checkSession();
  }, [navigate]);


  useEffect(() => {

    const handlePageShow = () => {
      fetch("http://localhost:5000/me", {
        credentials: "include",
      })
      .then((res) => {
        if (!res.ok) {
          navigate("/", { replace: true });
        }
      });
    };


    window.addEventListener(
      "pageshow",
      handlePageShow
    );


    return () => {
      window.removeEventListener(
        "pageshow",
        handlePageShow
      );
    };

  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      <ChatBot />
    </div>
  );
}