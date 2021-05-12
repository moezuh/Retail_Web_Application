from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np
import pypyodbc
import os
import csv


UPLOAD_FOLDER = '/home/site/wwwroot/static'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Helper functions

def connectTodb():
    myConnection = pypyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                            'SERVER=tcp:vcdcloudcomputing.database.windows.net,1433;'
                            'DATABASE=Group2DB;'
                            'UID=group2cc; PWD=Cloudcomputing2021;')
    return myConnection


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def uploadData(household, product, transaction):
    conn = connectTodb()
    db = conn.cursor()
    db.fast_executemany = True
    db.executemany("DELETE FROM TRANSACTIONS; DELETE FROM HOUSEHOLDS; DELETE FROM PRODUCTS;") # Delete all rows in a table

    with open(f"/home/site/wwwroot/static/{household}", "r") as file:
        reader = csv.reader(file, delimiter=',')
        counter = 0
        for row in reader:  # read each row and insert into db
            counter += 1
            if counter == 1:  # Ignore schema
                continue
            else:
                db.execute("INSERT INTO HOUSEHOLDS(HSHD_NUM, LOYALTY_FLAG, AGE_RANGE, MARITAL, INCOME_RANGE, HOMEOWNER, HSHD_COMPOSITION, HH_SIZE, CHILDREN) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [int(row[0]), row[1][:3], row[2][:10], row[3][:20], row[4][:20], row[5][:30], row[6][:50], row[7][:10], row[8][:10]])   
    
    with open(f"/home/site/wwwroot/static/{product}", "r") as file:
        reader = csv.reader(file, delimiter=',')
        counter = 0
        for row in reader:  # read each row and insert into db
            counter += 1
            if counter == 1:  # Ignore schema
                continue

            else:
                db.execute("INSERT INTO PRODUCTS(PRODUCT_NUM, DEPARTMENT, COMMODITY, BRAND_TY, NATURAL_ORGANIC_FLAG) VALUES (?, ?, ?, ?, ?)", [int(row[0]), row[1], row[2], row[3], row[4]])

    with open(f"/home/site/wwwroot/static/{transaction}", "r") as file:
        reader = csv.reader(file, delimiter=',')
        counter = 0
        for row in reader:  # read each row and insert into db
            counter += 1
            if counter == 1:  # Ignore schema
                continue
            elif counter == 10002:  # insert only 10k records in transaction table
                break
            else:
                db.execute("INSERT INTO TRANSACTIONS(BASKET_NUM, HSHD_NUM, PURCHASE, PRODUCT_NUM, SPEND, UNITS, STORE_R, WEEK_NUM, YEAR) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [int(row[0]), int(row[1]), row[2], int(row[3]), float(row[4]), int(row[5]), row[6], int(row[7]), int(row[8])])
    
    conn.commit()
    conn.close()
    print("file uploaded successfully")


class User():
    def __init__(self, fname, lname, email, password):
        self.fname = fname
        self.lname = lname
        self.email = email
        self.password = password
    
    def __repr__(self):
        return '<User %r>' % self.fname

@app.route('/')
@app.route('/home')
def default():
    return render_template("index.html")


@app.route('/validate', methods=['POST', 'GET'])
def validate():
    username = str(request.form['email'])
    password = str(request.form['password'])
    if not username or not password:
        return render_template("index.html")
    else:
        conn = connectTodb()
        db = conn.cursor()
        id_ = 0
        try:
            id_ = db.execute("SELECT * FROM users_info WHERE emails = ? AND passwords = ?",(username, password)).fetchone()[0]
            conn.close()
            return redirect(url_for("class_user_test")) # change it to dashboards to display dashbaords
        except:
            return render_template("invalid_login.html")  

@app.route('/Dashboard') # display dashboard
def dashboards():
    return render_template("dashboards.html")


@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route('/post_info', methods=['POST'])
def post_info():
    user = User(request.form['fname'], request.form['lname'], request.form['email'], request.form['password'])
    if not user.fname or not user.lname or not user.email or not user.password:
        return render_template("signup.html")
    else:
        conn = connectTodb()
        db = conn.cursor()
    try:
        db.execute("INSERT INTO users_info (Fnames, Lnames, emails, passwords) VALUES (?, ?, ?, ?)", ([user.fname, user.lname, user.email, user.password]))
        conn.commit()
        conn.close()
        return redirect(url_for('default'))
    except:
        conn.close()
        print("Error in inserting information into the database")
        return redirect(url_for('post_info'))


@app.route('/file_upload', methods=['GET', 'POST'])
def file_upload():
    if request.method == 'POST':
        household_file = request.files['file1']
        product_file = request.files['file2']
        transaction_file = request.files['file3']

        if allowed_file(household_file.filename) and allowed_file(product_file.filename) and allowed_file(transaction_file.filename):
            secure_household = secure_filename(household_file.filename)
            secure_product = secure_filename(product_file.filename)
            secure_transaction = secure_filename(transaction_file.filename)

            household_file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_household))
            product_file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_product))
            transaction_file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_transaction))
            uploadData(secure_household, secure_product, secure_transaction) # Upload file contents into database
            return redirect(url_for('data_sample'))
        else:
            return render_template("file_upload.html", filename="Wrong file type!")

    return render_template("file_upload.html")
    

