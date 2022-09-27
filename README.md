# Sports Meet

#### Requirements:
flask
flask-session
flask-mail
werkzeug (password hashing)

To run: flask --app application run

#### Description:
This website functions as a platform for people to connect with each other through similar hobbies. Users are able to join events organised by others or create their own event. 


#### Pages
**login.html**
log-in page.

**register.html**
For users to create their account. In this page, I included various input boxes for users to submit. After clearing the data validation, the information would be added to a database.

**index.html**
The homepage after logging in. I included a table for users to see their upcoming events. From this table, I considered what information to input as the table would not be able to fit all the information. I also added a function for the user to withdraw from the activitiy. This button linked to a withdraw page taking the input as the information from the table.

**events.html**
This page allowed users to browse through all the activities in the database. If they choose to filter events based on their hobbies, there is a drop-down box function. Just to make the interface better, I made the table header a variable that could change based on the hobby. After viewing the various activities, users could press on join to join the event. Upon joining the event (passing the data validation: such as is the event oversubscribed), users would receive an email to their registered gmail account.

**similar_events.html**
When the user loads this page, the number of events for each hobby that the user has joined will be counted, and the hobby the user is "most" interested in will be filtered. The user will view other events of the same hobby in this page. If there is a tie in terms of number of events per hobby, the other hobby (decided by alphabatical order) will be suggested via a submit input box, linking the user back to the events page.

**create.html**
This page allowed users to create their own activity. Once it passed the data validation, everyone will be able to view and join their event. User who created the event will automatically be added to the event. An email will also be sent to the registered gmail account to confirm the creation of event.

**change_password.html**
Similar to the registration page, users can change their password here after confirming their account details (by knowing the previous password).


#### Table
**connect.db**
Determine who joins which events - 
users: stores user account information. 
activities: stores every information regarding an event.

Data validation - 
participant: stores the detail of every participant who joined any event.
date_checker: check when the event has expired. Once the event has expired (ie event date is before today), the event will be automatically removed from the system. 


#### Flask Application
**application.py**
Perform checks on the user input as well as link pages to each other. Implemented Email notification with the help of flask documentation.
