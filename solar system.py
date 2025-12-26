import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import requests  
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def calculate_pv_system(
    household_load_w,
    days_of_autonomy,
    battery_dod,
    sun_hours_per_day,
    battery_voltage_options,
    pv_panel_cost_per_watt,
    battery_cost_per_wh,
    charge_controller_cost_per_amp,
    inverter_cost=0,
    other_costs=0,
    solar_safety_factor=1.2,
    controller_safety_factor=1.25,
    electricity_cost_per_kwh=0.15,
    panel_efficiency=0.18,
    system_lifetime_years=25,
    battery_cycle_life=1000,
    annual_maintenance_cost=0,
    subsidy=0
):
    """
    Calculates the components and initial cost of a PV system.
    
    Parameters:
    - household_load_w: Average household power consumption in watts
    - days_of_autonomy: Number of days the battery should power the house without sun
    - battery_dod: Battery depth of discharge (0.1-1.0)
    - sun_hours_per_day: Average peak sun hours per day
    - battery_voltage_options: List of possible battery system voltages
    - pv_panel_cost_per_watt: Cost of solar panels per watt
    - battery_cost_per_wh: Cost of battery storage per watt-hour
    - charge_controller_cost_per_amp: Cost of charge controller per amp
    - inverter_cost: Cost of the inverter
    - other_costs: Additional system costs
    - solar_safety_factor: Safety margin for solar panel sizing
    - controller_safety_factor: Safety margin for charge controller sizing
    - electricity_cost_per_kwh: Local electricity cost per kWh
    - panel_efficiency: Solar panel efficiency (0.1-0.25)
    - system_lifetime_years: Expected lifetime of the system in years
    - battery_cycle_life: Battery cycle life in days
    - annual_maintenance_cost: Annual maintenance cost
    - subsidy: Government subsidy or grant
    
    Returns a dictionary with system specifications and costs
    """
    # Input validation
    if household_load_w <= 0:
        raise ValueError("Household load must be greater than zero")
    if days_of_autonomy <= 0:
        raise ValueError("Days of autonomy must be greater than zero")
    if battery_dod <= 0 or battery_dod > 1:
        raise ValueError("Battery depth of discharge must be between 0 and 1")
    if sun_hours_per_day <= 0:
        raise ValueError("Sun hours per day must be greater than zero")
    if not battery_voltage_options:
        raise ValueError("At least one battery voltage option must be provided")
    
    # Calculate daily energy consumption in watt-hours
    daily_energy_wh = household_load_w * 24
    
    # Calculate required battery capacity in watt-hours
    required_battery_capacity_wh = daily_energy_wh * days_of_autonomy / battery_dod
    
    # Calculate best battery option
    best_battery_option = None
    lowest_battery_cost = float('inf')
    
    for voltage in battery_voltage_options:
        amp_hours = required_battery_capacity_wh / voltage
        battery_cost = battery_cost_per_wh * required_battery_capacity_wh
        
        if battery_cost < lowest_battery_cost or best_battery_option is None:
            lowest_battery_cost = battery_cost
            best_battery_option = {
                'voltage': voltage,
                'amp_hours': amp_hours,
                'cost': battery_cost
            }
    
    # Calculate solar panel size considering efficiency
    solar_panel_size_w = (daily_energy_wh / (sun_hours_per_day * panel_efficiency)) * solar_safety_factor
    solar_panel_cost = solar_panel_size_w * pv_panel_cost_per_watt
    
    # Calculate charge controller size
    charge_controller_amp_rating = (solar_panel_size_w / best_battery_option['voltage']) * controller_safety_factor
    charge_controller_cost = charge_controller_amp_rating * charge_controller_cost_per_amp
    
    # Battery replacements over system life
    battery_replacements = max(0, int(system_lifetime_years * 365 / battery_cycle_life) - 1)
    total_battery_cost = best_battery_option['cost'] * (1 + battery_replacements)
    
    # Calculate total system cost including maintenance and subsidy
    total_system_cost = (
        solar_panel_cost + total_battery_cost + charge_controller_cost + inverter_cost + other_costs
    )
    total_system_cost += annual_maintenance_cost * system_lifetime_years
    total_system_cost -= subsidy  # Apply subsidy

    # Calculate energy production and savings
    annual_energy_production_kwh = daily_energy_wh * 365 / 1000
    annual_savings = annual_energy_production_kwh * electricity_cost_per_kwh
    
    # Calculate payback period
    payback_years = total_system_cost / annual_savings if annual_savings > 0 else float('inf')
    
    # Calculate lifetime savings
    lifetime_savings = annual_savings * system_lifetime_years - total_system_cost
    
    # Calculate CO2 emissions reduction (average 0.85 kg CO2 per kWh of grid electricity)
    co2_reduction_kg_per_year = annual_energy_production_kwh * 0.85
    lifetime_co2_reduction_kg = co2_reduction_kg_per_year * system_lifetime_years
    
    # Return the system design with detailed information
    return {
        'best_battery_option': best_battery_option,
        'solar_panel_size_w': solar_panel_size_w,
        'charge_controller_amp_rating': charge_controller_amp_rating,
        'total_system_cost': total_system_cost,
        'daily_energy_wh': daily_energy_wh,
        'required_battery_capacity_wh': required_battery_capacity_wh,
        'payback_years': payback_years,
        'annual_savings': annual_savings,
        'lifetime_savings': lifetime_savings,
        'annual_energy_production_kwh': annual_energy_production_kwh,
        'co2_reduction_kg_per_year': co2_reduction_kg_per_year,
        'lifetime_co2_reduction_kg': lifetime_co2_reduction_kg,
        'roi_percentage': (lifetime_savings / total_system_cost) * 100 if total_system_cost > 0 else 0,
        'battery_replacements': battery_replacements,
        'total_battery_cost': total_battery_cost,
        'annual_maintenance_cost': annual_maintenance_cost,
        'subsidy': subsidy
    }
# given price of solar panels, battieries and regional prices are based on on some website:
#https://www.pvxchange.com/
#https://www.cleanenergyreviews.info/blog/solar-panel-prices
#https://www.energysage.com/
#https://www.solarpowereurope.org/
#https://www.solarquotes.com.au/panels/prices/