@app.route('/data_sample', methods=['POST', 'GET'])  # displays sample data pull
def data_sample():
    conn = connectTodb()
    db = conn.cursor()
    data = db.execute("SELECT * FROM [HOUSEHOLDS] JOIN [TRANSACTIONS] ON [TRANSACTIONS].[HSHD_NUM] = [HOUSEHOLDS].[HSHD_NUM] JOIN [PRODUCTS] ON [TRANSACTIONS].[PRODUCT_NUM] = [PRODUCTS].[PRODUCT_NUM] ORDER BY BASKET_NUM, PURCHASE, [TRANSACTIONS].PRODUCT_NUM, DEPARTMENT, COMMODITY").fetchall()
    df = pd.DataFrame(data)
    df = df.drop([10, 12], axis=1)  # Drop dublicate columns
    conn.close()
    hh = 10 # default information would be displayed for HSHD_NUM = 10 
    if request.method == 'POST':
        hh = int(request.form["HSHD_NUM"])
    
    items = df.values
    HSHD_NUMs = sorted(list(set(items[:, 0])))
    hh_details = []
    for row in items:
        if row[0] == hh:
            hh_details.append(row)
    
    return render_template('data_display.html', data = hh_details, HSHD_NUMs=HSHD_NUMs)


@app.route('/classification_test', methods=['GET', 'POST'])
def class_user_test():
    
    def runClassification(spend, marital, hh_size, income):
        # define the model
        model = LogisticRegression(max_iter = 1000)
        # dummy training to initialize weights and biases of the model
        model.fit(np.array([[0, 0, 0, 0], [1, 1, 1, 1]]), [0, 1]) 

        # Assigning trained weights and biases to the model
        model.coef_ = np.array([[ 0.01418876, -0.34609983, 0.14408751, 0.02292672]]) # weights
        model.bias_ = np.array([-0.3975337]) # bias

        example_instance = np.array([[spend, marital, hh_size, income]]) # [[TOTAL_SPEND, MARITAL, HH_SIZE, INCOME_RANGE]]

        # Test the model
        prediction = model.predict(example_instance)
        return prediction[0].item()

    df = pd.read_csv('CustomerChurn.csv')
    spendData = sorted(df.TOTAL_SPEND.unique().tolist())
    houseData = sorted(df.HH_SIZE.unique().tolist())
    incomeData = sorted(df.INCOME_RANGE.unique().tolist())

    if request.method == 'POST':
        spendVal = int(request.form['spend'])
        maritalVal = int(request.form['marital'])
        houseVal = int(request.form['house'])
        incomeVal = int(request.form['income'])
        resultInt = runClassification(spendVal, maritalVal, houseVal, incomeVal)
        result = 'Loyal'
        if resultInt == 0:
            result = 'Unloyal'
        return render_template("classification.html", spend_items=spendData, housesize_items=houseData,income_items=incomeData, result=result)

    return render_template("classification.html", spend_items=spendData, housesize_items=houseData,income_items=incomeData)

@app.route('/regression_test', methods=['GET', 'POST'])
def regression_test():

    def runRegression(purchases):
        # define the model
        lrModel = LinearRegression()
        # dummy training to initialize weights and biases of the model
        lrModel.fit(np.array([0]).reshape(-1, 1), [1])
        # Assigning trained weights and biases to the model
        lrModel.coef_ = np.array([[0.08037347]]) # weights
        lrModel.bias_ = np.array([3.68091473]) # bias
        example_instance = np.array([purchases]).reshape(-1, 1) # [NUMBER OF PURCHASES]
        # Test the model
        prediction = lrModel.predict(example_instance)
        print(prediction)
        return prediction[0].item()

    df = pd.read_csv('Samplepull1.csv')
    print(df)
    numPurchaseData = sorted(df['Number Of Purchases'].unique().tolist())
    print(numPurchaseData)

    if request.method == 'POST':
        purchVal = int(request.form['purchases'])
        resultInt = runRegression(purchVal)
        return render_template("regression.html", purchase_items=numPurchaseData, result=resultInt)

    return render_template("regression.html", purchase_items=numPurchaseData)

if __name__ == '__main__':
    app.run()
