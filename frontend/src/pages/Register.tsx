import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Shield, AlertCircle, CheckCircle } from "lucide-react";

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username) {
      newErrors.username = "Username is required";
    } else if (formData.username.length < 3) {
      newErrors.username = "Username must be at least 3 characters";
    }

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password =
        "Password must contain uppercase, lowercase, and number";
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {

  e.preventDefault();


  if (!validateForm()) return;



  try {


    const response = await fetch(
      "http://localhost:5000/register",
      {

        method:"POST",

        credentials:"include",

        headers:{
          "Content-Type":"application/json"
        },


        body:JSON.stringify({

          username:formData.username,

          email:formData.email,

          password:formData.password

        })

      }
    );



    const data = await response.json();



    if(response.ok){


      alert("Register Success");


      navigate("/");


    }
    else{


      alert(data.message);


    }



  }
  catch(error){

    console.log(error);

    alert("Backend error");

  }

};

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const getInputClassName = (fieldName: string) => {
    return `w-full px-4 py-3 rounded-lg border ${
      errors[fieldName]
        ? "border-red-500 focus:ring-red-500"
        : formData[fieldName as keyof typeof formData]
        ? "border-green-500 focus:ring-green-500"
        : "border-gray-300 focus:ring-indigo-500"
    } focus:ring-2 focus:outline-none transition`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-indigo-600 p-4 rounded-full mb-4">
            <Shield className="size-12 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Create Account
          </h1>
          <p className="text-gray-600 text-center">
            Join Scam Shield AI to stay protected
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className={getInputClassName("username")}
              placeholder="johndoe"
            />
            {errors.username && (
              <div className="flex items-center mt-2 text-red-600 text-sm">
                <AlertCircle className="size-4 mr-1" />
                {errors.username}
              </div>
            )}
            {!errors.username && formData.username.length >= 3 && (
              <div className="flex items-center mt-2 text-green-600 text-sm">
                <CheckCircle className="size-4 mr-1" />
                Username looks good
              </div>
            )}
          </div>

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={getInputClassName("email")}
              placeholder="you@example.com"
            />
            {errors.email && (
              <div className="flex items-center mt-2 text-red-600 text-sm">
                <AlertCircle className="size-4 mr-1" />
                {errors.email}
              </div>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={getInputClassName("password")}
              placeholder="••••••••"
            />
            {errors.password && (
              <div className="flex items-center mt-2 text-red-600 text-sm">
                <AlertCircle className="size-4 mr-1" />
                {errors.password}
              </div>
            )}
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              className={getInputClassName("confirmPassword")}
              placeholder="••••••••"
            />
            {errors.confirmPassword && (
              <div className="flex items-center mt-2 text-red-600 text-sm">
                <AlertCircle className="size-4 mr-1" />
                {errors.confirmPassword}
              </div>
            )}
            {!errors.confirmPassword &&
              formData.confirmPassword &&
              formData.password === formData.confirmPassword && (
                <div className="flex items-center mt-2 text-green-600 text-sm">
                  <CheckCircle className="size-4 mr-1" />
                  Passwords match
                </div>
              )}
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              id="terms"
              className="size-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1"
              required
            />
            <label htmlFor="terms" className="ml-2 text-sm text-gray-600">
              I agree to the{" "}
              <a href="#" className="text-indigo-600 hover:text-indigo-800">
                Terms of Service
              </a>{" "}
              and{" "}
              <a href="#" className="text-indigo-600 hover:text-indigo-800">
                Privacy Policy
              </a>
            </label>
          </div>

          <button
            type="submit"
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-300 font-medium transition duration-200 shadow-lg hover:shadow-xl"
          >
            Create Account
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{" "}
            <Link
              to="/"
              className="text-indigo-600 hover:text-indigo-800 font-medium"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
