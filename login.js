/*
last modification: 02/04/24
Description: JavaScript logic for the login of tree management webapp
*/

document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // Example of sending form data to your Flask backend
        fetch('http://localhost:5000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Login failed');
            }
            return response.json();
        })
        .then(data => {
            // Handle response data; for example, redirect on successful login
            window.location.href = '/dashboard.html'; // Adjust the redirection URL as needed
        })
        .catch(error => {
            console.error('Error during login:', error);
            alert('Login failed. Please check your username and password.');
        });
    });
});