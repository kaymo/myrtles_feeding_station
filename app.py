from flask import Flask, render_template, url_for, request, redirect
import sqlite3, datetime


app = Flask(__name__)
#app.config['DEBUG'] = False

# E.g., display 4 as "1 1/3"
def get_scoop_display(quantity):
    if quantity == 0:
        return '0'
        
    whole = quantity / 3
    remainder = quantity % 3
    
    displayed_whole = str(whole)

    if remainder == 1:
        displayed_remainder = ' &frac13;'
    elif remainder == 2:
        displayed_remainder = ' &frac23;'
    else:
        displayed_remainder = ''
        
    if whole == 0:
        return displayed_remainder
    
    if remainder == 0:
        return displayed_whole
    
    return str(whole) + displayed_remainder
    
# Get previous 3am
def get_day_start():
    now = datetime.datetime.now()
    timespan_three_hours = datetime.timedelta(hours=3)
    three_hours_ago = now - timespan_three_hours
    start_of_day_three_hours_ago = three_hours_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    return str(start_of_day_three_hours_ago + timespan_three_hours)


@app.route('/')
def index():
    portions = []
    today = { 'chicken': 0, 'fish': 0, 'total': 0 }
        
    con = None
    try: 
        # Connect to the db
        con = sqlite3.connect('myrtle.db')
        cur = con.cursor()
        
        # Get all entries since 3am
        query = "SELECT strftime('%H:%M',time), quantity, flavour FROM myrtle WHERE time > datetime('" + get_day_start() + "')"
        cur.execute(query)
        rows = cur.fetchall()

        # Form the data that will passed to the JS and HTML
        portions = []
        for row in rows:
        
            # Compile today's food
            if row[1] == 1:
                portion_quantity = '&frac13;'
            elif row[1] == 2:
                portion_quantity = '&frac23;'
            elif row[1] == 3:
                portion_quantity = '1'
            elif row[1] == 6:
                portion_quantity = '2'
                
            portions.append({ 'time': row[0], 'quantity': portion_quantity, 'flavour': row[2] })
        
            # Sum quantities and breakdown by flavour
            today['total'] += row[1]
            if row[2] == 'Fish':
                 today['fish'] += row[1]
            elif row[2] == 'Chicken':
                 today['chicken'] += row[1]
        
        today_display = { 'chicken': get_scoop_display(today['chicken']), 'fish': get_scoop_display(today['fish']), 'total': get_scoop_display(today['total']) }

    except sqlite3.Error, e:
        print "Error: {}".format(e.args[0])

    # Close the db connection    
    finally: 
        if con:
            con.close()
    
    return render_template('main.html', portions=portions, today=today_display, limit_reached = today['total']/3 >= 6)
    

@app.route('/food-portions', methods=['POST'])
def food_portions():
    # Grab the form data
    quantity = int(request.form['quantity'])
    flavour = request.form['flavour']
    
    # Connect to database
    con = None
    try: 
        con = sqlite3.connect('myrtle.db')    
        cur = con.cursor()
        
        # Insert the portion
        query = 'INSERT INTO myrtle (time, quantity, flavour) VALUES ("{:s}", {:d}, "{:s}")'.format(str(datetime.datetime.now()), quantity, flavour)
        cur.execute(query)
        con.commit()
        
    except sqlite3.Error, e:
        print "Error: {}".format(e.args[0])
        
    # Close the db connection    
    finally: 
        if con:
            con.close()
              
    # Refresh the page  
    return redirect(url_for('index'))
    

@app.route('/undo', methods=['POST'])
def undo():
    # Connect to database
    con = None
    try: 
        con = sqlite3.connect('myrtle.db')    
        cur = con.cursor()
        
        # Remove last DB entry
        query = 'DELETE FROM myrtle ORDER BY time DESC LIMIT 1'
        cur.execute(query)
        con.commit()
        
    except sqlite3.Error, e:
        print "Error: {}".format(e.args[0])
        
    # Close the db connection    
    finally: 
        if con:
            con.close()
            
    # Refresh the page  
    return redirect(url_for('index'))

    
if __name__ == '__main__':
    app.run()
