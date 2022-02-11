from Raspi_Gui import Flask, FlaskUI, render_template, redirect, url_for, request
from Raspi_Gui import os, requests, load_dotenv
from Raspi_Gui import mdls
from Raspi_Gui import LoginManager, login_user, logout_user, login_required, current_user, UserMixin, flash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from Raspi_Gui import func

app = Flask(__name__, static_url_path="/static")
UI = FlaskUI(app)

load_dotenv(os.path.join(os.getcwd(),".env"))

SECRET_KEY = os.environ.get("SECRET_KEY")
MAIN_URL = "http://192.168.1.111:4000"
STALL_ID = os.environ.get("STALL_ID")
ACCOUNT = os.environ.get("ACCOUNT")
PASSWORD = os.environ.get("PASSWORD")

app.config["SECRET_KEY"] = SECRET_KEY
login_manager = LoginManager(app)
login_manager.login_view = "signup"

@login_manager.user_loader
def load_user(user_id: int):
    return mdls.Stall.retrieve_info(STALL_ID, ACCOUNT, PASSWORD, MAIN_URL)

@app.route("/", methods=["GET", "POST"])
def signup():
    if (user_attempt:=mdls.Stall.retrieve_info(STALL_ID, ACCOUNT, PASSWORD, MAIN_URL)) != -1:
        login_user(user_attempt)
        flash("Logged In", category="success")
        return redirect(url_for("index"))
    form = mdls.Signup()
    if form.validate_on_submit():
        instance = mdls.Stall(0, form.Name.data, form.Password.data, form.Account.data, form.Phone.data)
        res = instance.register(MAIN_URL)
        if res == 0:  # IF REGISTERING IS SUCCESSFUL
            inst = mdls.Stall.retrieve_info(1, form.Account.data, form.Password.data)
            STALL_ID_ = inst.Stall_ID
            with open(".env", "w+") as file:
                file.write(f"SECRET_KEY={SECRET_KEY}")
                file.write(f"STALL_ID={STALL_ID_}")
                file.write(f"ACCOUNT={form.Account.data}")
                file.write(f"PASSWORD={form.Password.data}")
    return render_template("signup.html", form=form)


@login_required
@app.route("/home")
def index():
    return render_template("index.html", ACCOUNT=ACCOUNT)

@login_required
@app.route("/Manage", methods=["GET", "POST"])
def Manage_Orders():
    df = func.get_orders(MAIN_URL, STALL_ID)
    dic = func.json_to_dic("products.json")
    df["PATH"] = [dic.get(f'{idx}') for idx in df["ID_PRODUCT"].values]
    df["PRICE"] = df["PRICE"].map(lambda x : f'${x:.2f}')
    form = mdls.AcceptForm()
    if form.validate_on_submit() and (res:=request.form.get("Button_Value")):
        if form.Accept.data:
            mdls.Stall.update_order(MAIN_URL, res, "PREPARING")
            return redirect(url_for("Manage_Orders"))
        elif form.Deny.data:
            mdls.Stall.cancel_order(MAIN_URL, res)
            return redirect(url_for("Manage_Orders"))
        elif form.Done.data:  # THIS SHOULD TRIGGER ALLOCATE FUNCTION
            mdls.Stall.update_order(MAIN_URL, res, "READY")
            phone = df.loc[df["ID_ORDER"] == int(res)].PHONE_NO.values[0]
            phone = f'{phone}'
            Qr_Link = f'{MAIN_URL}/qrcode/send/{res}'
            df_check = all(func.get_orders(MAIN_URL)["STATUS"].isin(["READY", "COLLECTED"]))
            if len(phone) == 8 and phone.isnumeric() and df_check:
                func.notify_phone(f'{phone}', f"Your Order is Ready. Order ID @ {Qr_Link}")
            else:
                flash("Contact not Found")
                print("Connect information is inaccurate")
            return redirect(url_for("Manage_Orders"))
        elif form.Verify.data:
            import cv2
            cap = cv2.VideoCapture(0)  # VIDEO CAPTURE
            det = cv2.QRCodeDetector()

            while True:
                ret, frame = cap.read()
                if not ret:
                    cap.release()
                    cv2.destroyAllWindows()
                    return -1
                barcode_text = func.PROCESSBARCODE(frame, det)
                cv2.imshow('FRAME ATTENDANCE BARCODE', cv2.flip(frame, 1))
                if cv2.waitKey(20) & 0xFF == ord('q'):  # REPLACE THIS WITH GPIO BUTTON
                    break

                if barcode_text != None:
                    cap.release()
                    cv2.destroyAllWindows()
                    return redirect(url_for(f"FINAL_ORDERS", CUD_ID=f'{barcode_text}'))
            
            cap.release()
            cv2.destroyAllWindows()

        else:
            pass
    return render_template("Manage.html", data=df, form=form)



