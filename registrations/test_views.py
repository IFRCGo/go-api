# 1. create two users to function as gatekeepers
# 2. Make a request to views.NewRegistration with new user request
# 3. Access the Pending users table to obtain the user's token
# 4. Use the user token and user username to query views.VerifyEmail
# 5. Confirm that a user with an official email is activated, and a user without an official email is not activated
# 6. Use the admin token and new user username to query views.ValidateUser
# 7. Confirm that a user without an official email is activated.
