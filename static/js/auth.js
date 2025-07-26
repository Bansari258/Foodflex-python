document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('#login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const messageDiv = document.querySelector('#login-message');
            messageDiv.textContent = '';
            document.querySelectorAll('.error').forEach(el => el.textContent = '');

            const formData = {
                email: document.querySelector('#sign-in-dialog #email').value,
                password: document.querySelector('#sign-in-dialog #password').value
            };

            fetch('/api/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('#sign-in-dialog input[name="csrfmiddlewaretoken"]').value
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    localStorage.setItem('access_token', data.data.access);
                    localStorage.setItem('refresh_token', data.data.refresh);
                    messageDiv.style.color = 'green';
                    messageDiv.textContent = data.message;
                    setTimeout(() => window.location.href = '/', 2000);
                } else {
                    messageDiv.style.color = 'red';
                    if (data.errors) {
                        if (typeof data.errors === 'string') {
                            messageDiv.textContent = data.errors;
                        } else {
                            for (let field in data.errors) {
                                const errorSpan = document.querySelector(`#${field}-error`);
                                if (errorSpan) {
                                    errorSpan.style.color = 'red';
                                    errorSpan.textContent = Array.isArray(data.errors[field]) ? data.errors[field][0] : data.errors[field];
                                } else {
                                    messageDiv.textContent = data.errors[field] || 'Login failed.';
                                }
                            }
                        }
                    } else {
                        messageDiv.textContent = data.message || 'Login failed.';
                    }
                }
            })
            .catch(error => {
                messageDiv.style.color = 'red';
                messageDiv.textContent = 'An unexpected error occurred.';
            });
        });
    }
});