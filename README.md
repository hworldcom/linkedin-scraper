make sure that virtual environment installed
if not run

pip install virtualenv

to install dependencies run

virtualenv venv
source venv/bin/activate
pip install -r requirements.txt


extract_data_company_app.py
extracts mutual connections for a given company
currently the code assumes that the company can be found
in line 9 of the file specify the list of companies
the output will be stored in a newly created file linkedin_profiles.xlsx

extract_data_mutuals_app.py
extracts mutual connection from a list of people
currently the list given by a column in excel file
format is given in rethink_connections.xlsx
update the column "LinkedIn Profile" to generate mutual connections
new columns will be created in rethink_connections_updated.xlsx


running both files will require login to linkedin
once logged in cookies are stored and no second attempt needed
