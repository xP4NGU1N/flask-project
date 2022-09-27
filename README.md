# Sports Meet

### Requirements:
flask<br>
flask-session<br>
flask-mail<br>
werkzeug (password hashing)

To run: flask --app application run

### Description:
This website functions as a platform for people to connect with each other through similar hobbies. Users are able to join events organised by others or create their own event. 


#### Pages
**login.html**<br>
log-in page.

**register.html**<br>
For users to create their account. After validation, the information is added to db.

**index.html**<br>
Homepage after logging in. Users can see their upcoming events from a table and withdraw from any registered activitiy.

**events.html**<br>
Allows users to browse through all the activities (filtered by drop-down list). Users can join the activity so long it is not oversubscribed and will receive an email to their registered gmail account once confirmed.

**similar_events.html**<br>
When the user loads this page, the number of events for each hobby that the user has joined will be counted, and the hobby the user is "most" interested in will be filtered. The user will view other events of the same hobby in this page. If there is a tie in terms of number of events per hobby, the other hobby (decided by alphabatical order) will be suggested via a submit input box, linking the user back to the events page.

**create.html**<br>
Allows users to create their own activity. Once it passes validation, everyone will be able to view and join their event. User who created the event will automatically be added to the event. An email will also be sent to the registered gmail account to confirm the creation of event.

**change_password.html**<br>
Similar to the registration page, users can change their password here after confirming their account details (by knowing the previous password).


#### Table
**connect.db**<br>
Determine who joins which events -<br>
users: stores user account information.<br> 
activities: stores every information regarding an event.

Data validation -<br>
participant: stores the detail of every participant who joined any event.<br>
date_checker: check when the event has expired. Once the event has expired (ie event date is before today), the event will be automatically removed from the system.<br>


#### Flask Application
**application.py**<br>
Perform checks on the user input as well as link pages to each other. Implemented Email notification with the help of flask documentation.
