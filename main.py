from io import BytesIO
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from fasthtml.common import *
import datetime as dt

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PASSWORD = os.getenv("PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

BUTTON_STYLE = (
    "display: block; "
    "width: 220px; "
    "padding: 12px; "
    "margin: 25px 0; "
    "text-align: center; "
    "font-size: 18px; "
    "border-radius: 8px; "
    "background-color: #1e88e5; "
    "color: white; "
    "text-decoration: none; "
)

LABEL_STYLE = "width: 35%; font-weight: bold; padding-right: 10px; padding-bottom: 20px; text-align: right;"
INPUT_STYLE = "width: 65%; padding: 6px;"
BACK_BUTTON_STYLE = BUTTON_STYLE + "background: #555;"
SUBMIT_BUTTON_STYLE = BUTTON_STYLE + "background: #1e88e5;"

TABLE_STYLES = Style("""
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 16px;
}

.data-table th, .data-table td {
    padding: 4px 8px;
    border-bottom: 1px solid #333;
    text-align: left;
    white-space: nowrap;
}

.data-table th {
    background: #222;
    color: white;
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 2;
    text-align: left;
}
               
.data-table td {
    font-weight: normal;
}
""")

SUPABASE = create_client(SUPABASE_URL, SUPABASE_KEY)
app, rt = fast_app(hdrs=[TABLE_STYLES])

# Convert DataFrame to HTML table with clickable links
def df_to_html_table(df, link_trans_id=False, link_barcode=False):
    if df.empty:
        return P("No data found.")

    df = df.astype(str)

    header = Thead(Tr(*[Th(col) for col in df.columns]))

    body_rows = []
    for _, row in df.iterrows():
        cells = []

        for col in df.columns:
            value = row[col]

            # Clickable Trans ID ONLY if enabled
            if col == "Trans ID" and link_trans_id:
                value = A(
                    value,
                    href=f"/edit_transaction?trans_id={row['Trans ID']}",
                    style="color:#1e88e5; text-decoration:none;"
                )

            # Clickable Barcode ONLY if enabled
            elif col == "Barcode" and link_barcode:
                value = A(
                    value,
                    href=f"/edit_barcode?barcode={row['Barcode']}",
                    style="color:#1e88e5; text-decoration:none;"
                )

            cells.append(Td(value))

        body_rows.append(Tr(*cells))

    return Table(header, Tbody(*body_rows), cls="data-table")

# Login page
@rt("/", methods=["GET", "POST"])
def login(password: str | None = None):
    error_message = None

    # Check if the user input password is correct
    if password is not None:
        if password == PASSWORD:
            # Go to the home page and set session cookie if password is correct
            return Response(
                status_code=302,
                headers={
                    "Location": "/home",
                    "Set-Cookie": f"session={SECRET_KEY}; Path=/; Max-Age=3600; HttpOnly"
                }
            )
        else:
            error_message = "Incorrect password"

    return Title("Login to Quality Inventory"), Titled(
        Div(
            H2("Enter Password"),
            Form(
                Input(type="password", name="password", placeholder="Password", required=True),
                Input(type="submit", value="Login", style=SUBMIT_BUTTON_STYLE),
                method="POST"
            ),
            P(error_message, style="color:red;") if error_message else Div() # Display an error message if the password is incorrect
        )
    )

# Home page (requires login)
@rt("/home")
def home(req):
    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    return Title("Quality Inventory Home"), Titled(
    Div(
        H1("Quality Inventory", cls="mb-4", style="width: 97%; text-align:center;"),
        Div(
            A("Add New Item", href="/add_item", style=BUTTON_STYLE),
            A("Remove Item", href="/remove_item", style=BUTTON_STYLE),
            A("Transactions", href="/transactions", style=BUTTON_STYLE),
            A("Barcodes", href="/barcodes", style=BUTTON_STYLE),
            A("Inventory", href="/inventory", style=BUTTON_STYLE),
            A("Export Data To Excel", href="/export_excel", target="_blank", style=BUTTON_STYLE),
            style="max-width: 260px; margin: auto; margin-top: 40px;"
        )
    )
)

# Form to add new item into inventory
@rt("/add_item", methods=["GET", "POST"])
def add_item(
            req,
            values: dict | None = None,
            error_message: str | None = None,
            barcode: str | None = None,
            item_number: str | None = None,
            description: str | None = None,
            lot_number: str | None = None,
            exp_date: str | None = None,
            employee: str | None = None,
            item_type: str | None = None):

    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    # If no POST data → render form
    if barcode is None and item_number is None:
        return Title("Add New Item"), Titled(
            Div(
                H2("Add New Item", cls="mb-4", style="width: 105%; text-align:center;"),
                Div(
                    P(error_message, style="width: 105%; color:red; margin-bottom:15px;"),
                    style="text-align:center;"
                ) if error_message else Div(), # Display error message if any
                Form(
                    Div(Label("Barcode", style=LABEL_STYLE),
                        Input(type="text", name="barcode", required=True,
                              value=values.get("barcode", "") if values else "",
                              style=INPUT_STYLE),
                        style="display:flex; align-items:center; margin-bottom: 15px;"),
                    Div(Label("Item #", style=LABEL_STYLE),
                        Input(type="text", name="item_number", required=True,
                              value=values.get("item_number", "") if values else "",
                              style=INPUT_STYLE),
                        style="display:flex; align-items:center; margin-bottom: 15px;"),
                    Div(Label("Description", style=LABEL_STYLE),
                        Input(type="text", name="description", required=True,
                              value=values.get("description", "") if values else "",
                              style=INPUT_STYLE),
                        style="display:flex; align-items:center; margin-bottom: 15px;"),
                    Div(Label("Lot #", style=LABEL_STYLE),
                        Input(type="text", name="lot_number", required=True,
                              value=values.get("lot_number", "") if values else "",
                              style=INPUT_STYLE),
                        style="display:flex; align-items:center; margin-bottom: 15px;"),
                    Div(Label("Exp Date", style=LABEL_STYLE),
                        Input(type="date", name="exp_date", required=True,
                              value=values.get("exp_date", "") if values else "",
                              style=INPUT_STYLE),
                        style="display:flex; align-items:center; margin-bottom: 15px;"),
                    Div(Label("Type", style=LABEL_STYLE),
                        Select(
                            *[Option(text, value=text,
                                     selected=(values and values.get("item_type") == text))
                              for text in ["Vendor Damage", "Damage", "Expired", "Short Dated"]],
                            name="item_type", required=True, style=INPUT_STYLE),
                        style="display:flex; align-items:center; margin-bottom: 15px;"),
                    Div(Label("Employee", style=LABEL_STYLE),
                        Input(type="text", name="employee", required=True,
                              value=values.get("employee", "") if values else "",
                              style=INPUT_STYLE),
                        style="display:flex; align-items:center; margin-bottom: 15px;"),
                    Div(
                        A("Back", href="/home", style=BACK_BUTTON_STYLE + "margin-left: 100px; text-align:center; text-decoration:none; display:inline-block;"),
                        Button("Submit", type="submit", style=SUBMIT_BUTTON_STYLE),
                        style="display:flex; justify-content: space-between; margin-top: 20px;"
                    ),
                    method="POST", action="/add_item", style="max-width: 600px; margin: auto;"
                )
            )
        )

    # Get user input values
    values = {
        "barcode": barcode or "",
        "item_number": item_number or "",
        "description": description or "",
        "lot_number": lot_number or "",
        "exp_date": exp_date or "",
        "employee": employee or "",
        "item_type": item_type or ""
    }

    # Check user input for errors
    errors = []
    if len(values["barcode"]) != 6:
        errors.append("Barcode must be exactly 6 characters.")
    if len(values["item_number"]) > 50:
        errors.append("Item # cannot exceed 50 characters.")
    if len(values["description"]) > 100:
        errors.append("Description cannot exceed 100 characters.")
    if len(values["lot_number"]) > 50:
        errors.append("Lot # cannot exceed 50 characters.")
    if len(values["item_type"]) > 50:
        errors.append("Type cannot exceed 50 characters.")
    if len(values["employee"]) > 50:
        errors.append("Employee cannot exceed 50 characters.")

    try:
        values["barcode"] = int(values["barcode"])
    except:
        errors.append("Barcode must be numeric.")

    response = SUPABASE.table("barcodes").select("barcode").eq("barcode", values["barcode"]).execute()
    if response.data:
        errors.append("Barcode already exists.")

    if not all(values.values()):
        errors.append("All fields are required.")

    if errors:
        # Re-render form with error
        return add_item(values=values, error_message=errors[0])

    # Insert into Supabase
    data = {
        "barcode": values["barcode"],
        "item_number": values["item_number"],
        "description": values["description"],
        "lot_number": values["lot_number"],
        "exp_date": values["exp_date"],
        "typ": values["item_type"],
        "add_remove": "Add",
        "trans_date": str(pd.Timestamp.now()),
        "employee": values["employee"]
    }
    bc_data = {
        "barcode": values["barcode"],
        "item_number": values["item_number"],
        "description": values["description"],
        "lot_number": values["lot_number"],
        "typ": values["item_type"],
        "exp_date": values["exp_date"]
    }

    SUPABASE.table("transactions").insert(data).execute()
    SUPABASE.table("barcodes").insert(bc_data).execute()

    return Redirect("/home")

# Form to remove item from inventory
@rt("/remove_item", methods=["GET", "POST"])
def remove_item(
    req,
    barcode: str | None = None,
    employee: str | None = None,
    error_message: str | None = None
):
    record = None

    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    # If barcode was submitted check if it is valid
    if barcode:
        response = SUPABASE.table("barcodes").select("*").eq("barcode", barcode).execute()

        if not response.data:
            error_message = "This barcode does not exist."
        else:
            record = response.data[0]

            # Already removed
            if record.get("remove") == 1:
                error_message = "This barcode has already been removed."
                record = None

    # If user clicked REMOVE button remove the item
    if error_message == "DO_REMOVE":
        if not employee:
            error_message = "Employee is required before removing an item."
            return remove_item(barcode=barcode, error_message=error_message)
    
        data = {
            "barcode": record.get("barcode"),
            "item_number": record.get("item_number"),
            "description": record.get("description"),
            "lot_number": record.get("lot_number"),
            "exp_date": record.get("exp_date"),
            "typ": record.get("typ"),
            "add_remove": "Remove",
            "trans_date": str(pd.Timestamp.now()),
            "employee": record.get("employee")
        }

        # Add the remove transaction and mark barcode as removed
        SUPABASE.table("transactions").insert(data).execute()
        SUPABASE.table("barcodes").update({"remove": 1}).eq("barcode", record.get("barcode")).execute()
        return Redirect("/home")

    # Render page
    return Title("Remove Item"), Titled(
        Div(
            H2("Remove Item", style="text-align:center; margin-bottom:20px;"),
            Div(
                P(error_message, style="color:red; font-size:18px; margin-bottom:15px;"),
                style="text-align:center;"
            ) if error_message and error_message != "DO_REMOVE" else Div(), # Display error message if any

            # Barcode input form
            Form(
                Div(
                    Label("Barcode", style="width: 12%; font-weight:bold; text-align:left;"),
                    Input(type="text", name="barcode", placeholder="Enter Barcode",
                          value=barcode or "", style="width: 12%; padding:6px; margin-top:15px;"),
                    Button("Search", type="submit", style=SUBMIT_BUTTON_STYLE),
                    style="display:flex; align-items:center; gap:10px; justify-content:center;"
                ),
                method="POST",
                style="margin-bottom:30px;"
            ),

            # If valid record found → Show info
            Div(
                *( 
                    [
                        Div(
                            Label("Item #", style="width: 35%; font-weight:bold; align-items:left;"),
                            P(record.get("item_number"), style="width:40%; font-weight:normal;"),
                            style="display:flex; margin-bottom:10px;"
                        ),
                        Div(
                            Label("Description", style="width: 35%; font-weight:bold; align-items:left;"),
                            P(record.get("description"), style="width:40%; font-weight:normal;"),
                            style="display:flex; margin-bottom:10px;"
                        ),
                        Div(
                            Label("Lot #", style="width: 35%; font-weight:bold; align-items:left;"),
                            P(record.get("lot_number"), style="width:40%; font-weight:normal;"),
                            style="display:flex; margin-bottom:10px;"
                        ),
                        Div(
                            Label("Exp Date", style="width: 35%; font-weight:bold; align-items:left;"),
                            P(record.get("exp_date"), style="width:40%; font-weight:normal;"),
                            style="display:flex; margin-bottom:10px;"
                        ),
                        Div(
                            Label("Type", style="width: 35%; font-weight:bold; align-items:left;"),
                            P(record.get("typ"), style="width:40%; font-weight:normal;"),
                            style="display:flex; margin-bottom:10px;"
                        ),
                        Div(
                            Label("Employee", style="width: 35%; font-weight:bold; align-items:left;"),
                            Input(type="text", name="employee", style="width:40%; font-weight:normal;", required=True),
                            style="display:flex; margin-bottom:10px;"
                        )
                    ] if record else []
                ),

                # Bottom Buttons
                Div(
                    A("Back", href="/home", style=BACK_BUTTON_STYLE),
                    
                    # Remove button posts a special flag "DO_REMOVE"
                    Form(
                        Input(type="hidden", name="barcode", value=barcode or ""),
                        Input(type="hidden", name="employee", value=employee or ""),
                        Input(type="hidden", name="error_message", value="DO_REMOVE"),
                        Button("Remove", type="submit", style=SUBMIT_BUTTON_STYLE + "background:#d9534f;"),
                        method="POST"
                    ) if record else Div(),

                    style="display:flex; justify-content:space-between; margin-top:30px;"
                ),

                style="max-width:600px; margin:auto;"
            )
        )
    )

# Form to view, edit, and filter transactions
@rt("/transactions", methods=["GET", "POST"])
def transactions(
    req,
    barcode: str | None = None,
    item_number: str | None = None,
    description: str | None = None,
    lot_number: str | None = None,
    exp_date: str | None = None,
    item_type: str | None = None,
    trans_date_begin: str | None = None,
    trans_date_end: str | None = None,
    employee: str | None = None
):
    
    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    # Track input errors
    input_errors = {}

    # Read Supabase table and reformat
    response = SUPABASE.table("transactions").select("*").execute()
    df = pd.DataFrame(response.data)
    df = df[["trans_id", "barcode", "item_number", "description", "lot_number", "exp_date", "typ", "add_remove", "trans_date", "employee"]]
    df.columns = ["Trans ID", "Barcode", "Item #", "Description", "Lot #", "Exp Date", "Type", "Add/Remove", "Trans Date", "Employee"]
    df["Trans Date"] = pd.to_datetime(df["Trans Date"]).dt.floor("s")
    df.sort_values(by="Trans ID", ascending=False, inplace=True)

    # Apply filters
    if barcode: df = df[df["Barcode"].str.contains(barcode, case=False, na=False)]
    if item_number: df = df[df["Item #"].str.contains(item_number, case=False, na=False)]
    if description: df = df[df["Description"].str.contains(description, case=False, na=False)]
    if lot_number: df = df[df["Lot #"].str.contains(lot_number, case=False, na=False)]
    if exp_date: df = df[df["Exp Date"].astype(str).str.contains(exp_date, na=False)]
    if item_type: df = df[df["Type"].str.contains(item_type, case=False, na=False)]
    if employee: df = df[df["Employee"].str.contains(employee, case=False, na=False)]

    # Handle date filters with error highlighting
    if trans_date_begin:
        try:
            df = df[df["Trans Date"] >= pd.to_datetime(trans_date_begin)]
        except Exception as e:
            input_errors["trans_date_begin"] = True

    if trans_date_end:
        try:
            df = df[df["Trans Date"] <= pd.to_datetime(trans_date_end)]
        except Exception as e:
            input_errors["trans_date_end"] = True

    table = df_to_html_table(df, link_trans_id=True, link_barcode=False)

    # Filter row above table
    filter_row = Form(
        Div(
            Input(
                type="text",
                name="barcode",
                placeholder="Barcode",
                value=barcode or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="item_number",
                placeholder="Item #",
                value=item_number or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="description",
                placeholder="Description",
                value=description or "",
                style="width:160px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="lot_number",
                placeholder="Lot #",
                value=lot_number or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="exp_date",
                placeholder="Exp Date",
                value=exp_date or "",
                style="width:160px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="item_type",
                placeholder="Type",
                value=item_type or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="trans_date_begin",
                placeholder="Trans Date Begin",
                value=trans_date_begin or "",
                style="width:160px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="trans_date_end",
                placeholder="Trans Date End",
                value=trans_date_end or "",
                style="width:160px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="employee",
                placeholder="Employee",
                value=employee or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Button("Filter", type="submit", style=SUBMIT_BUTTON_STYLE),
            style="display:flex; flex-wrap: nowrap; overflow-x:auto; align-items:center;"
        ),
        method="POST"
    )

    # Render page
    return Title("Transactions"), Titled(
        Div(
            H2("Transactions", style="text-align:center; margin-bottom:20px;"),
            filter_row,
            Div(
                table,
                style=(
                    "height: 65vh; "
                    "overflow-y: auto; "
                    "border: 1px solid #444; "
                    "padding: 10px; "
                    "border-radius: 8px; margin-top:10px;"
                )
            ),
            # Buttons
            Div(
                A("Back", href="/home", style=BACK_BUTTON_STYLE + "text-align:center; text-decoration:none; display:inline-block;"),
                #Button("Submit", type="submit", style=SUBMIT_BUTTON_STYLE),
                style="display:flex; justify-content: space-between; margin-top: 20px;"
            ),
            style="max-width: 125%; margin:auto;"
        )
    )

# Form to edit existing transaction
@rt("/edit_transaction", methods=["GET", "POST"])
def edit_transaction(
    req,
    trans_id: str,
    barcode: str | None = None,
    item_number: str | None = None,
    description: str | None = None,
    lot_number: str | None = None,
    exp_date: str | None = None,
    add_remove: str | None = None,
    item_type: str | None = None,
    employee: str | None = None,
    delete: str | None = None,
    error_message: str | None = None,
    values: dict | None = None
):  
    
    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")


    # If DELETE button clicked, delete the record
    if delete == "DO_DELETE":
        SUPABASE.table("transactions").delete().eq("trans_id", trans_id).execute()
        return Redirect("/transactions")

    # Fetch record from Supabase
    response = SUPABASE.table("transactions").select("*").eq("trans_id", trans_id).execute()
    if not response.data:
        return Titled(P("Record not found.", style="color:red; text-align:center;"))

    record = response.data[0]

    # If POST, update the record
    if barcode or item_number or description or lot_number or exp_date or item_type or employee:
        # Use the provided values if present, otherwise fallback to None
        new_values = {
            "barcode": barcode or None,
            "item_number": item_number or None,
            "description": description or None,
            "lot_number": lot_number or None,
            "exp_date": exp_date or None,
            "typ": item_type or None,
            "add_remove": add_remove or None,
            "employee": employee or None
        }

        # User input validation
        errors = []
        if new_values["barcode"] and len(new_values["barcode"]) != 6:
            errors.append("Barcode must be exactly 6 characters.")
        if new_values["item_number"] and len(new_values["item_number"]) > 50:
            errors.append("Item # cannot exceed 50 characters.")
        if new_values["description"] and len(new_values["description"]) > 100:
            errors.append("Description cannot exceed 100 characters.")
        if new_values["lot_number"] and len(new_values["lot_number"]) > 50:
            errors.append("Lot # cannot exceed 50 characters.")
        if new_values["add_remove"] and len(new_values["add_remove"]) > 50:
            errors.append("Add/Remove cannot exceed 50 characters.")
        if new_values["employee"] and len(new_values["employee"]) > 50:
            errors.append("Employee cannot exceed 50 characters.")
        if errors:
            return edit_transaction(trans_id, error_message=errors[0], values=new_values)

        # Update Supabase with new values
        SUPABASE.table("transactions").update(new_values).eq("trans_id", trans_id).execute()
        return Redirect("/transactions")

    # If GET, render the page
    return Title("Edit Transaction"), Titled(
        Div(
            H2(f"Edit Transaction: {trans_id}", cls="mb-4", style="width: 105%; text-align:center;"),
            Div(
                P(error_message, style="width: 105%; color:red; margin-bottom:15px;"),
                style="text-align:center;"
            ) if error_message else Div(),

            Form(
                Div(
                    Label("Barcode", style=LABEL_STYLE),
                    Input(
                        type="text", name="barcode",
                        value=values.get("barcode", "") if values else (barcode or ""),
                        placeholder=record.get("barcode", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Item #", style=LABEL_STYLE),
                    Input(
                        type="text", name="item_number",
                        value=values.get("item_number", "") if values else (item_number or ""),
                        placeholder=record.get("item_number", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Description", style=LABEL_STYLE),
                    Input(
                        type="text", name="description",
                        value=values.get("description", "") if values else (description or ""),
                        placeholder=record.get("description", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Lot #", style=LABEL_STYLE),
                    Input(
                        type="text", name="lot_number",
                        value=values.get("lot_number", "") if values else (lot_number or ""),
                        placeholder=record.get("lot_number", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Exp Date", style=LABEL_STYLE),
                    Input(
                        type="text", name="exp_date",
                        value=values.get("exp_date", "") if values else (exp_date or ""),
                        placeholder=record.get("exp_date", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Type", style=LABEL_STYLE),
                    Select(
                        *[
                            Option(text, value=text,
                                selected=((values.get("item_type", "") if values else (item_type or record.get("typ"))) == text))
                            for text in ["Vendor Damage", "Damage", "Expired", "Short Dated"]
                        ],
                        name="item_type",
                        required=True,
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Add/Remove", style=LABEL_STYLE),
                    Select(
                        *[
                            Option(text, value=text,
                                selected=((values.get("add_remove", "") if values else (add_remove or record.get("add_remove"))) == text))
                            for text in ["Add", "Remove"]
                        ],
                        name="add_remove",
                        required=True,
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Employee", style=LABEL_STYLE),
                    Input(
                        type="text", name="employee",
                        value=values.get("employee", "") if values else (employee or ""),
                        placeholder=record.get("employee", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),

                # Buttons
                Div(
                    A("Back", href="/transactions", style=BACK_BUTTON_STYLE + "margin-left: 100px; text-align:center; text-decoration:none; display:inline-block;"),
                    Button("Delete", type="submit", name="delete", value="DO_DELETE",
                        style=SUBMIT_BUTTON_STYLE + "background:#d9534f; margin-left:20px; margin-right:20px;"),
                    Button("Submit", type="submit", style=SUBMIT_BUTTON_STYLE),
                    style="display:flex; justify-content: space-between; margin-top: 20px;"
                ),
                method="POST",
                style="max-width: 600px; margin: auto;"
            )
        )
    )

# Form to view and filter barcodes
@rt("/barcodes", methods=["GET", "POST"])
def barcodes(
    req,
    barcode: str | None = None,
    item_number: str | None = None,
    description: str | None = None,
    lot_number: str | None = None,
    exp_date: str | None = None,
    item_type: str | None = None
):
    
    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    # Read Supabase table and reformat
    response = SUPABASE.table("barcodes").select("*").execute()
    df = pd.DataFrame(response.data)
    df = df[["barcode", "item_number", "description", "lot_number", "exp_date", "typ", "remove"]]
    df.columns = ["Barcode", "Item #", "Description", "Lot #", "Exp Date", "Type", "Remove"]
    df.sort_values(by="Barcode", ascending=False, inplace=True)

    # Apply filters
    if barcode: df = df[df["Barcode"].str.contains(barcode, case=False, na=False)]
    if item_number: df = df[df["Item #"].str.contains(item_number, case=False, na=False)]
    if description: df = df[df["Description"].str.contains(description, case=False, na=False)]
    if lot_number: df = df[df["Lot #"].str.contains(lot_number, case=False, na=False)]
    if exp_date: df = df[df["Exp Date"].astype(str).str.contains(exp_date, na=False)]
    if item_type: df = df[df["Type"].str.contains(item_type, case=False, na=False)]

    table = df_to_html_table(df, link_trans_id=False, link_barcode=True)

    # Filter row above table
    filter_row = Form(
        Div(
            Input(
                type="text",
                name="barcode",
                placeholder="Barcode",
                value=barcode or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="item_number",
                placeholder="Item #",
                value=item_number or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="description",
                placeholder="Description",
                value=description or "",
                style="width:160px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="lot_number",
                placeholder="Lot #",
                value=lot_number or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="exp_date",
                placeholder="Exp Date",
                value=exp_date or "",
                style="width:160px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="item_type",
                placeholder="Type",
                value=item_type or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Button("Filter", type="submit", style=SUBMIT_BUTTON_STYLE),
            style="display:flex; flex-wrap: nowrap; overflow-x:auto; align-items:center;"
        ),
        method="POST"
    )

    # Render page
    return Title("Barcodes"), Titled(
        Div(
            H2("Barcodes", style="text-align:center; margin-bottom:20px;"),
            filter_row,
            Div(
                table,
                style=(
                    "height: 65vh; "
                    "overflow-y: auto; "
                    "border: 1px solid #444; "
                    "padding: 10px; "
                    "border-radius: 8px; margin-top:10px;"
                )
            ),
            # Buttons
            Div(
                A("Back", href="/home", style=BACK_BUTTON_STYLE + "text-align:center; text-decoration:none; display:inline-block;"),
                #Button("Submit", type="submit", style=SUBMIT_BUTTON_STYLE),
                style="display:flex; justify-content: space-between; margin-top: 20px;"
            ),
            style="max-width: 125%; margin:auto;"
        )
    )

# Form to edit existing barcode
@rt("/edit_barcode", methods=["GET", "POST"])
def edit_barcode(
    req,
    barcode: str | None = None,
    item_number: str | None = None,
    description: str | None = None,
    lot_number: str | None = None,
    exp_date: str | None = None,
    remove: str | None = None,
    item_type: str | None = None,
    delete: str | None = None,
    error_message: str | None = None,
    values: dict | None = None
):  
    
    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    # If DELETE button clicked, delete the record
    if delete == "DO_DELETE":
        SUPABASE.table("barcodes").delete().eq("barcode", barcode).execute()
        return Redirect("/barcodes")

    # Get record from Supabase
    response = SUPABASE.table("barcodes").select("*").eq("barcode", barcode).execute()
    if not response.data:
        return Titled(P("Record not found.", style="color:red; text-align:center;"))

    record = response.data[0]

    # If POST, update the record with user input
    if item_number or description or lot_number or exp_date or item_type or remove:
        # Use the provided values if present, otherwise fallback to the current record
        new_values = {
            "item_number": item_number or None,
            "description": description or None,
            "lot_number": lot_number or None,
            "exp_date": exp_date or None,
            "typ": item_type or None,
            "remove": remove or None
        }

        # Validate user input
        errors = []
        if new_values["item_number"] is not None and len(new_values["item_number"]) > 50:
            errors.append("Item # cannot exceed 50 characters.")
        if new_values["description"] is not None and len(new_values["description"]) > 100:
            errors.append("Description cannot exceed 100 characters.")
        if new_values["lot_number"] is not None and len(new_values["lot_number"]) > 50:
            errors.append("Lot # cannot exceed 50 characters.")
        if new_values["remove"] is not None and len(new_values["remove"]) > 50:
            errors.append("Remove cannot exceed 50 characters.")
        if errors:
            return edit_barcode(barcode, error_message=errors[0], values=new_values)

        # Update Supabase
        SUPABASE.table("barcodes").update(new_values).eq("barcode", barcode).execute()
        return Redirect("/barcodes")

    # If GET, render the page
    return Title("Edit Barcode"), Titled(
        Div(
            H2(f"Edit Barcode: {barcode}", cls="mb-4", style="width: 105%; text-align:center;"),
            Div(
                P(error_message, style="width: 105%; color:red; margin-bottom:15px;"),
                style="text-align:center;"
            ) if error_message else Div(),

            Form(
                Div(
                    Label("Item #", style=LABEL_STYLE),
                    Input(
                        type="text", name="item_number",
                        value=values.get("item_number", "") if values else (item_number or ""),
                        placeholder=record.get("item_number", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Description", style=LABEL_STYLE),
                    Input(
                        type="text", name="description",
                        value=values.get("description", "") if values else (description or ""),
                        placeholder=record.get("description", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Lot #", style=LABEL_STYLE),
                    Input(
                        type="text", name="lot_number",
                        value=values.get("lot_number", "") if values else (lot_number or ""),
                        placeholder=record.get("lot_number", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Exp Date", style=LABEL_STYLE),
                    Input(
                        type="text", name="exp_date",
                        value=values.get("exp_date", "") if values else (exp_date or ""),
                        placeholder=record.get("exp_date", ""),
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Type", style=LABEL_STYLE),
                    Select(
                        *[
                            Option(text, value=text,
                                selected=((values.get("item_type", "") if values else (item_type or record.get("typ"))) == text))
                            for text in ["Vendor Damage", "Damage", "Expired", "Short Dated"]
                        ],
                        name="item_type",
                        required=True,
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),
                Div(
                    Label("Remove", style=LABEL_STYLE),
                    Select(
                        *[
                            Option(text, value=text,
                                selected=((values.get("remove", "") if values else (remove or record.get("remove"))) == text))
                            for text in ["Add", "Remove"]
                        ],
                        name="remove",
                        required=True,
                        style=INPUT_STYLE
                    ),
                    style="display:flex; align-items:center; margin-bottom: 15px;"
                ),

                # Buttons
                Div(
                    A("Back", href="/barcodes", style=BACK_BUTTON_STYLE + "margin-left: 100px; text-align:center; text-decoration:none; display:inline-block;"),
                    Button("Delete", type="submit", name="delete", value="DO_DELETE",
                        style=SUBMIT_BUTTON_STYLE + "background:#d9534f; margin-left:20px; margin-right:20px;"),
                    Button("Submit", type="submit", style=SUBMIT_BUTTON_STYLE),
                    style="display:flex; justify-content: space-between; margin-top: 20px;"
                ),
                method="POST",
                style="max-width: 600px; margin: auto;"
            )
        )
    )

# Form to view current inventory with filters
@rt("/inventory")
def inventory(
    req,
    item_number: str | None = None,
    lot_number: str | None = None,
    exp_date: str | None = None,
    item_type: str | None = None
):
    
    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    # Read Supabase table
    response = SUPABASE.table("barcodes").select("*").execute()
    df = pd.DataFrame(response.data)

    # Render message if no inventory
    if df.empty:
        return Title("Inventory"), Titled(
            Div(
                H2("Inventory", style="text-align:center; margin-bottom:20px;"),
                P("No inventory found.", style="text-align:center;"),
                A("Back", href="/", style=BACK_BUTTON_STYLE),
                style="max-width:600px; margin:auto;"
            )
        )

    # Calculate current inventory
    df = df[df["remove"] == 0]

    grouped = (
        df.groupby(["item_number", "lot_number", "exp_date", "typ"])
          .agg(quantity=("barcode", "count"))
          .reset_index()
    )

    # Update inventory table in Supabase
    SUPABASE.table("inventory").delete().neq("id", 0).execute()
    SUPABASE.table("inventory").insert(grouped.to_dict(orient="records")).execute()

    grouped.columns = ["Item #", "Lot #", "Exp Date", "Type", "Quantity"]

    # Apply filters
    if item_number: grouped = grouped[grouped["Item #"].str.contains(item_number, case=False, na=False)]
    if lot_number: grouped = grouped[grouped["Lot #"].str.contains(lot_number, case=False, na=False)]
    if exp_date: grouped = grouped[grouped["Exp Date"].astype(str).str.contains(exp_date, na=False)]
    if item_type: grouped = grouped[grouped["Type"].str.contains(item_type, case=False, na=False)]

    table = df_to_html_table(grouped)

    # Filter row above table
    filter_row = Form(
        Div(
            Input(
                type="text",
                name="item_number",
                placeholder="Item #",
                value=item_number or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="lot_number",
                placeholder="Lot #",
                value=lot_number or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="exp_date",
                placeholder="Exp Date",
                value=exp_date or "",
                style="width:160px; margin-right:5px; margin-top:15px;"
            ),
            Input(
                type="text",
                name="item_type",
                placeholder="Type",
                value=item_type or "",
                style="width:120px; margin-right:5px; margin-top:15px;"
            ),
            Button("Filter", type="submit", style=SUBMIT_BUTTON_STYLE),
            style="display:flex; flex-wrap: nowrap; overflow-x:auto; align-items:center;"
        ),
        method="POST"
    )

    # Render page
    return Title("Inventory"), Titled(
        Div(
            H2("Inventory", style="text-align:center; margin-bottom:20px;"),
            filter_row,
            Div(
                table,
                style=(
                    "height: 70vh; "
                    "overflow-y: auto; "
                    "border: 1px solid #444; "
                    "padding: 10px; "
                    "border-radius: 8px; margin-top:10px;"
                )
            ),

            Div(
                A("Back", href="/home", style=BACK_BUTTON_STYLE),
                style="margin-top: 20px; text-align:center;"
            ),

            style="max-width: 125%; margin:auto;"
        )
    )

# Export data to Excel
@rt("/export_excel")
def export_excel(req):
    # Check if the user is logged in by verifying the session cookie
    if req.cookies.get("session") != SECRET_KEY:
        return Redirect("/")

    # Fetch data from Supabase and reformat
    df_transactions = pd.DataFrame(SUPABASE.table("transactions").select("*").execute().data)
    df_transactions = df_transactions[["trans_id", "barcode", "item_number", "description", "lot_number", "exp_date", "typ", "add_remove", "trans_date", "employee"]]
    df_transactions.sort_values(by="trans_id", ascending=False, inplace=True)
    df_barcodes = pd.DataFrame(SUPABASE.table("barcodes").select("*").execute().data)
    df_barcodes = df_barcodes[["barcode", "item_number", "description", "lot_number", "exp_date", "typ", "remove"]]
    df_barcodes.sort_values(by="barcode", ascending=False, inplace=True)

    # Create inventory sheet
    if not df_barcodes.empty:
        df_inventory = df_barcodes[df_barcodes["remove"] == 0].groupby(
            ["item_number", "lot_number", "exp_date", "typ"], as_index=False
        ).agg({"barcode": "count"}).rename(columns={"barcode": "Quantity"})
    else:
        df_inventory = pd.DataFrame()

    # Write Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_transactions.to_excel(writer, sheet_name="Transactions", index=False)
        df_barcodes.to_excel(writer, sheet_name="Barcodes", index=False)
        df_inventory.to_excel(writer, sheet_name="Inventory", index=False)
    output.seek(0)

    today = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return Response(
        output.read(),
        headers={
            "Content-Disposition": f"attachment; filename=quality_inv_data_{today}.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    )

serve()