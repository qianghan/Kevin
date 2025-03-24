/**
 * Test Authentication Script
 * 
 * Run this from the browser console to test authentication functionality
 */

async function testAuth() {
  console.group('Authentication Test');
  console.log('Starting authentication test...');
  
  // Test cookie presence
  const cookiesEnabled = navigator.cookieEnabled;
  console.log('Cookies enabled in browser:', cookiesEnabled);
  
  // Check document cookies
  const cookies = document.cookie;
  console.log('Document cookies exist:', !!cookies.length);
  console.log('Cookie string length:', cookies.length);
  console.log('Contains session token:', cookies.includes('next-auth.session-token'));
  
  try {
    // Make a fetch request with credentials
    console.log('Testing fetch API with credentials...');
    const fetchResponse = await fetch('/api/user/profile', {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('Fetch status:', fetchResponse.status);
    const fetchData = await fetchResponse.json();
    console.log('Fetch response:', fetchData);
    
    // Test axios request
    console.log('Testing axios request with credentials...');
    const { data: axiosData, status } = await axios.get('/api/user/profile', { 
      withCredentials: true 
    });
    
    console.log('Axios status:', status);
    console.log('Axios response:', axiosData);
    
    console.log('Authentication test completed');
  } catch (error) {
    console.error('Authentication test failed:', error);
    console.error('Error details:', {
      message: error.message,
      response: error.response,
      status: error.response?.status,
      data: error.response?.data
    });
  }
  
  console.groupEnd();
}

// You can call this function from the browser console
console.log('Auth test utility loaded. Run testAuth() to check authentication.'); 