@app.route("/OrderDetail/<CUS_ID>", methods=["GET", "POST"])
def FINAL_ORDERS(CUS_ID):
    form = mdls.Finish_Order()
    df = func.get_orders(MAIN_URL, STALL_ID)
    dic = func.json_to_dic("products.json")
    df = df.loc[((df["ID_CUSTOMER"] == int(CUS_ID)) & (df["STATUS"] == "READY"))]
    if df.size == 0:
        return redirect(url_for("Manage_Orders"))
    Total_Price = df["PRICE"].sum()
    df["PRICE"] = df["PRICE"].map(lambda x: f"${x:.2f}")
    df["PATH"] = [dic.get(f'{idx}') for idx in df["ID_PRODUCT"].values]
    if form.validate_on_submit() and (res:=request.form.get("Button_Value")):
        IDS = df["ID_ORDER"].values
        BOX_ID = mdls.Stall.BOX_STATUS(MAIN_URL, STALL_ID)
        for ID_ in IDS:
            mdls.Stall.update_order(MAIN_URL, ID_, "COLLECTED")
            if ID_ in BOX_ID.values:
                mdls.Stall.UPDATE_ORDER_BOX(MAIN_URL, ID_, 0)
        return redirect(url_for("Manage_Orders"))
    return render_template("Manage_Orders.html", data=df[["ID_ORDER", "PATH", "NAME", "PRICE"]], form=form)



@login_required
@app.route("/Dashboard")
def Dashboard():
    df = func.get_orders(MAIN_URL, STALL_ID)

    metrics = {"Total Sales":f'${df["PRICE"].values.sum():.2f}', 
                "No Of Sales":f'${df.shape[0]:.2f}',
                "Average Amount Per Sales": f'${df["PRICE"].values.mean():.2f}'
    }

    
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    path = "BAR_CHART.png"
    res = df["NAME"].value_counts().values
    plt.pie(res, labels=df["NAME"].unique(), shadow=False)    
    my_circle = plt.Circle( (0, 0), 0.7, color="white")
    plt.title("Volume Sales Per Item")
    plt.legend()
    p = plt.gcf()
    p.gca().add_artist(my_circle)
    plt.savefig(os.path.join(os.getcwd(), "static", path))
    plt.clf()

    return render_template("Dashboard.html", data=df[["ID_ORDER","NAME", "PRICE", "STATUS"]], metrics=metrics, path=path)

@login_required
@app.route("/Monitor", methods=["GET", "POST"])
def Monitor_Food():

    df = func.get_orders(MAIN_URL, STALL_ID)
    df = df.loc[df["STATUS"] == "READY"][["ID_ORDER","NAME", "PRICE", "STATUS"]]
    df_box = mdls.Stall.BOX_STATUS(MAIN_URL, STALL_ID)
    df = df.loc[~(df["ID_ORDER"].isin(df_box["ID_ORDER"]))]
    form = mdls.ALLOCATE()
    if form.validate_on_submit() and (res:=request.form.get("Button_Value")):
        if form.Allocate.data:
            ID_BOX = df_box.loc[df_box["STATUS"] == "UNOCCUPIED"]["ID_BOX"].values
            if ID_BOX.size >= 1:
                mdls.Stall.UPDATE_ORDER_BOX(MAIN_URL, ID_BOX[0], res)
        elif form.Release.data:
            mdls.Stall.UPDATE_ORDER_BOX(MAIN_URL, res, 0)
        else:
            pass

    return render_template("Monitor.html", data=df, data_box=df_box, form=form)

@login_required
@app.route("/About")
def About():
    return render_template("About.html")

if __name__ == "__main__":
    UI.run()