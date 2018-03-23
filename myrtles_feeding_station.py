from flask import Flask, render_template, url_for, request, redirect
import sqlite3, datetime


application = Flask(__name__)
application.config['DEBUG'] = False

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
    
    return displayed_whole + displayed_remainder
    
# Get previous 3am
def get_day_start(days_ago=0):
    now = datetime.datetime.now()
    timespan_three_hours = datetime.timedelta(hours=3)
    three_hours_ago = now - timespan_three_hours
    start_of_day_three_hours_ago = three_hours_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    
    timespan_days_ago = datetime.timedelta(days=days_ago)
    start_of_day_three_hours_ago -= timespan_days_ago
    
    return str(start_of_day_three_hours_ago + timespan_three_hours)


@application.route('/')
def index():
    portions = []
    today = { 'chicken': 0, 'fish': 0, 'total': 0 }
    next_flavour = 'Fish'
        
    con = None
    try: 
        # Connect to the db
        con = sqlite3.connect('myrtle.db')
        cur = con.cursor()
        
        # TODAY'S PORTIONS DATA
        
        # Get all entries since 3am
        query = "SELECT strftime('%H:%M',time), quantity, flavour FROM myrtle WHERE time > datetime('" + get_day_start() + "')"
        cur.execute(query)
        rows = cur.fetchall()

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
        
        # NEXT FLAVOUR
        
        if today['total'] == 0:
    
            # First scoop of the day so choose whichever flavour wasn't last fed
            query = "SELECT flavour FROM myrtle ORDER BY time DESC LIMIT 1"
            cur.execute(query)
            previous = cur.fetchone()
            
            if previous is not None and previous[0] == 'Fish':
                next_flavour = 'Chicken'
            else:
                next_flavour = 'Fish'
        else:
            # Alternate every 2 scoops
            first_flavour = rows[0][2]
            second_flavour = 'Fish' if first_flavour == 'Chicken' else 'Chicken'
            
            # Quantities are in 1/3-scoop units; alternate every 6 units
            if today['total'] % 12 < 6:
                next_flavour = first_flavour
            else:
                next_flavour = second_flavour
                
        # Display quantities as scoop fractions
        today_display = { 'chicken': get_scoop_display(today['chicken']), 'fish': get_scoop_display(today['fish']), 'total': get_scoop_display(today['total']) }

        # CHART DATA
        
        # Get all entries in the past n days
        n = 5
        cur.execute("SELECT strftime('%H:%M',time), quantity FROM myrtle WHERE time BETWEEN datetime('" + get_day_start(n) + "') AND datetime('" + get_day_start() + "') ")
        history_rows = cur.fetchall()
        
        # Get all entries today
        cur.execute("SELECT strftime('%H:%M',time), quantity FROM myrtle WHERE time > datetime('" + get_day_start() + "')")
        today_rows = cur.fetchall()

        # Form the time series for the x-axis buckets
        now = datetime.datetime.now()
        current = datetime.datetime(2000, 1, 1, 6)
        last = datetime.datetime(2000, 1, 2)
        delta = datetime.timedelta(minutes=15)
        times = []
        while current < last:
            times.append(current)
            current += delta
            
        history_datum = []
        today_datum = []
        for time in times:
            
            # For each time, sum the units fed before the time
            history_total = sum([row[1] for row in history_rows if row[0] < time.strftime('%H:%M')])
            today_total   = sum([row[1] for row in today_rows   if row[0] < time.strftime('%H:%M')])
            
            # [x,y] data pair where x is the time of day and y is the amount of food
            history_datum.append( "[Date.parse('{}'),{}]".format(time, float(history_total) / float(n * 3)) )
            
            if len(today_rows) and (time - delta) <= datetime.datetime(2000, 1, 1, now.hour, now.minute):
                today_datum.append("[Date.parse('{}'),{}]".format(time, float(today_total) / float(3)) )
            
        history_data = "[" +','.join(history_datum)+ "]"
        today_data = "[" +','.join(today_datum)+ "]"
        
    except sqlite3.Error, e:
        print "Error: {}".format(e.args[0])

    # Close the db connection    
    finally: 
        if con:
            con.close()
    
    return render_template('chart.html', portions=portions, today=today_display, limit_reached = today['total']/3 >= 6, next_flavour=next_flavour, history_data=history_data, today_data=today_data)
    

@application.route('/food-portions', methods=['POST'])
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
    

@application.route('/undo', methods=['POST'])
def undo():
    # Connect to database
    con = None
    try: 
        con = sqlite3.connect('myrtle.db')    
        cur = con.cursor()
        
        # Remove last DB entry
        query = "DELETE FROM myrtle WHERE time > datetime('" + get_day_start() + "') ORDER BY time DESC LIMIT 1"
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
    application.run()

# EOF
