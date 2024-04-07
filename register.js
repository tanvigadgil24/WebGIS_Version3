
/*
last modification: 02/04/24
Description: JavaScript logic for the login of tree management webapp
*/

document.addEventListener('DOMContentLoaded', function () {
    const registerForm = document.getElementById('registerForm');
    registerForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission

        const username = document.getElementById('newUsername').value;
        const password = document.getElementById('newPassword').value;

        // Preparing form data
        let formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        // Sending the form data to your Flask backend
        fetch('http://localhost:5000/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Redirect to the login page after successful registration
                window.location.href = 'login.html';
            } else {
                // Show an error message if registration failed
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error during account creation:', error);
            alert('Account creation failed. Please try again.');
        });
    });
})