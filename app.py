from flask import Flask, render_template, url_for
app = Flask(__name__)


@app.route('/')
def main():
    # Get today's feedings
    portions = [
        { 'time': '07:50', 'quantity': '2', 'flavour': 'Fish' },
        { 'time': '13:50', 'quantity': '&frac23;', 'flavour': 'Chicken' },
        { 'time': '16:14', 'quantity': '&frac23;', 'flavour': 'Chicken' },
        { 'time': '17:59', 'quantity': '&frac23;', 'flavour': 'Chicken' },
        { 'time': '20:04', 'quantity': '&frac13;', 'flavour': 'Fish' },
    ]
    today = { 'chicken': '2', 'fish': '2 &frac13;', 'total': '4 &frac13;' }
    
    return render_template('main.html', portions=portions, today=today)
    
@app.route('/food-portions', methods=['POST', 'DELETE'])
def food_portions():
    if request.method == 'POST':
        portion = request.form[portion_size]
        # Add portion to DB
        flash('Myrtle\'s been fed!')
    elif request.method == 'DELETE':
        # remove last DB entry
        flash('Fat-fingered fuck.')
    return redirect(url_for('index'))

    
if __name__ == '__main__':
    app.run()
