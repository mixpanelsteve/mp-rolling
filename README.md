mp-rolling
==========

rolling retention in mixpanel

Pass the api_key and secret as two command line parameters (or alter the script to make it easier)
update the beginning date and retention types that you're interested in

Output format:

cohorts - the total number of uniques seen with that day as the Signed up / U:Created

each type of retention specified will have its own key in the final return
-this specifies the number of the original cohort that has been seen after n days from creation, where n is the type specified
