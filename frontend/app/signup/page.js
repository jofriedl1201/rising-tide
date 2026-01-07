'use client';

import { useState, useEffect } from 'react';

export default function SignupPage() {
    const [formData, setFormData] = useState({
        shop_name: '',
        subdomain: '',
        user_email: '',
        plan_id: '1',
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [user, setUser] = useState(null); // Authenticated user
    const [isSubdomainManuallyEdited, setIsSubdomainManuallyEdited] = useState(false);

    const submitShop = async (data) => {
        setIsLoading(true);
        setError('');

        try {
            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
            const response = await fetch(`${backendUrl}/create-checkout-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const responseData = await response.json();

            if (response.ok) {
                window.location.href = responseData.url;
            } else {
                setError(responseData.detail || 'An error occurred during signup.');
                setIsLoading(false);
            }
        } catch (err) {
            setError('Failed to connect to the server.');
            setIsLoading(false);
        }
    };

    const handleSignout = async () => {
        try {
            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
            await fetch(`${backendUrl}/auth/signout`, {
                method: 'POST',
                credentials: 'include',
            });
            // Clear user state and reload
            setUser(null);
            window.location.reload();
        } catch (error) {
            console.error('Signout error:', error);
        }
    };

    // Check authentication status on mount
    useEffect(() => {
        const checkSession = async () => {
            try {
                const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
                const response = await fetch(`${backendUrl}/auth/users/me`, {
                    credentials: 'include', // CRITICAL: Send session cookie
                });

                if (response.ok) {
                    const userData = await response.json();
                    setUser(userData);
                    console.log("Authenticated user:", userData);
                } else {
                    console.log("Not authenticated");
                    setUser(null);
                }
            } catch (error) {
                console.error("Error checking session:", error);
                setUser(null);
            }
        };
        checkSession();
    }, []);

    const handleOAuth = (provider) => {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        window.location.href = `${backendUrl}/auth/login/${provider}?next=/signup`;
    };

    const generateSlug = (text) => {
        return text
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => {
            const newData = { ...prev, [name]: value };

            // Auto-generate subdomain from shop name if not manually edited
            if (name === 'shop_name' && !isSubdomainManuallyEdited) {
                newData.subdomain = generateSlug(value);
            }

            return newData;
        });
    };

    const handleSubdomainChange = (e) => {
        setIsSubdomainManuallyEdited(true);
        handleChange(e);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        // If user is already logged in, submit immediately
        if (user) {
            await submitShop({
                ...formData,
                user_email: user.email
            });
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                    {user ? `Welcome, ${user.email}!` : 'Start your 30-day free trial'}
                </h2>
                <p className="mt-2 text-center text-sm text-gray-600">
                    {user ? 'Please complete your shop details below.' : 'Sign in to create your shop.'}
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    {error && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-r-md" role="alert">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm text-red-700">{error}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* OAuth Buttons - only show if not authenticated */}
                    {!user && (
                        <div className="space-y-3 mb-6">
                            <button
                                type="button"
                                onClick={() => handleOAuth('google')}
                                className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                                </svg>
                                Sign up with Google
                            </button>

                            <button
                                type="button"
                                onClick={() => handleOAuth('microsoft')}
                                className="w-full flex items-center justify-center gap-3 bg-[#2F2F2F] text-white py-3 px-4 rounded-lg hover:bg-[#1F1F1F] transition-colors font-medium"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 23 23">
                                    <path fill="#f3f3f3" d="M0 0h23v23H0z" />
                                    <path fill="#f35325" d="M1 1h10v10H1z" />
                                    <path fill="#81bc06" d="M12 1h10v10H12z" />
                                    <path fill="#05a6f0" d="M1 12h10v10H1z" />
                                    <path fill="#ffba08" d="M12 12h10v10H12z" />
                                </svg>
                                Sign up with Microsoft
                            </button>
                        </div>
                    )}

                    {user && (
                        <div className="mb-8 p-4 bg-green-50 border border-green-200 rounded-md flex items-center justify-between">
                            <div className="flex items-center">
                                <span className="text-green-500 mr-3">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                </span>
                                <div>
                                    <p className="text-green-700 font-medium">Logged in as {user.email}</p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={handleSignout}
                                className="text-sm text-green-600 hover:text-green-800 font-medium underline"
                            >
                                Sign Out
                            </button>
                        </div>
                    )}

                    {/* Shop Creation Prompt - shown when authenticated */}
                    {user && (
                        <div className="mb-6 text-center">
                            <h2 className="text-2xl font-semibold text-gray-800">Now let's create your shop!</h2>
                        </div>
                    )}

                    <form className="space-y-6" onSubmit={handleSubmit}>
                        <input type="hidden" name="plan_id" value={formData.plan_id} />

                        {/* Shop Name */}
                        <div>
                            <label htmlFor="shop_name" className="block text-sm font-medium text-gray-700 mb-1">
                                Shop Name
                            </label>
                            <input
                                id="shop_name"
                                name="shop_name"
                                type="text"
                                required
                                disabled={!user}
                                className={`appearance-none block w-full px-4 py-3 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out ${!user ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200' : 'border-gray-300'}`}
                                placeholder={!user ? "Sign in to enter shop name" : "My Awesome Shop"}
                                value={formData.shop_name}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Subdomain */}
                        <div>
                            <label htmlFor="subdomain" className="block text-sm font-medium text-gray-700 mb-1">
                                Subdomain
                            </label>
                            <div className="mt-1 flex rounded-md shadow-sm">
                                <input
                                    id="subdomain"
                                    name="subdomain"
                                    type="text"
                                    required
                                    disabled={!user}
                                    className={`flex-1 min-w-0 block w-full px-4 py-3 rounded-none rounded-l-md border focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out ${!user ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200' : 'border-gray-300'}`}
                                    placeholder={!user ? "myshop" : "myshop"}
                                    value={formData.subdomain}
                                    onChange={handleSubdomainChange}
                                />
                                <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                                    .rapidcat.com
                                </span>
                            </div>
                        </div>

                        {/* Email Input Removed */}

                        <div className="pt-2">
                            <button
                                type="submit"
                                disabled={isLoading || !user}
                                className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white transition duration-150 ease-in-out ${isLoading || !user
                                    ? 'bg-gray-400 cursor-not-allowed'
                                    : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                                    }`}
                            >
                                {isLoading ? 'Processing...' : (user ? 'Start 30-day free trial' : 'Sign in to Continue')}
                            </button>
                        </div>
                    </form>
                </div>
                <div className="px-10 py-4 bg-gray-50 border-t border-gray-100 text-center">
                    <p className="text-xs text-gray-500">By signing up, you agree to our Terms of Service and Privacy Policy.</p>
                </div>
            </div>
        </div>
    );
}