# Solar panel database (sample)
SOLAR_PANELS = [
    {"name": "Economy 250W Panel", "watts": 250, "cost_per_watt": 0.70, "efficiency": 0.15},
    {"name": "Standard 300W Panel", "watts": 300, "cost_per_watt": 0.85, "efficiency": 0.18},
    {"name": "Premium 350W Panel", "watts": 350, "cost_per_watt": 1.10, "efficiency": 0.22},
    {"name": "Monocrystalline 400W Panel", "watts": 400, "cost_per_watt": 0.95, "efficiency": 0.20},
    {"name": "Monocrystalline 450W Panel", "watts": 450, "cost_per_watt": 1.00, "efficiency": 0.21},
    {"name": "PERC 360W Panel", "watts": 360, "cost_per_watt": 0.90, "efficiency": 0.19},
    {"name": "PERC 410W Panel", "watts": 410, "cost_per_watt": 0.98, "efficiency": 0.20},
    {"name": "Bifacial 380W Panel", "watts": 380, "cost_per_watt": 1.05, "efficiency": 0.21},
    {"name": "Bifacial 420W Panel", "watts": 420, "cost_per_watt": 1.15, "efficiency": 0.22},
    {"name": "HJT 390W Panel", "watts": 390, "cost_per_watt": 1.20, "efficiency": 0.22},
    {"name": "HJT 440W Panel", "watts": 440, "cost_per_watt": 1.25, "efficiency": 0.23},
    {"name": "N-Type 370W Panel", "watts": 370, "cost_per_watt": 1.00, "efficiency": 0.20},
    {"name": "N-Type 430W Panel", "watts": 430, "cost_per_watt": 1.15, "efficiency": 0.22},
    {"name": "Thin Film 320W Panel", "watts": 320, "cost_per_watt": 0.80, "efficiency": 0.17},
]

# Battery database (sample)
BATTERIES = [
    {"name": "Lead-Acid", "voltage": 12, "cost_per_wh": 0.15, "cycle_life": 500, "dod": 0.5},
    {"name": "AGM", "voltage": 12, "cost_per_wh": 0.22, "cycle_life": 1000, "dod": 0.7},
    {"name": "Lithium-Ion", "voltage": 48, "cost_per_wh": 0.35, "cycle_life": 3000, "dod": 0.8},
]

# Add regional price estimates
REGIONAL_PRICES = {
    "Europe": {
        "currency": "€",
        "solar_panel_per_watt": {"low": 0.65, "average": 0.80, "premium": 1.15},
        "battery_per_wh": {"lead_acid": 0.16, "agm": 0.23, "lithium": 0.37},
        "controller_per_amp": {"pwm": 5.0, "mppt": 8.5},
        "inverter_base": {"1kw": 320, "2kw": 550, "5kw": 950}
    },
    "Germany": {
        "currency": "€",
        "solar_panel_per_watt": {"low": 0.70, "average": 0.85, "premium": 1.20},
        "battery_per_wh": {"lead_acid": 0.18, "agm": 0.25, "lithium": 0.40},
        "controller_per_amp": {"pwm": 5.5, "mppt": 9.0},
        "inverter_base": {"1kw": 350, "2kw": 600, "5kw": 1000}
    }
}

# Function to estimate solar data based on location without external API
#https://globalsolaratlas.info/map
#https://pvwatts.nrel.gov/
#https://solargis.com/resources/free-maps-and-gis-data?locality=world
def estimate_sun_hours_by_latitude(latitude):
    """Estimates sun hours based on latitude only - no API needed"""
    equator_distance = abs(float(latitude))
    if equator_distance < 20:
        return 6.0  # Tropical regions
    elif equator_distance < 40:
        return 5.0  # Temperate regions
    else:
        return 4.0  # Polar regions

# Add common household appliances database
#https://energy-efficient-products.ec.europa.eu/ecodesign-and-energy-label_en
#https://www.energy.gov/energysaver/estimating-appliance-and-home-electronic-energy-use
COMMON_APPLIANCES = [
    {"name": "Refrigerator", "watts": 150, "hours": 24},
    {"name": "LED TV", "watts": 50, "hours": 4},
    {"name": "Lights", "watts": 60, "hours": 6},
    {"name": "Water Heater", "watts": 1000, "hours": 6},
    {"name": "Laptop", "watts": 70, "hours": 5},
    {"name": "Ceiling Fan", "watts": 75, "hours": 8},
    {"name": "Microwave", "watts": 900, "hours": 0.5},
    {"name": "Router/Modem", "watts": 10, "hours": 24},
    {"name": "Air Conditioner", "watts": 1000, "hours": 8},
    {"name": "Washing Machine", "watts": 500, "hours": 1}
]

class SolarCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bosch Solar System Calculator")
        self.root.geometry("950x700")
        self.root.configure(bg="#f0f4f8")  # Light background for a modern look

        # Fancy title at the top
        title_frame = tk.Frame(self.root, bg="#003366")
        title_frame.pack(fill="x")
        title_label = tk.Label(
            title_frame,
            text="Bosch Solar System Calculator",
            font=("Segoe UI", 22, "bold"),
            fg="#ffffff",
            bg="#003366",
            pady=18
        )
        title_label.pack()

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.input_tab = ttk.Frame(self.notebook)
        self.results_tab = ttk.Frame(self.notebook)
        self.visualization_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.input_tab, text="System Inputs")
        self.notebook.add(self.results_tab, text="Results")
        self.notebook.add(self.visualization_tab, text="Visualizations")
        
        # Setup input form
        self.setup_input_form()
        
        # Initialize results variables
        self.system_design = None
        
    def setup_input_form(self):
        # Create a main frame for the form
        form_frame = ttk.Frame(self.input_tab, padding="10")
        form_frame.pack(fill='both', expand=True)
        
        # Create two columns
        left_frame = ttk.Frame(form_frame)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=5)
        
        right_frame = ttk.Frame(form_frame)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=5)
        
        # Left column - Load & Location
        ttk.Label(left_frame, text="Energy Requirements", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        # Add Load Calculator button in the left frame after household load input
        load_calc_frame = ttk.Frame(left_frame)
        load_calc_frame.pack(fill="x", pady=2)
        
        ttk.Label(load_calc_frame, text="Household load (Watts):").pack(side=tk.LEFT)
        self.household_load_var = tk.StringVar(value="1000")
        ttk.Entry(load_calc_frame, textvariable=self.household_load_var).pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        ttk.Button(load_calc_frame, text="Calculate Load", command=self.open_load_calculator).pack(side=tk.RIGHT)
        
        ttk.Label(left_frame, text="Location (for solar data)").pack(anchor="w", pady=5)
        
        # Add address search field
        address_frame = ttk.Frame(left_frame)
        address_frame.pack(fill="x", pady=2)
        
        ttk.Label(address_frame, text="Address:").pack(side=tk.LEFT)
        self.address_var = tk.StringVar()
        ttk.Entry(address_frame, textvariable=self.address_var, width=30).pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        ttk.Button(address_frame, text="Search", command=self.geocode_address).pack(side=tk.RIGHT)
        
        # Keep existing lat/long fields
        location_frame = ttk.Frame(left_frame)
        location_frame.pack(fill="x", pady=2)
        
        ttk.Label(location_frame, text="Latitude:").pack(side=tk.LEFT)
        self.latitude_var = tk.StringVar(value="40.0")
        ttk.Entry(location_frame, textvariable=self.latitude_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(location_frame, text="Longitude:").pack(side=tk.LEFT, padx=5)
        self.longitude_var = tk.StringVar(value="-74.0")
        ttk.Entry(location_frame, textvariable=self.longitude_var, width=10).pack(side=tk.LEFT)
        
        ttk.Button(location_frame, text="Estimate Sun Hours", command=self.lookup_sun_hours).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(left_frame, text="Sun hours per day:").pack(anchor="w", pady=5)
        self.sun_hours_var = tk.StringVar(value="4.5")
        ttk.Entry(left_frame, textvariable=self.sun_hours_var).pack(fill="x")
        
        # Add region selection above the panel selection
        ttk.Label(left_frame, text="Region for price estimates:", font=("Arial", 10)).pack(anchor="w", pady=5)
        self.region_var = tk.StringVar(value="Europe")
        region_combobox = ttk.Combobox(left_frame, textvariable=self.region_var, state="readonly")
        region_combobox['values'] = ["Europe", "Germany"]
        region_combobox.current(0)
        region_combobox.pack(fill="x", pady=2)
        region_combobox.bind("<<ComboboxSelected>>", self.update_regional_prices)

        # Add a price lookup button
        price_lookup_button = ttk.Button(left_frame, text="Use Regional Price Estimates", 
                                         command=self.apply_regional_prices)
        price_lookup_button.pack(fill="x", pady=10)

        # Solar Panel Selection
        ttk.Label(left_frame, text="Solar Panel", font=("Arial", 12, "bold")).pack(anchor="w", pady=10)
        
        ttk.Label(left_frame, text="Select panel type:").pack(anchor="w")
        self.panel_type_var = tk.StringVar()
        panel_combobox = ttk.Combobox(left_frame, textvariable=self.panel_type_var)
        panel_combobox['values'] = [panel["name"] for panel in SOLAR_PANELS]
        panel_combobox.current(1) if len(SOLAR_PANELS) > 1 else None
        panel_combobox.pack(fill="x", pady=5)
        panel_combobox.bind("<<ComboboxSelected>>", self.update_panel_cost)
        
        # --- Currency symbol for panel cost ---
        self.pv_cost_label = ttk.Label(left_frame, text=f"Custom panel cost per watt ({self.get_currency_symbol()}):")
        self.pv_cost_label.pack(anchor="w")
        self.pv_cost_var = tk.StringVar(value="0.85")
        ttk.Entry(left_frame, textvariable=self.pv_cost_var).pack(fill="x", pady=5)
        
        # Right column - Battery & System
        ttk.Label(right_frame, text="Battery System", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        ttk.Label(right_frame, text="Select battery type:").pack(anchor="w")
        self.battery_type_var = tk.StringVar()
        battery_combobox = ttk.Combobox(right_frame, textvariable=self.battery_type_var)
        battery_combobox['values'] = [battery["name"] for battery in BATTERIES]
        battery_combobox.current(1) if len(BATTERIES) > 1 else None
        battery_combobox.pack(fill="x", pady=5)
        battery_combobox.bind("<<ComboboxSelected>>", self.update_battery_params)
        
        ttk.Label(right_frame, text="Days of autonomy:").pack(anchor="w")
        self.autonomy_var = tk.StringVar(value="2")
        ttk.Entry(right_frame, textvariable=self.autonomy_var).pack(fill="x", pady=5)
        
        ttk.Label(right_frame, text="Battery depth of discharge (0.1-1.0):").pack(anchor="w")
        self.dod_var = tk.StringVar(value="0.7")
        ttk.Entry(right_frame, textvariable=self.dod_var).pack(fill="x", pady=5)
        
        # --- Currency symbol for battery cost ---
        self.battery_cost_label = ttk.Label(right_frame, text=f"Battery cost per watt-hour ({self.get_currency_symbol()}):")
        self.battery_cost_label.pack(anchor="w")
        self.battery_cost_var = tk.StringVar(value="0.22")
        ttk.Entry(right_frame, textvariable=self.battery_cost_var).pack(fill="x", pady=5)
        
        # Other system components
        ttk.Label(right_frame, text="Other Components", font=("Arial", 12, "bold")).pack(anchor="w", pady=10)
        
        # --- Currency symbol for controller cost ---
        self.controller_cost_label = ttk.Label(right_frame, text=f"Charge controller cost per amp ({self.get_currency_symbol()}):")
        self.controller_cost_label.pack(anchor="w")
        self.controller_cost_var = tk.StringVar(value="8.0")
        ttk.Entry(right_frame, textvariable=self.controller_cost_var).pack(fill="x", pady=5)
        
        # --- Currency symbol for inverter and other costs ---
        self.inverter_cost_label = ttk.Label(right_frame, text=f"Inverter cost ({self.get_currency_symbol()}):")
        self.inverter_cost_label.pack(anchor="w")
        self.inverter_cost_var = tk.StringVar(value="500")
        ttk.Entry(right_frame, textvariable=self.inverter_cost_var).pack(fill="x", pady=5)
        
        self.other_costs_label = ttk.Label(right_frame, text=f"Other costs ({self.get_currency_symbol()}):")
        self.other_costs_label.pack(anchor="w")
        self.other_costs_var = tk.StringVar(value="200")
        ttk.Entry(right_frame, textvariable=self.other_costs_var).pack(fill="x", pady=5)
        
        # --- New: Mounting, Cabling, Installation ---
        ttk.Label(right_frame, text="Mounting structure cost (€):").pack(anchor="w")
        self.mounting_cost_var = tk.StringVar(value="300")
        ttk.Entry(right_frame, textvariable=self.mounting_cost_var).pack(fill="x", pady=5)

        ttk.Label(right_frame, text="Cabling cost (€):").pack(anchor="w")
        self.cabling_cost_var = tk.StringVar(value="150")
        ttk.Entry(right_frame, textvariable=self.cabling_cost_var).pack(fill="x", pady=5)

        ttk.Label(right_frame, text="Installation/Labor cost (€):").pack(anchor="w")
        self.installation_cost_var = tk.StringVar(value="400")
        ttk.Entry(right_frame, textvariable=self.installation_cost_var).pack(fill="x", pady=5)
        
        # Add maintenance cost input
        ttk.Label(right_frame, text="Annual maintenance cost (€):").pack(anchor="w")
        self.maintenance_cost_var = tk.StringVar(value="100")
        ttk.Entry(right_frame, textvariable=self.maintenance_cost_var).pack(fill="x", pady=5)

        # Add subsidy input
        ttk.Label(right_frame, text="Government subsidy (€):").pack(anchor="w")
        self.subsidy_var = tk.StringVar(value="0")
        ttk.Entry(right_frame, textvariable=self.subsidy_var).pack(fill="x", pady=5)
     
        # --- Buttons frame at bottom (centered and styled) ---
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(side=tk.BOTTOM, fill="x", pady=20)

        center_btns = ttk.Frame(button_frame)
        center_btns.pack(anchor="center")

        style = ttk.Style()
        style.configure("Fancy.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.map("Fancy.TButton",
                  foreground=[('active', '#003366')],
                  background=[('active', '#e6eaf0')])

        ttk.Button(center_btns, text="Calculate System", command=self.calculate_system, style="Fancy.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(center_btns, text="Save Design", command=self.save_design, style="Fancy.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(center_btns, text="Load Design", command=self.load_design, style="Fancy.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(center_btns, text="Price Guide", command=self.show_price_guide, style="Fancy.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(center_btns, text="Clear", command=self.clear_inputs, style="Fancy.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(center_btns, text="Exit", command=self.root.quit, style="Fancy.TButton").pack(side=tk.LEFT, padx=10)

    def get_region_from_coordinates(self, lat, lon): #get cordination based on location search
        """Returns 'Germany' if coordinates are in Germany, 'Europe' if in Europe, else None."""
        lat = float(lat)
        lon = float(lon)
        # Rough bounding box for Germany
        if 47.2 <= lat <= 55.1 and 5.9 <= lon <= 15.1:
            return "Germany"
        # Rough bounding box for Europe (excluding Russia, Turkey, etc.)
        if 35.0 <= lat <= 71.0 and -10.0 <= lon <= 40.0:
            return "Europe"
        return None

    def geocode_address(self):
        """Geocodes an address to get latitude and longitude"""
        address = self.address_var.get().strip()
        if not address:
            messagebox.showerror("Input Error", "Please enter an address to search")
            return
            
        try:
            # Show busy cursor during search
            self.root.config(cursor="wait")
            self.root.update()
            
            # Use Nominatim geocoding service (OpenStreetMap)
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            headers = {
                "User-Agent": "SolarCalculatorApp/1.0"  # Required by Nominatim
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200 and response.json():
                location = response.json()[0]
                lat = location.get("lat")
                lon = location.get("lon")
                
                if lat and lon:
                    self.latitude_var.set(lat)
                    self.longitude_var.set(lon)
                    
                    # Auto-update region based on coordinates
                    region = self.get_region_from_coordinates(lat, lon)
                    if region:
                        self.region_var.set(region)
                        self.update_regional_prices()
                    else:
                        messagebox.showwarning("Region", "Location is outside supported regions. Defaulting to Europe prices.")
                        self.region_var.set("Europe")
                        self.update_regional_prices()
                    
                    # Auto-estimate sun hours based on new location
                    self.lookup_sun_hours()
                    
                    display_name = location.get("display_name", "")
                    messagebox.showinfo("Location Found", 
                                       f"Found location: {display_name}\n"
                                       f"Latitude: {lat}, Longitude: {lon}")
                else:
                    messagebox.showerror("Location Error", "Could not find coordinates for this address")
            else:
                messagebox.showerror("Search Error", "No results found for this address")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to geocode address: {str(e)}")
        finally:
            # Reset cursor
            self.root.config(cursor="")
    
    def update_panel_cost(self, event):
        selected_panel = next((panel for panel in SOLAR_PANELS if panel["name"] == self.panel_type_var.get()), None)
        if selected_panel:
            self.pv_cost_var.set(str(selected_panel["cost_per_watt"]))
    
    def update_battery_params(self, event):
        selected_battery = next((battery for battery in BATTERIES if battery["name"] == self.battery_type_var.get()), None)
        if selected_battery:
            self.battery_cost_var.set(str(selected_battery["cost_per_wh"]))
            self.dod_var.set(str(selected_battery["dod"]))
    
    def update_regional_prices(self, event=None):
        """Updates price recommendations when region changes and updates currency symbols"""
        # Update all cost labels to use the correct currency symbol
        currency = self.get_currency_symbol()
        self.pv_cost_label.config(text=f"Custom panel cost per watt ({currency}):")
        self.battery_cost_label.config(text=f"Battery cost per watt-hour ({currency}):")
        self.controller_cost_label.config(text=f"Charge controller cost per amp ({currency}):")
        self.inverter_cost_label.config(text=f"Inverter cost ({currency}):")
        self.other_costs_label.config(text=f"Other costs ({currency}):")
        messagebox.showinfo("Price Information", 
                            f"Selected region: {self.region_var.get()}\n"
                            "Click 'Use Regional Price Estimates' to apply typical prices for this region.")

    def get_currency_symbol(self):
        """Returns the appropriate currency symbol based on selected region"""
        # Only Europe and Germany are available now
        return "€"

    def apply_regional_prices(self):
        """Applies price estimates based on selected region"""
        region = self.region_var.get()
        
        if region in REGIONAL_PRICES:
            regional_data = REGIONAL_PRICES[region]
            
            # Determine price tier for panel type
            panel_type = self.panel_type_var.get()
            price_tier = "average"
            if "Economy" in panel_type:
                price_tier = "low"
            elif "Premium" in panel_type or "HJT" in panel_type or "Bifacial" in panel_type:
                price_tier = "premium"
            
            # Determine battery price key
            battery_type = self.battery_type_var.get()
            battery_price_key = "agm"
            if "Lead-Acid" in battery_type:
                battery_price_key = "lead_acid"
            elif "Lithium" in battery_type:
                battery_price_key = "lithium"
            
            # Apply regional prices
            self.pv_cost_var.set(str(regional_data["solar_panel_per_watt"][price_tier]))
            self.battery_cost_var.set(str(regional_data["battery_per_wh"][battery_price_key]))
            self.controller_cost_var.set(str(regional_data["controller_per_amp"]["mppt"]))
            
            # Estimate inverter cost
            household_load = float(self.household_load_var.get())
            if household_load < 800:
                self.inverter_cost_var.set(str(regional_data["inverter_base"]["1kw"]))
            elif household_load < 2000:
                self.inverter_cost_var.set(str(regional_data["inverter_base"]["2kw"]))
            else:
                self.inverter_cost_var.set(str(regional_data["inverter_base"]["5kw"]))
            
            currency = regional_data.get("currency", "€")
            messagebox.showinfo("Prices Updated", 
                               f"Applied typical prices for {region} based on selected components.\n"
                               f"All prices shown in {currency}")
        else:
            messagebox.showerror("Region Error", "Price data not available for selected region")

    def show_price_guide(self):
        """Shows pricing information and explanations to users"""
        price_guide = tk.Toplevel(self.root)
        price_guide.title("Solar Component Price Guide")
        price_guide.geometry("700x500")
        
        # Create scrollable text area
        frame = ttk.Frame(price_guide)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        text = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set)
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        # Get currency symbol
        currency = self.get_currency_symbol()
        
        # Add pricing information content
        text.insert("end", "Solar Component Price Guide\n\n", "title")
        text.insert("end", f"This guide provides typical price ranges for solar system components in {self.region_var.get()}. " 
                    "Prices vary by region, quality, and market conditions.\n\n")
        
        text.insert("end", "SOLAR PANELS:\n", "heading")
        text.insert("end", f"• Economy panels: {currency}0.65-{currency}0.75 per watt\n")
        text.insert("end", f"• Standard panels: {currency}0.75-{currency}0.95 per watt\n")
        text.insert("end", f"• PERC panels: {currency}0.85-{currency}1.00 per watt\n")
        text.insert("end", f"• Monocrystalline panels: {currency}0.90-{currency}1.05 per watt\n")
        text.insert("end", f"• N-Type panels: {currency}0.95-{currency}1.15 per watt\n")
        text.insert("end", f"• Bifacial panels: {currency}1.00-{currency}1.20 per watt\n")
        text.insert("end", f"• HJT panels: {currency}1.15-{currency}1.30 per watt\n")
        text.insert("end", f"• Premium panels: {currency}1.10-{currency}1.35 per watt\n\n")
        
        text.insert("end", "BATTERIES:\n", "heading")
        text.insert("end", f"• Lead-Acid: {currency}0.15-{currency}0.20 per Wh\n")
        text.insert("end", f"• AGM: {currency}0.22-{currency}0.30 per Wh\n")
        text.insert("end", f"• Lithium-Ion: {currency}0.35-{currency}0.50 per Wh\n\n")
        
        text.insert("end", "CHARGE CONTROLLERS:\n", "heading")
        text.insert("end", f"• PWM: {currency}5.00-{currency}6.00 per amp\n")
        text.insert("end", f"• MPPT: {currency}8.00-{currency}10.00 per amp\n\n")
        
        text.insert("end", "INVERTERS:\n", "heading")
        text.insert("end", f"• 1kW: {currency}300-{currency}400\n")
        text.insert("end", f"• 2kW: {currency}500-{currency}700\n")
        text.insert("end", f"• 5kW: {currency}900-{currency}1200\n\n")
        
        # Add style tags
        text.tag_configure("title", font=("Arial", 14, "bold"))
        text.tag_configure("heading", font=("Arial", 12, "bold"))
        
        # Make text read-only
        text.config(state="disabled")
        
        # Add close button
        ttk.Button(price_guide, text="Close", command=price_guide.destroy).pack(pady=10)
    
    def lookup_sun_hours(self):
        try:
            latitude = float(self.latitude_var.get())
            sun_hours = estimate_sun_hours_by_latitude(latitude)
            self.sun_hours_var.set(str(sun_hours))
            messagebox.showinfo("Solar Data", f"Estimated sun hours per day: {sun_hours}")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid latitude")
    
    def open_load_calculator(self):
        """Opens a dialog to help calculate household load"""
        load_calculator = tk.Toplevel(self.root)
        load_calculator.title("Household Load Calculator")
        load_calculator.geometry("600x500")
        
        # Create frame for the appliance list
        appliance_frame = ttk.Frame(load_calculator, padding="10")
        appliance_frame.pack(fill='both', expand=True)
        
        # Create columns for the appliance list
        ttk.Label(appliance_frame, text="Appliance", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(appliance_frame, text="Watts", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(appliance_frame, text="Hours", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(appliance_frame, text="Daily Wh", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, pady=5)
        
        # List to store appliance entries
        appliance_entries = []
        
        # Total calculation frame setup
        total_frame = ttk.Frame(load_calculator)
        total_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(total_frame, text="Total Daily Consumption:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        total_wh_label = ttk.Label(total_frame, text="0 Wh")
        total_wh_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(total_frame, text="Average Power:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=20)
        average_watts_label = ttk.Label(total_frame, text="0 W")
        average_watts_label.pack(side=tk.LEFT, padx=5)
        
        # Define calculate_total function first before it's referenced
        def calculate_total():
            total = 0
            for _, watts_entry, hours_entry, _ in appliance_entries:
                try:
                    watts = float(watts_entry.get())
                    hours = float(hours_entry.get())
                    total += watts * hours
                except ValueError:
                    pass
            
            total_wh_label.config(text=f"{total:.1f} Wh")
            total_watts = total / 24 if total > 0 else 0
            average_watts_label.config(text=f"{total_watts:.1f} W")
        
        def add_appliance_row(appliance=None):
            row = len(appliance_entries) + 1
            
            # Create variables for this row
            name_var = tk.StringVar(value=appliance["name"] if appliance else "")
            watts_var = tk.StringVar(value=str(appliance["watts"]) if appliance else "")
            hours_var = tk.StringVar(value=str(appliance["hours"]) if appliance else "")
            
            # Create the row widgets
            name_entry = ttk.Entry(appliance_frame, textvariable=name_var)
            name_entry.grid(row=row, column=0, padx=5, pady=2)
            
            watts_entry = ttk.Entry(appliance_frame, textvariable=watts_var, width=8)
            watts_entry.grid(row=row, column=1, padx=5, pady=2)
            
            hours_entry = ttk.Entry(appliance_frame, textvariable=hours_var, width=8)
            hours_entry.grid(row=row, column=2, padx=5, pady=2)
            
            daily_wh_label = ttk.Label(appliance_frame, text="0")
            daily_wh_label.grid(row=row, column=3, padx=5, pady=2)
            
            def update_daily_wh(*args):
                try:
                    watts = float(watts_var.get())
                    hours = float(hours_var.get())
                    daily_wh = watts * hours
                    daily_wh_label.config(text=f"{daily_wh:.1f}")
                    calculate_total()  # Now this reference is valid
                except ValueError:
                    daily_wh_label.config(text="Error")
            
            watts_var.trace_add("write", update_daily_wh)
            hours_var.trace_add("write", update_daily_wh)
            update_daily_wh()
            
            # Store the entries
            appliance_entries.append((name_entry, watts_entry, hours_entry, daily_wh_label))
        
        # Add initial rows from common appliances
        for appliance in COMMON_APPLIANCES[:5]:  # Start with just a few
            add_appliance_row(appliance)
        
        # Add buttons for managing appliances
        button_frame = ttk.Frame(load_calculator)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        def add_new_row():
            add_appliance_row()
        
        def add_from_common():
            # Show dialog with common appliances
            appliance_list = [app["name"] for app in COMMON_APPLIANCES]
            selected = simpledialog.askstring(
                "Add Common Appliance",
                "Select an appliance:",
                parent=load_calculator,
                initialvalue=appliance_list[0]
            )
            if selected:
                appliance = next((a for a in COMMON_APPLIANCES if a["name"] == selected), None)
                if appliance:
                    add_appliance_row(appliance)
        
        ttk.Button(button_frame, text="Add Row", command=add_new_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Common Appliance", command=add_from_common).pack(side=tk.LEFT, padx=5)
        
        # Buttons to apply or cancel
        final_button_frame = ttk.Frame(load_calculator)
        final_button_frame.pack(fill='x', padx=10, pady=10)
        
        def apply_total():
            try:
                total_watts = float(average_watts_label.cget("text").split()[0])
                self.household_load_var.set(str(total_watts))
                load_calculator.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid total watts calculation")
        
        ttk.Button(final_button_frame, text="Apply to Calculator", command=apply_total).pack(side=tk.RIGHT, padx=5)
        ttk.Button(final_button_frame, text="Cancel", command=load_calculator.destroy).pack(side=tk.RIGHT, padx=5)
    
    def clear_inputs(self):
        """Resets all input fields to their default values"""
        self.household_load_var.set("1000")
        self.autonomy_var.set("2")
        self.dod_var.set("0.7")
        self.sun_hours_var.set("4.5")
        self.battery_type_var.set("AGM")
        self.pv_cost_var.set("0.85")
        self.battery_cost_var.set("0.22")
        self.controller_cost_var.set("8.0")
        self.inverter_cost_var.set("500")
        self.other_costs_var.set("200")
        self.mounting_cost_var.set("300")
        self.cabling_cost_var.set("150")
        self.installation_cost_var.set("400")
        self.latitude_var.set("40.0")
        self.longitude_var.set("-74.0")
        self.panel_type_var.set("Standard 300W Panel")
        self.address_var.set("")
        self.region_var.set("Europe")
        self.maintenance_cost_var.set("100")
        self.subsidy_var.set("0")
        self.update_regional_prices()
        # Optionally clear results and visualizations
        for widget in self.results_tab.winfo_children():
            widget.destroy()
        for widget in self.visualization_tab.winfo_children():
            widget.destroy()

    def calculate_system(self):
        try:
            # Get user inputs
            household_load_w = float(self.household_load_var.get())
            days_of_autonomy = float(self.autonomy_var.get())
            battery_dod = float(self.dod_var.get())
            sun_hours_per_day = float(self.sun_hours_var.get())
            
            # Get selected battery type
            selected_battery = next((battery for battery in BATTERIES if battery["name"] == self.battery_type_var.get()), BATTERIES[0])
            battery_voltage_options = [selected_battery["voltage"]]
            battery_cost_per_wh = float(self.battery_cost_var.get())
            
            # Get other costs
            pv_panel_cost_per_watt = float(self.pv_cost_var.get())
            charge_controller_cost_per_amp = float(self.controller_cost_var.get())
            inverter_cost = float(self.inverter_cost_var.get())
            other_costs = float(self.other_costs_var.get())
            
            # --- New: Add extra BOS costs ---
            mounting_cost = float(self.mounting_cost_var.get())
            cabling_cost = float(self.cabling_cost_var.get())
            installation_cost = float(self.installation_cost_var.get())
            other_costs += mounting_cost + cabling_cost + installation_cost
            
            # Get new inputs
            annual_maintenance_cost = float(self.maintenance_cost_var.get())
            subsidy = float(self.subsidy_var.get())
            
            # Validate inputs
            if battery_dod < 0.1 or battery_dod > 1.0:
                messagebox.showerror("Input Error", "Battery depth of discharge must be between 0.1 and 1.0")
                return
            
            if sun_hours_per_day <= 0:
                messagebox.showerror("Input Error", "Sun hours must be greater than 0")
                return
            
            # Calculate system
            self.system_design = calculate_pv_system(
                household_load_w=household_load_w,
                days_of_autonomy=days_of_autonomy,
                battery_dod=battery_dod,
                sun_hours_per_day=sun_hours_per_day,
                battery_voltage_options=battery_voltage_options,
                pv_panel_cost_per_watt=pv_panel_cost_per_watt,
                battery_cost_per_wh=battery_cost_per_wh,
                charge_controller_cost_per_amp=charge_controller_cost_per_amp,
                inverter_cost=inverter_cost,
                other_costs=other_costs,
                battery_cycle_life=selected_battery["cycle_life"],
                annual_maintenance_cost=annual_maintenance_cost,
                subsidy=subsidy
            )
            
            # Display results
            self.display_results()
            self.create_visualizations()
            
            # Switch to results tab
            self.notebook.select(1)
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please check your inputs. {str(e)}")
    
    def display_results(self):
        # Clear previous results
        for widget in self.results_tab.winfo_children():
            widget.destroy()
        
        if not self.system_design:
            ttk.Label(self.results_tab, text="No results to display yet. Calculate a system first.").pack(pady=20)
            return
        
        # Create results display
        results_frame = ttk.Frame(self.results_tab, padding="20")
        results_frame.pack(fill='both', expand=True)
        
        ttk.Label(results_frame, text="System Design Results", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
        
        # Energy requirements
        ttk.Label(results_frame, text="Daily Energy Consumption:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(results_frame, text=f"{self.system_design['daily_energy_wh']:.2f} Wh").grid(row=1, column=1, sticky="w", pady=5)
        
        # Battery system
        ttk.Label(results_frame, text="Battery System", font=("Arial", 12, "bold")).grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        
        ttk.Label(results_frame, text="Required Battery Capacity:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{self.system_design['required_battery_capacity_wh']:.2f} Wh").grid(row=3, column=1, sticky="w", pady=2)
        
        ttk.Label(results_frame, text="Recommended Battery:").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{self.system_design['best_battery_option']['voltage']}V, {self.system_design['best_battery_option']['amp_hours']:.2f} Ah").grid(row=4, column=1, sticky="w", pady=2)
        
        currency = self.get_currency_symbol()
        
        ttk.Label(results_frame, text="Battery Cost:").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{currency}{self.system_design['best_battery_option']['cost']:.2f}").grid(row=5, column=1, sticky="w", pady=2)
        
        # Solar system
        ttk.Label(results_frame, text="Solar System", font=("Arial", 12, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=10)
        
        ttk.Label(results_frame, text="Recommended Solar Panel Size:").grid(row=7, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{self.system_design['solar_panel_size_w']:.2f} W").grid(row=7, column=1, sticky="w", pady=2)
        
        ttk.Label(results_frame, text="Recommended Charge Controller:").grid(row=8, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{self.system_design['charge_controller_amp_rating']:.2f} A").grid(row=8, column=1, sticky="w", pady=2)
        
        # Financial analysis
        ttk.Label(results_frame, text="Financial Analysis", font=("Arial", 12, "bold")).grid(row=9, column=0, columnspan=2, sticky="w", pady=10)
        
        ttk.Label(results_frame, text="Total System Cost:").grid(row=10, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{currency}{self.system_design['total_system_cost']:.2f}").grid(row=10, column=1, sticky="w", pady=2)
        
        ttk.Label(results_frame, text="Estimated Annual Savings:").grid(row=11, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{currency}{self.system_design['annual_savings']:.2f}").grid(row=11, column=1, sticky="w", pady=2)
        
        ttk.Label(results_frame, text="Estimated Payback Period:").grid(row=12, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{self.system_design['payback_years']:.1f} years").grid(row=12, column=1, sticky="w", pady=2)
        
        ttk.Label(results_frame, text="Battery Replacements:").grid(row=13, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"{self.system_design['battery_replacements']}").grid(row=13, column=1, sticky="w", pady=2)

        ttk.Label(results_frame, text="Total Battery Cost:").grid(row=14, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"€{self.system_design['total_battery_cost']:.2f}").grid(row=14, column=1, sticky="w", pady=2)

        ttk.Label(results_frame, text="Annual Maintenance Cost:").grid(row=15, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"€{self.system_design['annual_maintenance_cost']:.2f}").grid(row=15, column=1, sticky="w", pady=2)

        ttk.Label(results_frame, text="Government Subsidy:").grid(row=16, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, text=f"-€{self.system_design['subsidy']:.2f}").grid(row=16, column=1, sticky="w", pady=2)

        # --- Add Download PDF button ---
        button_frame = ttk.Frame(results_frame)
        button_frame.grid(row=100, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Download PDF", command=self.download_pdf).pack()

    def download_pdf(self):
        """Export the results as a PDF file."""
        if not self.system_design:
            messagebox.showwarning("No Data", "No results to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save Results as PDF"
        )
        if not file_path:
            return

        try:
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            x_margin = 2 * cm
            y = height - 2 * cm

            c.setFont("Helvetica-Bold", 16)
            c.drawString(x_margin, y, "Bosch Solar System Calculator - Results")
            y -= 1.2 * cm

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y, "System Design Results")
            y -= 0.8 * cm

            c.setFont("Helvetica", 10)
            def draw_line(label, value):
                nonlocal y
                c.drawString(x_margin, y, f"{label}")
                c.drawString(x_margin + 8*cm, y, f"{value}")
                y -= 0.6 * cm

            # Energy requirements
            draw_line("Daily Energy Consumption:", f"{self.system_design['daily_energy_wh']:.2f} Wh")

            # Battery system
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "Battery System")
            y -= 0.7 * cm
            c.setFont("Helvetica", 10)
            draw_line("Required Battery Capacity:", f"{self.system_design['required_battery_capacity_wh']:.2f} Wh")
            draw_line("Recommended Battery:", f"{self.system_design['best_battery_option']['voltage']}V, {self.system_design['best_battery_option']['amp_hours']:.2f} Ah")
            draw_line("Battery Cost:", f"€{self.system_design['best_battery_option']['cost']:.2f}")

            # Solar system
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "Solar System")
            y -= 0.7 * cm
            c.setFont("Helvetica", 10)
            draw_line("Recommended Solar Panel Size:", f"{self.system_design['solar_panel_size_w']:.2f} W")
            draw_line("Recommended Charge Controller:", f"{self.system_design['charge_controller_amp_rating']:.2f} A")

            # Financial analysis
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "Financial Analysis")
            y -= 0.7 * cm
            c.setFont("Helvetica", 10)
            draw_line("Total System Cost:", f"€{self.system_design['total_system_cost']:.2f}")
            draw_line("Estimated Annual Savings:", f"€{self.system_design['annual_savings']:.2f}")
            draw_line("Estimated Payback Period:", f"{self.system_design['payback_years']:.1f} years")
            draw_line("Battery Replacements:", f"{self.system_design['battery_replacements']}")
            draw_line("Total Battery Cost:", f"€{self.system_design['total_battery_cost']:.2f}")
            draw_line("Annual Maintenance Cost:", f"€{self.system_design['annual_maintenance_cost']:.2f}")
            draw_line("Government Subsidy:", f"-€{self.system_design['subsidy']:.2f}")

            # Add a footer
            y -= 1.2 * cm
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(x_margin, y, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            c.save()
            messagebox.showinfo("PDF Saved", f"Results exported to {file_path}")
        except Exception as e:
            messagebox.showerror("PDF Error", f"Failed to export PDF: {str(e)}")

    def create_visualizations(self):
        # Clear previous visualizations
        for widget in self.visualization_tab.winfo_children():
            widget.destroy()

        if not self.system_design:
            ttk.Label(self.visualization_tab, text="No data to visualize yet. Calculate a system first.").pack(pady=20)
            return

        import numpy as np
        fig = plt.Figure(figsize=(14, 7), dpi=100)

        # --- 1. Cost Breakdown Pie Chart ---
        ax1 = fig.add_subplot(131)
        battery_cost = self.system_design['total_battery_cost']
        solar_panel_cost = self.system_design['solar_panel_size_w'] * float(self.pv_cost_var.get())
        controller_cost = self.system_design['charge_controller_amp_rating'] * float(self.controller_cost_var.get())
        inverter_cost = float(self.inverter_cost_var.get())
        mounting_cost = float(self.mounting_cost_var.get())
        cabling_cost = float(self.cabling_cost_var.get())
        installation_cost = float(self.installation_cost_var.get())
        other_costs = float(self.other_costs_var.get())
        maintenance_cost = self.system_design['annual_maintenance_cost'] * self.system_design.get('payback_years', 25)
        subsidy = float(self.system_design.get('subsidy', 0))
        costs = [
            battery_cost,
            solar_panel_cost,
            controller_cost,
            inverter_cost,
            mounting_cost,
            cabling_cost,
            installation_cost,
            other_costs,
            maintenance_cost,
            -subsidy if subsidy > 0 else 0
        ]
        labels = [
            'Battery', 'Solar Panels', 'Charge Controller', 'Inverter',
            'Mounting', 'Cabling', 'Installation', 'Other',
            'Maintenance', 'Subsidy'
        ]
        pie_colors = [
            '#f4b183',  # Battery
            '#a9d18e',  # Solar Panels
            '#9dc3e6',  # Charge Controller
            '#ffe699',  # Inverter
            '#b7dee8',  # Mounting
            '#c9c9c9',  # Cabling
            '#f8cbad',  # Installation
            '#c6e0b4',  # Other
            '#b4c6e7',  # Maintenance
            '#cccccc',  # Subsidy
        ]
        costs_labels = [(c, l) for c, l in zip(costs, labels) if c > 0]
        pie_colors_used = [pie_colors[labels.index(l)] for _, l in costs_labels]
        ax1.pie([c for c, _ in costs_labels], labels=[l for _, l in costs_labels], autopct='%1.1f%%', startangle=90, colors=pie_colors_used)
        ax1.set_title('System Cost Breakdown (%)')

        # --- 2. Cost per Component Bar Chart ---
        ax2 = fig.add_subplot(132)
        # Exclude subsidy from bar chart
        bar_labels = [l for c, l in zip(costs, labels) if l != 'Subsidy' and c > 0]
        bar_costs = [c for c, l in zip(costs, labels) if l != 'Subsidy' and c > 0]
        bar_colors = [pie_colors[labels.index(l)] for l in bar_labels]
        ax2.bar(bar_labels, bar_costs, color=bar_colors)
        ax2.set_title('Component Costs (€)')
        ax2.set_xlabel('Component')
        ax2.set_ylabel('Cost (€)')
        ax2.tick_params(axis='x', rotation=20)
        ax2.grid(True, linestyle=':', axis='y')

        # --- 3. Cumulative Profit and ROI Over Time Line Chart ---
        ax3 = fig.add_subplot(133)
        lifetime_years = int(self.system_design.get('system_lifetime_years', 25))
        total_system_cost = self.system_design['total_system_cost']
        annual_savings = self.system_design['annual_savings']
        annual_maintenance = self.system_design['annual_maintenance_cost']

        years = np.arange(1, lifetime_years + 1)
        profit = np.array([annual_savings * y - annual_maintenance * y for y in years]) - total_system_cost
        roi = np.where((total_system_cost + annual_maintenance * (years - 1)) > 0,
                       profit / (total_system_cost + annual_maintenance * (years - 1)) * 100, 0)

        # Plot Cumulative Profit
        ax3.plot(years, profit, label='Cumulative Profit (€)', color='seagreen', linewidth=3, marker='o')
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Profit (€)', color='seagreen')
        ax3.tick_params(axis='y', labelcolor='seagreen')
        ax3.set_title('Cumulative Profit & ROI Over Time')
        ax3.grid(True, linestyle=':', which='both', axis='both')
        ax3.set_xticks(np.arange(1, lifetime_years + 1, max(1, lifetime_years // 10)))

        # Plot ROI on secondary y-axis
        ax3b = ax3.twinx()
        ax3b.plot(years, roi, label='ROI (%)', color='royalblue', linewidth=3, marker='s')
        ax3b.set_ylabel('ROI (%)', color='royalblue')
        ax3b.tick_params(axis='y', labelcolor='royalblue')

        # Highlight payback year
        payback_year = np.argmax(profit > 0) + 1 if np.any(profit > 0) else None
        if payback_year:
            ax3.axvline(payback_year, color='red', linestyle='--', alpha=0.7)
            ax3.annotate(f'Payback\nYear {payback_year}', xy=(payback_year, 0), xytext=(payback_year+1, 0),
                         arrowprops=dict(arrowstyle='->', color='red'), color='red', fontsize=10, fontweight='bold')

        # Format y-axis for currency
        from matplotlib.ticker import FuncFormatter
        ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'€{x:,.0f}'))

        # Combine legends
        lines, labels = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3b.get_legend_handles_labels()
        ax3.legend(lines + lines2, labels + labels2, loc='upper left')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.visualization_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def save_design(self):
        if not self.system_design:
            messagebox.showwarning("No Data", "Calculate a system first before saving.")
            return
        
        # Get all the input values
        design_data = {
            "household_load_w": self.household_load_var.get(),
            "days_of_autonomy": self.autonomy_var.get(),
            "battery_dod": self.dod_var.get(),
            "sun_hours_per_day": self.sun_hours_var.get(),
            "battery_type": self.battery_type_var.get(),
            "pv_panel_cost_per_watt": self.pv_cost_var.get(),
            "battery_cost_per_wh": self.battery_cost_var.get(),
            "charge_controller_cost_per_amp": self.controller_cost_var.get(),
            "inverter_cost": self.inverter_cost_var.get(),
            "other_costs": self.other_costs_var.get(),
            "mounting_cost": self.mounting_cost_var.get(),
            "cabling_cost": self.cabling_cost_var.get(),
            "installation_cost": self.installation_cost_var.get(),
            "latitude": self.latitude_var.get(),
            "longitude": self.longitude_var.get(),
            "panel_type": self.panel_type_var.get(),
            "annual_maintenance_cost": self.maintenance_cost_var.get(),
            "subsidy": self.subsidy_var.get(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": self.system_design
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Solar System Design"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(design_data, f, indent=4)
                messagebox.showinfo("Success", f"Design saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def load_design(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Solar System Design"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    design_data = json.load(f)
                
                # Load the values into the form
                self.household_load_var.set(design_data.get("household_load_w", "1000"))
                self.autonomy_var.set(design_data.get("days_of_autonomy", "2"))
                self.dod_var.set(design_data.get("battery_dod", "0.7"))
                self.sun_hours_var.set(design_data.get("sun_hours_per_day", "4.5"))
                self.battery_type_var.set(design_data.get("battery_type", "AGM"))
                self.pv_cost_var.set(design_data.get("pv_panel_cost_per_watt", "0.85"))
                self.battery_cost_var.set(design_data.get("battery_cost_per_wh", "0.22"))
                self.controller_cost_var.set(design_data.get("charge_controller_cost_per_amp", "8.0"))
                self.inverter_cost_var.set(design_data.get("inverter_cost", "500"))
                self.other_costs_var.set(design_data.get("other_costs", "200"))
                self.mounting_cost_var.set(design_data.get("mounting_cost", "300"))
                self.cabling_cost_var.set(design_data.get("cabling_cost", "150"))
                self.installation_cost_var.set(design_data.get("installation_cost", "400"))
                self.latitude_var.set(design_data.get("latitude", "40.0"))
                self.longitude_var.set(design_data.get("longitude", "-74.0"))
                self.panel_type_var.set(design_data.get("panel_type", "Standard 300W Panel"))
                self.maintenance_cost_var.set(design_data.get("annual_maintenance_cost", "100"))
                self.subsidy_var.set(design_data.get("subsidy", "0"))
                
                # Load results if available
                if "results" in design_data:
                    self.system_design = design_data["results"]
                    self.display_results()
                    self.create_visualizations()
                    
                messagebox.showinfo("Success", "Design loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")

# Main function
if __name__ == "__main__":
    root = tk.Tk()
    app = SolarCalculatorApp(root)
    root.mainloop()